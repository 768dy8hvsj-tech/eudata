#!/usr/bin/env python3
"""Load Eurostat purchasing-power series into the tidy store.

WHY THIS FILE EXISTS AS A STUB. The study measures purchasing power only through
PPP-adjusted income (GNI and GDP per capita at PPP). It has no price levels at all, and no
measure of what households actually consume. That is half the question missing: "is
purchasing power greater there" needs both what you earn and what things cost, and the
store answers only the first.

The four series that close the gap were identified exactly -- dataset, dimension order,
codes and all -- and then could not be collected: `ec.europa.eu:443` answers 403 at the
egress proxy for this session, and WebFetch refuses URLs that have not appeared in a user
message. Both are policy denials rather than faults, so nothing was routed around and no
value was invented.

So this script is the loader, written and tested against the store's schema, waiting for
input. It takes either the raw wide-format TSV Eurostat returns, or the pipe-delimited long
format `SERIES|GEO|YEAR|VALUE`, and appends to data/indicators.csv with source and retrieval
date on every row, exactly as the rest of the store does.

USAGE
    python3 load_pps.py <file> [<file> ...]        # .tsv or .txt, series inferred by name
    python3 load_pps.py --dry-run <file>          # parse and report, write nothing

TO COLLECT THE DATA, one of:
  * paste the four URLs in a message to the assistant (clears the WebFetch provenance gate);
  * download the TSVs and drop them in the uploads directory;
  * have ec.europa.eu added to the session's egress allowlist.

    https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/prc_ppp_ind_1/A.VI_PPS_EU27_2020_HAB.A01?format=TSV&startPeriod=2010&endPeriod=2025
    https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/prc_ppp_ind_1/A.VI_PPS_EU27_2020_HAB.GDP?format=TSV&startPeriod=2010&endPeriod=2025
    https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/prc_ppp_ind_1/A.PLI_EU27_2020.A01?format=TSV&startPeriod=2010&endPeriod=2025
    https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/prc_ppp_ind_1/A.PLI_EU27_2020.A0101?format=TSV&startPeriod=2010&endPeriod=2025
    https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/earn_nt_net/A.PPS.NET.P1_NCH_AW100?format=TSV&startPeriod=2010&endPeriod=2025

Codes verified against the Eurostat vocabularies: in `prc_ppp_ind_1` the dimension order is
freq.na_item.ppp_cat.geo, with A01 = actual individual consumption and A0101 = food and
non-alcoholic beverages. In `earn_nt_net` the order is freq.currency.estruct.ecase.geo, and
the case is P1_NCH_AW100 -- single person, no children, 100% of the average wage -- with
estruct NET. (A1_0 does not exist in that vocabulary; omitting estruct returns gross, tax
and social-security rows mixed together.)

VINTAGE, to be recorded on the rows rather than discovered later: 2025 is provisional and
revises in December 2026. 2024 is NOT final either -- it reaches "revised preliminary" in
December 2026 and final only in December 2027. The earliest fully final year is 2023.
`prc_ppp_ind_1` also carries a COICOP 2018 classification break: the new classification was
applied in December 2025 to 2022-2024 only, so a 2010-2025 series straddles a break at
2021/2022, which bites hardest on the food price level. `earn_nt_net` has its own break at
2024, when compilation passed from the OECD to the Joint Research Centre.
"""
import csv, sys, pathlib, datetime, re, collections

BASE = pathlib.Path(__file__).resolve().parent
STORE = BASE / "data" / "indicators.csv"

# series id -> (store code, name, unit, source string)
SERIES = {
    "AIC_PPS_IDX": ("EUROSTAT.AIC_PPS_IDX",
                    "Actual individual consumption per capita, volume index in PPS "
                    "(EU27_2020 = 100)", "index",
                    "Eurostat prc_ppp_ind_1, A.VI_PPS_EU27_2020_HAB.A01"),
    "GDP_PPS_IDX": ("EUROSTAT.GDP_PPS_IDX",
                    "GDP per capita, volume index in PPS (EU27_2020 = 100)", "index",
                    "Eurostat prc_ppp_ind_1, A.VI_PPS_EU27_2020_HAB.GDP"),
    "PLI_AIC":     ("EUROSTAT.PLI_AIC",
                    "Price level index, actual individual consumption (EU27_2020 = 100)",
                    "index", "Eurostat prc_ppp_ind_1, A.PLI_EU27_2020.A01"),
    "PLI_FOOD":    ("EUROSTAT.PLI_FOOD",
                    "Price level index, food and non-alcoholic beverages "
                    "(EU27_2020 = 100)", "index",
                    "Eurostat prc_ppp_ind_1, A.PLI_EU27_2020.A0101"),
    "EARN_PPS":    ("EUROSTAT.EARN_NT_PPS",
                    "Annual net earnings in PPS, single person without children on 100% of "
                    "the average wage", "PPS",
                    "Eurostat earn_nt_net, A.PPS.NET.P1_NCH_AW100"),
}

