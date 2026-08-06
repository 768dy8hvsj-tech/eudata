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
        if r["indicator_code"].startswith("DERIVED."):
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

countries = sorted({r["iso3"] for r in rows} - {"EUU"})
derived = 0
for src_code, out_code, out_name in [
    ("NY.GDP.PCAP.PP.CD", "DERIVED.PPP.PCT.EU", "GDP per capita PPP as % of EU average"),
    ("NY.GDP.PCAP.KD", "DERIVED.KD.PCT.EU", "GDP per capita (constant 2015 US$) as % of EU average"),
    ("NY.GNP.PCAP.PP.CD", "DERIVED.GNI.PCT.EU", "GNI per capita PPP as % of EU average"),
]:
    eu = by.get(("EUU", src_code), {})
    for iso in countries:
        pc = by.get((iso, src_code), {})
        if not pc:
            continue
        name = next(r["country"] for r in rows if r["iso3"] == iso)
        for y, v in sorted(pc.items()):
            if y in eu and eu[y]:
                rows.append({
                    "iso3": iso, "country": name,
                    "indicator_code": out_code, "indicator_name": out_name,
                    "unit": "%", "year": y, "value": round(v / eu[y] * 100, 2),
                    "source": "Derived from World Bank " + src_code + " (country / EUU)",
                    "retrieved": "2026-08-01",
                })
                derived += 1

# 4. derived: trade openness = exports + imports, both already % of GDP.
#    This is the standard openness measure. It exceeds 100% wherever goods cross
#    a border more than once (re-exports, cross-border supply chains), which is
#    why small single-market economies sit so far above the rest.
for iso in countries + ["EUU"]:
    ex = by.get((iso, "NE.EXP.GNFS.ZS"), {})
    im = by.get((iso, "NE.IMP.GNFS.ZS"), {})
    if not ex or not im:
        continue
    name = next(r["country"] for r in rows if r["iso3"] == iso)
    for y in sorted(set(ex) & set(im)):
        rows.append({
            "iso3": iso, "country": name,
            "indicator_code": "DERIVED.TRADE.OPEN",
            "indicator_name": "Trade openness (exports + imports, % of GDP)",
            "unit": "%", "year": y, "value": round(ex[y] + im[y], 3),
            "source": "Derived from World Bank NE.EXP.GNFS.ZS + NE.IMP.GNFS.ZS",
            "retrieved": "2026-08-02",
        })
        derived += 1

# 5. derived: net migration per 1,000 population.
#    Raw net migration is a headcount, so on any chart it simply ranks countries
#    by size — Germany dwarfs Estonia for reasons that have nothing to do with
#    migration behaviour. Scaling by population makes the series comparable.
for iso in countries + ["EUU"]:
    nm = by.get((iso, "SM.POP.NETM"), {})
    pop = by.get((iso, "SP.POP.TOTL"), {})
    if not nm or not pop:
        continue
    name = next(r["country"] for r in rows if r["iso3"] == iso)
    for y in sorted(set(nm) & set(pop)):
        if not pop[y]:
            continue
        rows.append({
            "iso3": iso, "country": name,
            "indicator_code": "DERIVED.NETM.P1000",
            "indicator_name": "Net migration per 1,000 population",
            "unit": "per 1,000", "year": y,
            "value": round(nm[y] / pop[y] * 1000, 3),
            "source": "Derived from World Bank SM.POP.NETM / SP.POP.TOTL",
            "retrieved": "2026-08-02",
        })
        derived += 1

# 6. derived: EU budget net position, on TWO conventions, because there is no single
#    correct one and the gap between them is large enough to change who counts as a net
#    contributor.
#
#    Commission convention  = allocated expenditure - national contributions.
#      National contributions exclude customs duties, which the Commission treats as the
#      Union's own revenue rather than a national payment.
#
#    Broad convention       = (expenditure - administration) - (contributions + customs).
#      Strips administrative spending, which is allocated to whoever hosts the institutions
#      and makes Belgium and Luxembourg look like large net recipients (administration is
#      54% of Belgium's allocated expenditure and 76% of Luxembourg's in 2023), and counts
#      customs duties as money the member state raised.
#
#    Validation: Poland 2004-2023 gives 178.2bn on the Commission convention and 164.7bn on
#    the broad one. SGH Warsaw School of Economics publishes 161.8bn, within 1.8% of the
#    broad figure — the residual is data vintage, this workbook being the Sept 2025 release.
for iso in countries:
    ex = by.get((iso, "BUDGET.EXPEND"), {})
    co = by.get((iso, "BUDGET.CONTRIB"), {})
    ad = by.get((iso, "BUDGET.ADMIN"), {})
    cu = by.get((iso, "BUDGET.CUSTOMS"), {})
    gni = by.get((iso, "BUDGET.GNI"), {})
    if not ex or not co:
        continue
    name = next(r["country"] for r in rows if r["iso3"] == iso)
    for y in sorted(set(ex) & set(co)):
        variants = [
            ("DERIVED.BUDGET.NET", "EU budget net position (Commission convention)",
             ex[y] - co[y]),
            ("DERIVED.BUDGET.NET.BROAD",
             "EU budget net position (excluding administration, including customs)",
             (ex[y] - ad.get(y, 0.0)) - (co[y] + cu.get(y, 0.0))),
        ]
        for code, nm, v in variants:
            rows.append({
                "iso3": iso, "country": name, "indicator_code": code, "indicator_name": nm,
                "unit": "EUR million", "year": y, "value": round(v, 3),
                "source": "Derived from European Commission EU spending and revenue workbook",
                "retrieved": "2026-08-04"})
            derived += 1
            if gni.get(y):
                rows.append({
                    "iso3": iso, "country": name,
                    "indicator_code": code + ".PCT.GNI",
                    "indicator_name": nm + ", % of GNI",
                    "unit": "%", "year": y, "value": round(v / gni[y] * 100, 4),
                    "source": "Derived from European Commission EU spending and revenue "
                              "workbook (Commission's own GNI denominator)",
                    "retrieved": "2026-08-04"})
                derived += 1

# 7. trade direction. Every other trade series in this project measures HOW MUCH a country
#    trades; this one measures WHO WITH. It is the difference between an economy opening and
#    an economy reorienting, and for the 2004 wave the answer turns out to be the first only.
tp = os.path.join(DATA, "raw", "_trade_partners.csv")
if os.path.exists(tp):
    CODE = {("export share", "European Union"): ("TRADE.EU.EXP.SHR",
             "Exports to the EU, % of total exports"),
            ("import share", "European Union"): ("TRADE.EU.IMP.SHR",
             "Imports from the EU, % of total imports")}
    REG = {"Asia": "ASIA", "America": "AMER", "Africa": "AFR",
           "Rest of Europe (non-EU27)": "EUR", "Oceania & polar regions": "OCE",
           "North America (USMCA)": "USMCA", "Latin America": "LATAM"}
    for r in csv.DictReader(open(tp, encoding="utf-8")):
        key = (r["measure"], r["partner"])
        if key in CODE:
            code, nm = CODE[key]
        elif r["partner"] in REG and r["measure"] == "export share":
            code = "TRADE.REG.EXP." + REG[r["partner"]]
            nm = f"Exports to {r['partner']}, % of extra-EU exports"
        else:
            continue
        name = next((x["country"] for x in rows if x["iso3"] == r["iso3"]), r["iso3"])
        add({"iso3": r["iso3"], "country": name, "indicator_code": code,
             "indicator_name": nm, "unit": r["unit"], "year": r["year"],
             "value": r["value"], "source": r["source"], "retrieved": r["retrieved"]})
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
