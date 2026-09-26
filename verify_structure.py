#!/usr/bin/env python3
"""End-to-end check of structure.html, going back to the raw Eurostat file rather than to
the pipeline. Every value embedded in the page (all 18 sectors, all 8 families, every
country-year) is recomputed here from the raw numbers by an independent path and must
match to 0.001 percentage points. The CSV in data/structure.csv is checked the same way.
Spot values that anyone can confirm on the Eurostat site are printed at the end."""
import json, re, os, sys, csv
B = os.path.dirname(os.path.abspath(__file__))
raw = open(os.path.join(B, "data/raw/eurostat_nama_10_a64_B1G_1992-2025.txt"), encoding="utf-8").read().split("\n")[3:]
V = {}
for l in raw:
    if not l.strip(): continue
    g, c, y0, vals = l.split("|")[:4]
    if y0 == "-": continue
    for i, v in enumerate(vals.split(";")):
        if v: V[(g, c, int(y0) + i)] = float(v)
html = open(os.path.join(B, "structure.html"), encoding="utf-8").read()
P = json.loads(re.search(r'<script id="payload" type="application/json">(.*?)</script>', html, re.S).group(1).replace("<\\/", "</"))
REC = {"agri":"A01","forest":"A02","fish":"A03","mining":"B","foodmfg":"C10-C12","othermfg":"C|-C10-C12","energy":"D",
       "water":"E","constr":"F","trade":"G","transport":"H","hotels":"I","ict":"J","finance":"K","realestate":"L",
       "business":"M_N","public":"O-Q","other":"R-U"}
FAM = {"agri_forest":"A01+A02","fishing":"A03","mining_energy":"B+D+E","manufacturing":"C","construction":"F",
       "trade_transport":"G+H+I","business_finance":"J+K+L+M_N","public_other":"O-Q+R-U"}
def share(g, expr, y):
    tot = V.get((g, "TOTAL", y))
    if expr.startswith("C|-"):
        a, b = V.get((g, "C", y)), V.get((g, "C10-C12", y))
        return None if a is None or b is None else 100 * (a - b) / tot
    s = 0
    for c in expr.split("+"):
        v = V.get((g, c, y))
        if v is None: return None
        s += v
    return 100 * s / tot
n = bad = 0
for c in P["countries"]:
    g = c["geo"]
    for i, y in enumerate(c["years"]):
        for k, e in REC.items():
            want, got = share(g, e, y), c["detail"][k][i]
            n += 1
            if (want is None) != (got is None) or (want is not None and abs(want - got) > 0.001):
                bad += 1; print("DETAIL", g, y, k, want, got)
        if y in c["complete"]:
            for k, e in FAM.items():
                want, got = share(g, e, y), c["family"][k][i]
                if want is None:   # published only in combined form: Malta B-E, Switzerland A
                    if g == "MT" and k == "mining_energy": want = share(g, "B-E", y) - share(g, "C", y)
                    elif g == "CH" and k == "agri_forest": want = share(g, "A", y)
                    elif g == "CH" and k == "fishing": want = 0.0
                n += 1
                if want is None or abs(want - got) > 0.001: bad += 1; print("FAMILY", g, y, k, want, got)
            s = sum(c["family"][k][i] for k in FAM)
            if abs(s - 100) > 0.05: bad += 1; print("SUM", g, y, s)
rows = list(csv.DictReader(open(os.path.join(B, "data/structure.csv"), encoding="utf-8")))
iso2geo = {c["iso3"]: c["geo"] for c in P["countries"]}
for r in rows:
    want = share(iso2geo[r["iso3"]], REC[r["sector_key"]], int(r["year"])); n += 1
    if want is None or abs(want - float(r["share_of_gva_pct"])) > 0.001: bad += 1; print("CSV", r)
print(f"{n} values checked, {bad} mismatches")
for g, c, y in [("IS","A03",1995),("IS","A03",2025),("NO","B",2022),("LU","K",2024),("IE","C",2015)]:
    print(f"  {g} {c} {y}: {V[(g,c,y)]:,} of {V[(g,'TOTAL',y)]:,} m NAC = {100*V[(g,c,y)]/V[(g,'TOTAL',y)]:.2f}%")
sys.exit(1 if bad else 0)