# Eurostat geo -> this store's ISO3. EL and UK are the two that catch people out.
GEO = {
    "AT": "AUT", "BE": "BEL", "BG": "BGR", "HR": "HRV", "CY": "CYP", "CZ": "CZE",
    "DK": "DNK", "EE": "EST", "FI": "FIN", "FR": "FRA", "DE": "DEU", "EL": "GRC",
    "HU": "HUN", "IE": "IRL", "IT": "ITA", "LV": "LVA", "LT": "LTU", "LU": "LUX",
    "MT": "MLT", "NL": "NLD", "PL": "POL", "PT": "PRT", "RO": "ROU", "SK": "SVK",
    "SI": "SVN", "ES": "ESP", "SE": "SWE", "UK": "GBR", "NO": "NOR", "IS": "ISL",
    "CH": "CHE", "EU27_2020": "EUU", "TR": "TUR", "RS": "SRB", "ME": "MNE",
    "MK": "MKD", "AL": "ALB", "BA": "BIH",
}
NAME = {}
for _f in ("countries.csv", "nonmembers.csv"):
    _p = BASE / "data" / _f
    if _p.exists():
        for _r in csv.DictReader(open(_p, encoding="utf-8")):
            NAME.setdefault(_r["iso3"], _r.get("name") or _r["iso3"])
NAME.setdefault("EUU", "European Union")

FLAG = re.compile(r"[a-z]+$")          # Eurostat appends p / e / b / d to a value


def parse(path):
    """-> [(series_id, geo, year, value, flag)] from either accepted input shape."""
    text = pathlib.Path(path).read_text(encoding="utf-8")
    rows = []
    if "|" in text.splitlines()[0] if text.strip() else False:
        for ln in text.splitlines():
            ln = ln.strip()
            if ln.upper().startswith(("FLAGS", "UNREAD")):
                break                    # everything after is annotation, not data
            if not ln or ln.startswith("#"):
                continue
            parts = [p.strip() for p in ln.split("|")]
            if len(parts) < 4:
                continue
            sid, geo, yr, val = parts[:4]
            if sid not in SERIES or val.startswith(":") or not val:
                continue
            rows.append((sid, geo, yr, val, ""))
        return rows

    # wide TSV: first cell is "freq,na_item,ppp_cat,geo\\TIME_PERIOD", then year columns
    lines = [l for l in text.splitlines() if l.strip()]
    head = lines[0].split("\t")
    years = [h.strip() for h in head[1:]]
    sid = None
    for k, (_c, _n, _u, src) in SERIES.items():
        key = src.split(", ")[-1]
        if key in text or key.replace(".", "\t") in text:
            sid = k
            break
    if sid is None:                     # fall back to the filename
        for k in SERIES:
            if k.lower() in pathlib.Path(path).name.lower():
                sid = k
                break
    if sid is None:
        raise SystemExit(f"{path}: cannot tell which series this is — rename it after one "
                         f"of {', '.join(SERIES)} or use the pipe format")
    for ln in lines[1:]:
        cells = ln.split("\t")
        geo = cells[0].split(",")[-1].strip()
        for yr, raw in zip(years, cells[1:]):
            raw = raw.strip()
            if not raw or raw.startswith(":"):
                continue
            fl = FLAG.search(raw)
            flag = fl.group(0) if fl else ""
            val = FLAG.sub("", raw).strip()
            if not val:
                continue
            rows.append((sid, geo, yr, val, flag))
    return rows


def main(argv):
    dry = "--dry-run" in argv
    files = [a for a in argv if not a.startswith("--")]
    if not files:
        print(__doc__.split("USAGE")[1].split("TO COLLECT")[0].strip())
        return 1

    today = datetime.date.today().isoformat()
    out, skipped, flags = [], collections.Counter(), collections.Counter()
    for f in files:
        for sid, geo, yr, val, flag in parse(f):
            iso = GEO.get(geo)
            if not iso:
                skipped[geo] += 1
                continue
            try:
                v = float(val)
            except ValueError:
                skipped[f"unparseable:{val}"] += 1
                continue
            code, name, unit, src = SERIES[sid]
            if flag:
                flags[f"{sid} {flag}"] += 1
            # every row carries where it came from and when, like the rest of the store
            note = src + ("; flagged " + flag if flag else "")
            if int(yr) >= 2024:
                note += ("; 2025 provisional, 2024 revised-preliminary — both revise "
                         "December 2026")
            out.append([iso, NAME.get(iso, iso), code, name, unit, yr, repr(v), note, today])

    print(f"{len(out)} rows from {len(files)} file(s)")
    for k, v in sorted(collections.Counter(r[2] for r in out).items()):
        yrs = sorted({int(r[5]) for r in out if r[2] == k})
        n = len({r[0] for r in out if r[2] == k})
        print(f"  {k:26} {len(yrs and [x for x in out if x[2]==k]):>4} rows, "
              f"{n:>2} entities, {min(yrs)}-{max(yrs)}")
    if flags:
        print("flagged values:", dict(flags))
    if skipped:
        print("skipped:", dict(skipped))
    if dry:
        print("dry run — nothing written")
        return 0

    existing = set()
    with open(STORE, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            existing.add((r["iso3"], r["indicator_code"], r["year"]))
    fresh = [r for r in out if (r[0], r[2], r[5]) not in existing]
    print(f"{len(out) - len(fresh)} already in the store, appending {len(fresh)}")
    with open(STORE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows(fresh)
    print(f"appended to {STORE}. Now run: gen_narrative.py -> narrate.py -> "
          f"build_dashboard.py <all> and the harnesses")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
