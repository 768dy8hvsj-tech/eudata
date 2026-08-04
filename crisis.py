#!/usr/bin/env python3
"""Crisis resilience: did EU members fall further, or recover faster, than non-members?

Why this is a different and in one respect better test than the accession design.
A crisis is a common shock landing on everyone in the same calendar year, so the
comparison does not rest on parallel trends — it rests on a shared starting point,
which the crisis itself supplies. What it cannot do is randomise membership: countries
were not assigned to the EU, so any gap still mixes effect with selection.

Episodes are derived from the data, not asserted. A year counts as a synchronised
downturn when a large share of the 41 entities contract together; that picks out
2009 (90% contracting) and 2020 (93%) as global, and 2012 (49%) as something else —
see the concentration test, which is the point of including it.

Depth  = trough as % of the pre-crisis peak.
Recovery = years from the pre-crisis peak until the peak level is regained.
"""
import csv, collections, statistics, json

CODE = "NY.GDP.PCAP.KD"
s = collections.defaultdict(dict)
for r in csv.DictReader(open("data/indicators.csv", encoding="utf-8")):
    if r["value"]:
        s[(r["iso3"], r["indicator_code"])][int(r["year"])] = float(r["value"])

regs = {r["iso3"]: r for r in csv.DictReader(open("data/regions.csv", encoding="utf-8"))}
meta = {r["iso3"]: r for r in csv.DictReader(open("data/countries.csv", encoding="utf-8"))}
blocs = {b["iso3"]: b for b in csv.DictReader(open("data/blocs.csv", encoding="utf-8"))}

EPISODES = [
    {"id": "gfc", "label": "Global financial crisis",
     "peakRange": (2006, 2008), "troughRange": (2009, 2013), "recoverBy": 2019},
    {"id": "covid", "label": "COVID-19",
     "peakRange": (2018, 2019), "troughRange": (2020, 2021), "recoverBy": 2025},
]


def episode(iso, ep):
    d = s.get((iso, CODE), {})
    pk = [(y, d[y]) for y in range(ep["peakRange"][0], ep["peakRange"][1] + 1) if y in d]
    tr = [(y, d[y]) for y in range(ep["troughRange"][0], ep["troughRange"][1] + 1) if y in d]
    if not pk or not tr:
        return None
    py, pv = max(pk, key=lambda t: t[1])
    ty, tv = min(tr, key=lambda t: t[1])
    if tv >= pv:                       # no contraction at all
        return {"peakYear": py, "depth": 0.0, "troughYear": ty, "recovYears": 0, "recovered": True}
    rec = None
    for y in range(ty, ep["recoverBy"] + 1):
        if y in d and d[y] >= pv:
            rec = y
            break
    return {"peakYear": py, "troughYear": ty,
            "depth": round((tv / pv - 1) * 100, 2),
            "recovYears": (rec - py) if rec else None,
            "recovered": rec is not None}


def euro_by(iso, year):
    e = (meta.get(iso, {}) or {}).get("euro_adopted", "") or ""
    e = e.strip()
    if not e:
        return False
    try:
        return int(e[:4]) <= year
    except ValueError:
        return False


# ---- concentration test: was 2012 a global shock or a European one?
print("=== Was the 2012 downturn global? share contracting, by group ===")
for y in (2009, 2012, 2020):
    grp = collections.defaultdict(lambda: [0, 0])
    for iso, r in regs.items():
        d = s.get((iso, CODE), {})
        if y not in d or (y - 1) not in d or not d[y - 1]:
            continue
        k = "EU member" if r["group"] == "member" else "non-member"
        grp[k][1] += 1
        if d[y] / d[y - 1] - 1 < 0:
            grp[k][0] += 1
    line = "  ".join(f"{k}: {v[0]}/{v[1]} ({v[0]/v[1]*100:.0f}%)" for k, v in sorted(grp.items()))
    print(f"  {y}   {line}")

out = {}
for ep in EPISODES:
    print(f"\n=== {ep['label']} ===")
    rows = []
    for iso, r in regs.items():
        e = episode(iso, ep)
        if not e:
            continue
        e.update(iso3=iso, name=r["name"], member=r["group"] == "member",
                 region=r["region"], euro=euro_by(iso, ep["troughRange"][0]))
        rows.append(e)
    seen = {}
    for e in rows:                      # regions.csv lists Belarus twice, deliberately
        seen[e["iso3"]] = e
    rows = list(seen.values())
    out[ep["id"]] = rows

    def summ(sel, lbl):
        sel = [x for x in sel]
        if not sel:
            return
        dep = [x["depth"] for x in sel]
        rc = [x["recovYears"] for x in sel if x["recovYears"] is not None]
        never = sum(1 for x in sel if x["recovYears"] is None)
        print(f"  {lbl:34s} n={len(sel):2d}  median depth {statistics.median(dep):+6.2f}%"
              f"   median recovery {statistics.median(rc) if rc else float('nan'):4.1f} yrs"
              f"   never recovered {never}")

    summ([x for x in rows if x["member"]], "EU members")
    summ([x for x in rows if not x["member"]], "non-members")
    if ep["id"] == "gfc":
        summ([x for x in rows if x["member"] and x["euro"]], "  EU members, euro by 2009")
        summ([x for x in rows if x["member"] and not x["euro"]], "  EU members, own currency 2009")

json.dump(out, open("crisis_payload.json", "w"), ensure_ascii=False)
print("\ncrisis_payload.json written")
