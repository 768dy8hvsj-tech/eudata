#!/usr/bin/env python3
"""Merge data/raw/<ISO3>.csv files (+ the original Poland/EU seed) into
data/indicators.csv, normalising units and adding derived series.

Unit convention in the consolidated file:
  ST.INT.ARVL  raw count of arrivals
  SM.POP.NETM  raw count of people
Charts apply their own display scaling.
"""
import csv, glob, os, collections

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
FIELDS = ["iso3", "country", "indicator_code", "indicator_name", "unit",
          "year", "value", "source", "retrieved"]

rows = []
seen = set()


def add(r):
    key = (r["iso3"], r["indicator_code"], int(r["year"]))
    if key in seen:
        return
    seen.add(key)
    rows.append(r)


# 1. existing consolidated file (Poland + EU aggregate seed)
old = os.path.join(DATA, "indicators.csv")
if os.path.exists(old):
    for r in csv.DictReader(open(old, encoding="utf-8")):
        if r["value"] == "":
            continue
        # the seed stored these pre-scaled; convert to raw counts
        if r["indicator_code"] == "ST.INT.ARVL" and r["unit"] == "millions":
            r["value"] = str(float(r["value"]) * 1e6)
            r["unit"] = "count"
            r["indicator_name"] = "International tourism, number of arrivals"
        elif r["indicator_code"] == "SM.POP.NETM" and r["unit"] == "thousands":
            r["value"] = str(float(r["value"]) * 1e3)
            r["unit"] = "count"
            r["indicator_name"] = "Net migration"
        if r["indicator_code"] == "DERIVED.PPP.PCT.EU":
            continue  # recomputed below
        add(r)

# 2. per-country raw files collected by the subagents
for path in sorted(glob.glob(os.path.join(DATA, "raw", "*.csv"))):
    for r in csv.DictReader(open(path, encoding="utf-8")):
        if not r.get("value") or not r.get("year", "").strip().isdigit():
            continue
        add({k: r.get(k, "") for k in FIELDS})

# 3. derived: GDP per capita PPP as % of the EU average
by = collections.defaultdict(dict)
for r in rows:
    by[(r["iso3"], r["indicator_code"])][int(r["year"])] = float(r["value"])

eu = by.get(("EUU", "NY.GDP.PCAP.PP.CD"), {})
countries = sorted({r["iso3"] for r in rows} - {"EUU"})
derived = 0
for iso in countries:
    pc = by.get((iso, "NY.GDP.PCAP.PP.CD"), {})
    name = next(r["country"] for r in rows if r["iso3"] == iso)
    for y, v in sorted(pc.items()):
        if y in eu and eu[y]:
            rows.append({
                "iso3": iso, "country": name,
                "indicator_code": "DERIVED.PPP.PCT.EU",
                "indicator_name": "GDP per capita PPP as % of EU average",
                "unit": "%", "year": y, "value": round(v / eu[y] * 100, 2),
                "source": "Derived from World Bank NY.GDP.PCAP.PP.CD (country / EUU)",
                "retrieved": "2026-07-27",
            })
            derived += 1

rows.sort(key=lambda r: (r["iso3"], r["indicator_code"], int(r["year"])))
with open(os.path.join(DATA, "indicators.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

# swap in the verified milestone table
newm = os.path.join(DATA, "milestones_new.csv")
if os.path.exists(newm):
    os.replace(newm, os.path.join(DATA, "milestones.csv"))

iso_counts = collections.Counter(r["iso3"] for r in rows)
print(f"indicators.csv: {len(rows)} rows, {len(iso_counts)} entities, {derived} derived")
for iso, n in sorted(iso_counts.items()):
    print(f"  {iso} {n}")
