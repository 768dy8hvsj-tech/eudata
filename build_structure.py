#!/usr/bin/env python3
"""What each economy is made of: sector shares of gross value added, 1992 onward.

SOURCE. Eurostat national accounts, dataset nama_10_a64, na_item B1G (gross value added),
unit CP_MNAC (current prices, national currency). One file, data/raw/
eurostat_nama_10_a64_B1G_1992-2025.txt, carrying its own retrieval stamp and a checksum
that is re-verified here before anything is read.

WHY VALUE ADDED AND NOT GDP. Industry breakdowns exist only for value added. GDP is value
added plus taxes on products minus subsidies; the tax wedge cannot be allocated to
industries, so "fishing is x% of GDP" is always, in the official statistics, "x% of gross
value added". The shares here sum to 100 by construction of the accounts, and the build
proves it (below).

WHY CURRENT PRICES. A share is a ratio of two values in the same year and currency, so
currency and price level cancel. Chain-linked volumes are not additive and must never be
used for shares.

NOTHING IS ESTIMATED. Where Eurostat does not publish a split (Switzerland's agriculture /
forestry / fishing; Malta's mining and energy; the latest year's agricultural detail for
many countries) the split is shown as missing, and the composition chart stops at the last
year in which every family is published. No gap is filled, interpolated or pro-rated.

TOURISM. Tourism is not an industry in national accounts. "Accommodation & food services"
(NACE I) is the one consistently measured proxy; it understates tourism because it omits
tourist spending on transport (air travel especially), retail and recreation.

CHECKS (the build aborts if any fails):
  1. file checksum matches the one written at retrieval;
  2. sections A..U sum to the published TOTAL within 0.5% in every published year;
  3. A01+A02+A03 = A within 0.5% (or 0.2m NAC for tiny values) where published;
  4. C10-C12 <= C;
  5. the eight families of every plotted year sum to 100.0 +/- 0.05.
"""
import json, os, sys, collections, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw", "eurostat_nama_10_a64_B1G_1992-2025.txt")

GEO = {"BE":"BEL","BG":"BGR","CZ":"CZE","DK":"DNK","DE":"DEU","EE":"EST","IE":"IRL","EL":"GRC",
 "ES":"ESP","FR":"FRA","HR":"HRV","IT":"ITA","CY":"CYP","LV":"LVA","LT":"LTU","LU":"LUX","HU":"HUN",
 "MT":"MLT","NL":"NLD","AT":"AUT","PL":"POL","PT":"PRT","RO":"ROU","SI":"SVN","SK":"SVK","FI":"FIN",
 "SE":"SWE","UK":"GBR","NO":"NOR","IS":"ISL","CH":"CHE","EU27_2020":"EUU"}
NAMES = {"EUU":"EU-27 (2020 composition)","NOR":"Norway","ISL":"Iceland","CHE":"Switzerland"}
SLUG = {"GBR":"united-kingdom"}
SECTIONS = ["A","B","C","D","E","F","G","H","I","J","K","L","M_N","O-Q","R-U"]

# The 18 detailed sectors: key, label, how to compute (list of + codes, list of - codes)
DETAIL = [
 ("agri","Agriculture (crops & livestock)",["A01"],[]),
 ("forest","Forestry & logging",["A02"],[]),
 ("fish","Fishing & aquaculture",["A03"],[]),
 ("mining","Mining & quarrying (incl. oil & gas)",["B"],[]),
 ("foodmfg","Food, drink & tobacco manufacturing",["C10-C12"],[]),
 ("othermfg","Other manufacturing",["C"],["C10-C12"]),
 ("energy","Electricity, gas & heat",["D"],[]),
 ("water","Water, sewerage & waste",["E"],[]),
 ("constr","Construction",["F"],[]),
 ("trade","Wholesale & retail trade",["G"],[]),
 ("transport","Transport & storage",["H"],[]),
 ("hotels","Accommodation & food services (tourism proxy)",["I"],[]),
 ("ict","Information & communication",["J"],[]),
 ("finance","Finance & insurance",["K"],[]),
 ("realestate","Real estate",["L"],[]),
 ("business","Professional, scientific & support services",["M_N"],[]),
 ("public","Public administration, education & health",["O-Q"],[]),
 ("other","Arts, recreation & other services",["R-U"],[]),
]
# Eight families for the stacked chart, bottom to top, in palette-slot order.
FAMILY = [
 ("agri_forest","Agriculture & forestry",[["A01","A02"]],[]),
 ("fishing","Fishing & aquaculture",[["A03"]],[]),
 ("mining_energy","Mining, energy & utilities",[["B","D","E"],["B-E"]],[["C"]]),
 ("manufacturing","Manufacturing",[["C"]],[]),
 ("construction","Construction",[["F"]],[]),
 ("trade_transport","Trade, transport & hospitality",[["G","H","I"]],[]),
 ("business_finance","Business, finance & property",[["J","K","L","M_N"]],[]),
 ("public_other","Public & other services",[["O-Q","R-U"]],[]),
]
FOOD = ["agri","fish","forest","foodmfg"]

