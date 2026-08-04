#!/usr/bin/env python3
"""Build a country dashboard from the CSV data store.

Usage:  python3 build_dashboard.py POL [more ISO3 codes...]

Reads:
    data/indicators.csv          tidy long format, one row per (country, indicator, year)
    data/milestones.csv          accession/legal/political events per country
    data/narrative/<ISO3>.json   qualitative content + page layout
    template.html                presentation layer (no data in it)

Writes:
    <country-slug>-dashboard.html   self-contained, no external requests
"""
import csv, json, sys, datetime, pathlib, re

BASE = pathlib.Path(__file__).resolve().parent
DATA = BASE / "data"


def load_indicators():
    """-> {(iso3, code): {year: value}}, total row count"""
    table, n = {}, 0
    with open(DATA / "indicators.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            raw = r["value"].strip()
            val = None if raw == "" else float(raw)
            table.setdefault((r["iso3"], r["indicator_code"]), {})[int(r["year"])] = val
            n += 1
    return table, n


def load_milestones(iso3):
    out = []
    with open(DATA / "milestones.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["iso3"] == iso3:
                out.append({"date": r["date"], "sort": float(r["sort_year"]), "label": r["label"],
                            "description": r["description"], "kind": r["kind"]})
    out.sort(key=lambda m: m["sort"])
    return out


def collect_series_keys(nar):
    """Walk the narrative layout and return every {iso3, code} series referenced."""
    keys = []

    def walk(node):
        if isinstance(node, dict):
            if "series" in node and isinstance(node["series"], list):
                for s in node["series"]:
                    keys.append((s.get("iso3"), s["code"]))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(nar)
    return keys


def build(iso3):
    table, rowcount = load_indicators()
    nar = json.loads((DATA / "narrative" / f"{iso3}.json").read_text(encoding="utf-8"))
    w = nar["window"]
    years = list(range(int(w["start"]), int(w["end"]) + 1))

    # series payload: only what the layout actually references
    series = {}
    for req_iso, code in collect_series_keys(nar):
        iso = req_iso or iso3
        key = f"{iso}|{code}"
        if key in series:
            continue
        by_year = table.get((iso, code))
        if by_year is None:
            raise SystemExit(f"missing series in indicators.csv: {iso} / {code}")
        series[key] = [by_year.get(y) for y in years]

    # KPI tiles: resolve any value pulled straight from the data
    kpis = []
    for k in nar["kpis"]:
        k = dict(k)
        vf = k.pop("valueFrom", None)
        if vf:
            vals = table[(vf.get("iso3", iso3), vf["code"])]
            yr = max(y for y in years if vals.get(y) is not None) if vf["year"] == "last" else int(vf["year"])
            v = vals[yr]
            k["value"] = f"{v:,.{vf.get('dp', 1)}f}{vf.get('suffix', '')}"
        kpis.append(k)

    payload = {
        "iso3": iso3, "name": nar["name"], "subtitle": nar["subtitle"],
        "window": w, "years": years, "series": series, "kpis": kpis,
        "heroChart": nar["heroChart"], "tabs": nar["tabs"],
        "sources": nar["sources"], "method": nar["method"],
        "milestones": load_milestones(iso3),
        # same derived episodes the comparison page uses, so a country's line can be
        # read against the shocks every country faced
        "crises": [
            {"from": 2008, "to": 2009, "scope": "global"},
            {"from": 2011, "to": 2013, "scope": "european"},
            {"from": 2020, "to": 2020, "scope": "global"},
        ],
        "generated": datetime.date.today().isoformat(),
        "rowCount": rowcount,
    }

    html = (BASE / "template.html").read_text(encoding="utf-8")
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("__TITLE__", f"{nar['name']} — EU membership impact")
    html = html.replace("__PAYLOAD__", blob)

    slug = re.sub(r"[^a-z0-9]+", "-", nar["name"].lower()).strip("-")
    out = BASE / f"{slug}-dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"built {out.name}  ({len(series)} series, {len(years)} years, {len(payload['milestones'])} milestones)")
    return out


if __name__ == "__main__":
    for code in (sys.argv[1:] or ["POL"]):
        build(code.upper())
