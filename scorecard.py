#!/usr/bin/env python3
"""Per-country synthesis scorecard: what the study can and cannot say about
who gains and who does not. Every column is either an accounting fact or a
descriptive trajectory -- the causal tier is bloc-level and lives in analysis.py.
"""
import csv, collections, json, os, statistics

BASE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(BASE, "data")

vals = collections.defaultdict(dict)   # (iso, code) -> {year: value}
name = {}
for r in csv.DictReader(open(os.path.join(D, "indicators.csv"), encoding="utf-8")):
    try: v = float(r["value"])
    except: continue
    vals[(r["iso3"], r["indicator_code"])][int(r["year"])] = v
    name[r["iso3"]] = r["country"]

acc = {}
bloc = {}
for r in csv.DictReader(open(os.path.join(D, "blocs.csv"), encoding="utf-8")):
    if r["group"] == "member" and r["accession_year"].strip().isdigit():
        acc[r["iso3"]] = int(r["accession_year"])
        bloc[r["iso3"]] = r["bloc"]
members = sorted(acc)
print(len(members), "members with accession year")

def at(iso, code, y, tol=2):
    s = vals.get((iso, code), {})
    if not s: return None
    for d in range(0, tol+1):
        for yy in (y-d, y+d):
            if yy in s: return s[yy]
    return None

def last(iso, code, floor=2018):
    s = vals.get((iso, code), {})
    ys = [y for y in s if y >= floor]
    return s[max(ys)] if ys else None

CONV = "DERIVED.GNI.PCT.EU"
rows = []
for iso in members:
    a = acc[iso]
    base_y = max(a, 1996)
    c0 = at(iso, CONV, base_y, 3)
    c1 = last(iso, CONV)
    t0 = at(iso, "DERIVED.TRADE.OPEN", base_y, 3)
    t1 = last(iso, "DERIVED.TRADE.OPEN")
    # budget: cumulative and mean % GNI, both conventions
    out = {}
    for key, code in (("comm", "DERIVED.BUDGET.NET"), ("broad", "DERIVED.BUDGET.NET.BROAD")):
        s = vals.get((iso, code), {})
        out[key+"_cum"] = sum(s.values())/1000 if s else None      # EUR bn
        p = vals.get((iso, code + ".PCT.GNI"), {})
        out[key+"_pct"] = statistics.mean(p.values()) if p else None
        out[key+"_n"] = len(s)
    rows.append(dict(iso=iso, name=name.get(iso, iso), acc=a, base=base_y, bloc=bloc[iso],
                     c0=c0, c1=c1, dc=(c1-c0) if (c0 and c1) else None,
                     t0=t0, t1=t1, dt=(t1-t0) if (t0 and t1) else None, **out))

rows.sort(key=lambda r: -(r["dc"] if r["dc"] is not None else -999))
hdr = f"{'country':<16}{'acc':>5}{'from':>6}{'conv0':>8}{'conv now':>9}{'Δconv':>8}{'Δtrade':>8}{'net €bn':>10}{'broad €bn':>11}{'%GNI/yr':>9}{'yrs':>5}"
print("\n=== MEMBERS ===\n" + hdr)
for r in rows:
    f = lambda v, p=1: ("—" if v is None else f"{v:.{p}f}")
    print(f"{r['name']:<16}{r['acc']:>5}{r['base']:>6}{f(r['c0']):>8}{f(r['c1']):>9}"
          f"{f(r['dc']):>8}{f(r['dt']):>8}{f(r['comm_cum'],1):>10}{f(r['broad_cum'],1):>11}"
          f"{f(r['broad_pct'],2):>9}{r['broad_n']:>5}")

nm = sorted(set(name) - set(members) - {"EUU", "EMU", "WLD", "CHN", "USA"})
print("\n=== NON-MEMBERS === (2000 -> latest)")
nrows = []
for iso in nm:
    c0 = at(iso, CONV, 2000, 3); c1 = last(iso, CONV)
    t0 = at(iso, "DERIVED.TRADE.OPEN", 2000, 3); t1 = last(iso, "DERIVED.TRADE.OPEN")
    nrows.append((iso, name[iso], c0, c1, (c1-c0) if (c0 and c1) else None,
                  (t1-t0) if (t0 and t1) else None))
nrows.sort(key=lambda r: -(r[4] if r[4] is not None else -999))
print(f"{'country':<20}{'conv2000':>10}{'conv now':>10}{'Δconv':>8}{'Δtrade':>8}")
for iso, n, c0, c1, dc, dt in nrows:
    f = lambda v: ("—" if v is None else f"{v:.1f}")
    print(f"{n:<20}{f(c0):>10}{f(c1):>10}{f(dc):>8}{f(dt):>8}")

json.dump({"members": rows, "nonmembers": nrows}, open(os.path.join(BASE, "scorecard.json"), "w"), indent=1)