def ck(s):
    a = 0
    for ch in s: a = (a*31 + ord(ch)) % 1000000007
    return a

def load():
    t = open(RAW, encoding="utf-8").read()
    lines = t.split("\n")
    meta0, meta1 = lines[0], lines[1]
    body = "\n".join(lines[2:]).rstrip("\n")
    want = dict(p.split("=") for p in meta1[2:].split())
    assert len(body) == int(want["body_len"]) and ck(body) == int(want["body_ck"]), "raw file checksum FAILED"
    data = collections.defaultdict(dict); flags = collections.defaultdict(dict)
    for l in body.split("\n")[1:]:
        g, c, y0, vals, fl = (l.split("|") + [""])[:5]
        if y0 == "-": continue
        for i, v in enumerate(vals.split(";")):
            if v != "": data[g].setdefault(c, {})[int(y0)+i] = float(v)
        for f in [x for x in fl.split(",") if x]:
            flags[g].setdefault(c, {})[int(f[:4])] = f[4:]
    return data, flags, meta0

def val(d, codes, y):
    s = 0.0
    for c in codes:
        v = d.get(c, {}).get(y)
        if v is None: return None
        s += v
    return s

def fam_value(d, spec, y):
    plus_alts, minus = spec[2], spec[3]
    for alt in plus_alts:
        p = val(d, alt, y)
        if p is None: continue
        if alt == ["B-E"]:
            m = val(d, minus[0], y) if minus else 0.0
            if m is None: continue
            return p - m, "combined"
        return p, None
    return None, None

