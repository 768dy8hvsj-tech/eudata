#!/usr/bin/env python3
"""Verify every rank chip against the data store, independently of the code that made it.

WHY THIS IS WORTH CHECKING. A rank is a single small number that looks authoritative and
carries no error bars, so a wrong one is unusually hard for a reader to catch. The two ways
it goes wrong are both silent: ranking across a year some countries have not reported yet,
and ranking a country against an aggregate (the EU average, the world) that happens to sit
in the same table.

So this recomputes every chip from data/indicators.csv, using its own reading of the rule
rather than importing build_dashboard, and checks four things: the rank is right, the year
is a year that country actually has, ranks agree across all 31 pages, and no aggregate has
leaked into the comparison pool.
"""
import csv, json, re, sys, pathlib, collections

BASE = pathlib.Path(__file__).resolve().parent
POOL = sorted(p.stem for p in (BASE / "data" / "narrative").glob("*.json"))
# entities in the store that are NOT countries with pages -- these must never be ranked
AGG = {"EUU", "WLD", "USA", "CHN", "RUS", "TUR", "UKR", "BLR", "MDA",
       "SRB", "ALB", "MKD", "BIH", "MNE"}

table = collections.defaultdict(dict)
for r in csv.DictReader(open(BASE / "data" / "indicators.csv", encoding="utf-8")):
    if r["value"].strip():
        table[(r["iso3"], r["indicator_code"])][int(r["year"])] = float(r["value"])

def payload(fn):
    m = re.search(r'<script id="payload" type="application/json">(.*?)</script>',
                  (BASE / fn).read_text(encoding="utf-8"), re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))

pages = {}
for r in csv.DictReader(open(BASE / "data" / "countries.csv", encoding="utf-8")):
    pages[re.sub(r"[^a-z0-9]+", "-", r["name"].lower()).strip("-") + "-dashboard.html"] = r["iso3"]
for fn, iso in (("norway-dashboard.html", "NOR"), ("iceland-dashboard.html", "ISL"),
                ("switzerland-dashboard.html", "CHE")):
    pages[fn] = iso

bad, seen, n = [], collections.defaultdict(dict), 0
for fn, iso in sorted(pages.items()):
    if not (BASE / fn).exists():
        continue
    P = payload(fn)
    for code, R in (P.get("ranks") or {}).items():
        n += 1
        # 1. the pool is countries with pages, never an aggregate
        for side in ("top", "bottom"):
            if R[side]["iso3"] in AGG:
                bad.append(f"{iso}/{code}: {side} is {R[side]['iso3']}, an aggregate")
            if R[side]["iso3"] not in POOL:
                bad.append(f"{iso}/{code}: {side} {R[side]['iso3']} is outside the page set")
        # 2. recompute the common year by the stated rule
        have = {i: table[(i, code)] for i in POOL if table[(i, code)]}
        years = sorted({y for d in have.values() for y in d}, reverse=True)
        year = next((y for y in years
                     if sum(1 for d in have.values() if y in d) >= 0.8 * len(have)), None)
        if year != R["year"]:
            bad.append(f"{iso}/{code}: year {R['year']} but the rule gives {year}")
            continue
        # 3. recompute the rank and the endpoints
        vals = sorted(((i, d[year]) for i, d in have.items() if year in d), key=lambda t: -t[1])
        order = [i for i, _ in vals]
        if iso not in order:
            bad.append(f"{iso}/{code}: ranked but has no {year} value")
            continue
        for got, want, what in ((R["rank"], order.index(iso) + 1, "rank"),
                                (R["n"], len(vals), "n"),
                                (R["top"]["iso3"], order[0], "top"),
                                (R["bottom"]["iso3"], order[-1], "bottom")):
            if got != want:
                bad.append(f"{iso}/{code}: {what} {got}, recomputes to {want}")
        if abs(R["value"] - table[(iso, code)][year]) > 0.011:
            bad.append(f"{iso}/{code}: value {R['value']} != store {table[(iso, code)][year]}")
        if not 1 <= R["rank"] <= R["n"]:
            bad.append(f"{iso}/{code}: rank {R['rank']} outside 1..{R['n']}")
        seen[code][iso] = (R["rank"], R["n"], R["year"])

# 4. every page must agree about the same indicator
for code, d in seen.items():
    ns = {v[1] for v in d.values()}
    ys = {v[2] for v in d.values()}
    if len(ns) > 1 or len(ys) > 1:
        bad.append(f"{code}: pages disagree — n={sorted(ns)} year={sorted(ys)}")
    ranks = sorted(v[0] for v in d.values())
    if len(ranks) != len(set(ranks)):
        bad.append(f"{code}: duplicate ranks across pages {ranks}")

print(f"{n} rank chips across {len(seen)} indicators · pool of {len(POOL)} countries")
for code, d in sorted(seen.items()):
    a = next(iter(d.values()))
    print(f"  {code:24} {len(d):>2} pages ranked, of {a[1]}, year {a[2]}")
print(f"{len(bad)} problem(s)")
for b in bad:
    print("  *** " + b)
sys.exit(1 if bad else 0)
