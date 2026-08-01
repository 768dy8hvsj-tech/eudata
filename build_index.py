#!/usr/bin/env python3
"""Build index.html — the cross-country comparison page.

Reads data/indicators.csv + data/countries.csv and emits a self-contained page
comparing every country that has data, on GDP per capita (PPP), GNI per capita
(PPP), unemployment and convergence with the EU average.

Form choices follow the project's dataviz rules: a ranked bar chart uses ONE
hue (magnitude, not identity), and the time-series comparison is small
multiples rather than 17 lines in 17 colours.
"""
import csv, json, os, datetime, collections, re

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

METRICS = [
    {"id": "gdppc", "code": "NY.GDP.PCAP.PP.CD", "label": "GDP per capita (PPP)",
     "unit": "$", "dp": 0, "prefix": "$",
     "blurb": "Gross domestic product per head at purchasing power parity, current international $. "
              "The headline measure of material living standards, adjusted so that a dollar buys a "
              "comparable basket in every country."},
    {"id": "gnipc", "code": "NY.GNP.PCAP.PP.CD", "label": "GNI per capita (PPP)",
     "unit": "$", "dp": 0, "prefix": "$",
     "blurb": "Gross national income per head at PPP. GNI counts income accruing to a country's "
              "residents rather than output produced inside its borders — the gap between GNI and "
              "GDP is large in economies hosting substantial foreign-owned production, Ireland and "
              "Luxembourg above all."},
    {"id": "unemp", "code": "SL.UEM.TOTL.ZS", "label": "Unemployment rate",
     "unit": "%", "dp": 1, "suffix": "%", "lowerIsBetter": True,
     "blurb": "Unemployment as a share of the labour force, ILO-modelled estimate. Lower is better, "
              "so this ranking is sorted ascending."},
    {"id": "conv", "code": "DERIVED.PPP.PCT.EU", "label": "Convergence with the EU average",
     "unit": "%", "dp": 1, "suffix": "%",
     "blurb": "GDP per capita (PPP) as a percentage of the EU-wide average. 100% means exactly at "
              "the EU average. This is the single clearest measure of whether a member state is "
              "catching up with, holding level against, or falling behind the Union as a whole."},
]


def load():
    series = collections.defaultdict(dict)
    names = {}
    for r in csv.DictReader(open(os.path.join(DATA, "indicators.csv"), encoding="utf-8")):
        if not r["value"]:
            continue
        series[(r["iso3"], r["indicator_code"])][int(r["year"])] = float(r["value"])
        names[r["iso3"]] = r["country"]
    return series, names


def main():
    series, names = load()
    meta = {r["iso3"]: r for r in csv.DictReader(open(os.path.join(DATA, "countries.csv"), encoding="utf-8"))}
    have = sorted({iso for (iso, _) in series} - {"EUU"})

    years = list(range(1996, 2026))
    payload = {"generated": datetime.date.today().isoformat(), "years": years,
               "metrics": [], "countries": [], "missing": []}

    for iso in have:
        m = meta.get(iso, {})
        payload["countries"].append({
            "iso3": iso, "name": names.get(iso, iso),
            "accession": m.get("accession_date", ""),
            "euro": m.get("euro_adopted", ""),
            "oecd": m.get("oecd_member", ""),
            "slug": re.sub(r"[^a-z0-9]+", "-", names.get(iso, iso).lower()).strip("-") + "-dashboard.html",
        })

    for iso, m in sorted(meta.items()):
        if iso not in have and iso != "GBR":
            payload["missing"].append({"iso3": iso, "name": m["name"]})
        elif iso == "GBR" and iso not in have:
            payload["missing"].append({"iso3": iso, "name": m["name"]})

    for spec in METRICS:
        rows, lines = [], {}
        for iso in have:
            d = series.get((iso, spec["code"]))
            if not d:
                continue
            latest_year = max(d)
            rows.append({"iso3": iso, "name": names[iso], "value": d[latest_year], "year": latest_year})
            lines[iso] = [d.get(y) for y in years]
        rows.sort(key=lambda r: r["value"], reverse=not spec.get("lowerIsBetter"))
        eu = series.get(("EUU", spec["code"]))
        payload["metrics"].append({
            "id": spec["id"], "label": spec["label"], "blurb": spec["blurb"],
            "unit": spec["unit"], "dp": spec["dp"],
            "prefix": spec.get("prefix", ""), "suffix": spec.get("suffix", ""),
            "lowerIsBetter": bool(spec.get("lowerIsBetter")),
            "ranked": rows, "lines": lines,
            "euLine": [eu.get(y) for y in years] if eu else None,
        })

    html = open(os.path.join(BASE, "index_template.html"), encoding="utf-8").read()
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    open(os.path.join(BASE, "index.html"), "w", encoding="utf-8").write(html.replace("__PAYLOAD__", blob))
    print(f"built index.html ({len(have)} countries, {len(payload['metrics'])} metrics, "
          f"{len(payload['missing'])} still missing)")


if __name__ == "__main__":
    main()