def main():
    data, flags, meta = load()
    names = {}
    for r in open(os.path.join(BASE, "data", "countries.csv"), encoding="utf-8").read().splitlines()[1:]:
        iso, nm = r.split(",")[:2]; names[iso] = nm
    names.update(NAMES)
    fails, out = [], []
    csv_rows = []
    for g, iso in GEO.items():
        d = data[g]; tot = d["TOTAL"]; yrs = sorted(tot)
        # check 2: sections sum
        for y in yrs:
            parts = [d.get(s, {}).get(y) for s in SECTIONS]
            if None in parts:
                # Malta publishes B and D combined only inside B-E: test with B-E instead
                be = d.get("B-E", {}).get(y)
                alt = [d.get(s, {}).get(y) for s in ["A","B-E","F","G","H","I","J","K","L","M_N","O-Q","R-U"]]
                if None in alt: continue
                parts = alt
            s = sum(parts)
            if abs(s - tot[y]) > 0.005*abs(tot[y]): fails.append(f"{g} {y}: sections {s:.1f} vs total {tot[y]:.1f}")
        # check 3/4
        for y in yrs:
            a = d.get("A", {}).get(y); sp = val(d, ["A01","A02","A03"], y)
            if a is not None and sp is not None and abs(sp - a) > max(0.005*abs(a), 0.2):
                fails.append(f"{g} {y}: A01+A02+A03 {sp} vs A {a}")
            c = d.get("C", {}).get(y); f = d.get("C10-C12", {}).get(y)
            if c is not None and f is not None and f > c + 0.1: fails.append(f"{g} {y}: C10-C12 > C")
        det, fam, notes = {}, {}, set()
        for key, lab, plus, minus in DETAIL:
            s = []
            for y in yrs:
                p = val(d, plus, y); m = val(d, minus, y) if minus else 0.0
                s.append(None if p is None or m is None else round(100*(p-m)/tot[y], 3))
            det[key] = s
        acomb = [None if d.get("A",{}).get(y) is None else round(100*d["A"][y]/tot[y],3) for y in yrs]
        for key, lab, *_ in FAMILY:
            s = []
            for y in yrs:
                v, how = fam_value(d, (key, lab) + tuple(_), y)
                if how == "combined": notes.add("mining_energy_combined")
                s.append(None if v is None else round(100*v/tot[y], 3))
            fam[key] = s
        # A country that never publishes the A01/A02/A03 split (Switzerland) gets one combined
        # primary-sector family instead; fishing is then inside it, not zero. A country that
        # publishes the split but not yet for its latest year is NOT given a combined year --
        # the chart would silently change definition at its right edge -- it just stops earlier.
        if all(v is None for v in fam["agri_forest"]) and any(v is not None for v in acomb):
            fam["agri_forest"] = list(acomb); fam["fishing"] = [0.0 if v is not None else None for v in acomb]
            notes.add("primary_combined")
        complete = [i for i, y in enumerate(yrs) if all(fam[k][i] is not None for k, *_ in FAMILY)]
        for i in complete:
            ssum = sum(fam[k][i] for k, *_ in FAMILY)
            if abs(ssum - 100) > 0.05: fails.append(f"{g} {yrs[i]}: families sum {ssum:.3f}")
        # families are shares of TOTAL; tiny residuals are rounding in the published parts
        resid = [round(100 - sum(fam[k][i] for k, *_ in FAMILY), 3) for i in complete]
        fl = flags.get(g, {}).get("TOTAL", {})
        rec = {"iso3": iso, "geo": g, "name": names.get(iso, g), "years": yrs,
               "family": fam, "detail": det, "agriCombined": acomb,
               "complete": [yrs[i] for i in complete],
               "flags": {str(y): f for y, f in sorted(fl.items())},
               "notes": sorted(notes), "maxResidual": max([abs(r) for r in resid] or [0]),
               "page": (SLUG.get(iso) or names.get(iso, "").lower().replace(" ", "-")) + "-dashboard.html" if iso != "EUU" else "eu.html"}
        out.append(rec)
        for i, y in enumerate(yrs):
            for key, lab, *_ in DETAIL:
                if det[key][i] is not None: csv_rows.append((iso, key, lab, y, det[key][i]))
    if fails:
        print("CHECKS FAILED:"); print("\n".join(fails[:40])); sys.exit(1)
    worst = max(out, key=lambda r: r["maxResidual"])
    print(f"all checks passed; worst family residual {worst['maxResidual']:.3f}pp ({worst['geo']})")
    payload = {"countries": out, "detailKeys": [[k, l] for k, l, *_ in DETAIL],
               "familyKeys": [[k, l] for k, l, *_ in FAMILY], "food": FOOD,
               "source": meta.lstrip("# "), "built": datetime.date.today().isoformat()}
    with open(os.path.join(BASE, "data", "structure.csv"), "w", encoding="utf-8") as f:
        f.write("iso3,sector_key,sector,year,share_of_gva_pct,source\n")
        for r in csv_rows:
            f.write(f'{r[0]},{r[1]},"{r[2]}",{r[3]},{r[4]},Eurostat nama_10_a64 B1G CP_MNAC\n')
    tpl = os.path.join(BASE, "structure_template.html")
    if os.path.exists(tpl):
        html = open(tpl, encoding="utf-8").read().replace("__PAYLOAD__", json.dumps(payload, separators=(",", ":")).replace("</", "<\\/"))
        open(os.path.join(BASE, "structure.html"), "w", encoding="utf-8").write(html)
        print("structure.html written")
    json.dump(payload, open(os.path.join(BASE, "structure_payload.json"), "w"), separators=(",", ":"))

if __name__ == "__main__":
    main()
