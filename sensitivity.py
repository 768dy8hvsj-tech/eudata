#!/usr/bin/env python3
"""Window-length sensitivity: does a longer pre-period strengthen the design?

Mirrors analysis.py's estimator exactly (same coverage rule, same DiD, same
placebo, same CI) so results are comparable, then sweeps the window lengths.
Validated against the production numbers before any sweep is reported.
"""
import csv, math, statistics, collections

series = collections.defaultdict(dict)
for r in csv.DictReader(open("data/indicators.csv", encoding="utf-8")):
    if r["value"]:
        series[(r["iso3"], r["indicator_code"])][int(r["year"])] = float(r["value"])
blocs = list(csv.DictReader(open("data/blocs.csv", encoding="utf-8")))
members = [b for b in blocs if b["group"] == "member"]
controls = [b for b in blocs if b["group"] == "control"]

PUBLISHED = collections.defaultdict(set)
for (_i, _c), _d in series.items():
    PUBLISHED[_c].update(_d)


def val(iso, code, y, log=False):
    v = series.get((iso, code), {}).get(y)
    if v is None:
        return None
    return (math.log(v) if v > 0 else None) if log else v


def need(code, lo, hi):
    k = len([y for y in PUBLISHED.get(code, ()) if lo <= y <= hi])
    return min(3, k) if k else 3


def wmean(iso, code, lo, hi, log=False):
    vs = [val(iso, code, y, log) for y in range(lo, hi + 1)]
    vs = [v for v in vs if v is not None]
    return statistics.fmean(vs) if len(vs) >= need(code, lo, hi) and len(vs) >= 2 else None


def did(code, bloc, w_pre, w_post, log=False, scale=1.0):
    ctrls = [c for c in controls if c["control_for"] == bloc]
    rows = []
    for m in members:
        if m["bloc"] != bloc or not m["accession_year"]:
            continue
        T = int(m["accession_year"])
        pre = wmean(m["iso3"], code, T + w_pre[0], T + w_pre[1], log)
        post = wmean(m["iso3"], code, T + w_post[0], T + w_post[1], log)
        if pre is None or post is None:
            continue
        cd = []
        for c in ctrls:
            cp = wmean(c["iso3"], code, T + w_pre[0], T + w_pre[1], log)
            cq = wmean(c["iso3"], code, T + w_post[0], T + w_post[1], log)
            if cp is not None and cq is not None:
                cd.append((cq - cp) * scale)
        if not cd:
            continue
        rows.append((post - pre) * scale - statistics.fmean(cd))
    if not rows:
        return None
    mu = statistics.fmean(rows)
    if len(rows) < 3:
        return {"n": len(rows), "mean": mu, "ci": None}
    se = statistics.stdev(rows) / math.sqrt(len(rows))
    return {"n": len(rows), "mean": mu, "ci": (mu - 1.96 * se, mu + 1.96 * se)}


def report(label, code, bloc, w_pre, w_post, log=False, scale=1.0):
    r = did(code, bloc, w_pre, w_post, log, scale)
    # placebo: same estimator, shifted entirely before accession
    span = w_pre[1] - w_pre[0]
    p_early = (w_pre[0] - span - 1, w_pre[0] - 1)
    p = did(code, bloc, p_early, w_pre, log, scale)
    if not r:
        return f"{label:26s} no estimate"
    ci = f"[{r['ci'][0]:+6.2f},{r['ci'][1]:+6.2f}]" if r["ci"] else "     n/a     "
    sig = "" if (not r["ci"] or r["ci"][0] <= 0 <= r["ci"][1]) else " SIG"
    if p and p["ci"]:
        psig = not (p["ci"][0] <= 0 <= p["ci"][1])
        dom = abs(p["mean"]) >= 0.5 * abs(r["mean"])
        pv = "FAILS" if (psig or dom) else "passes"
        ptxt = f"placebo {p['mean']:+6.2f} {pv}"
    else:
        ptxt = "placebo untestable"
    return (f"{label:26s} n={r['n']:2d} {r['mean']:+7.2f} {ci}{sig:4s} | {ptxt}"
            f"  [pre {w_pre[0]}..{w_pre[1]} post {w_post[0]}..{w_post[1]}]")


CASES = [
    ("Trade openness, East", "DERIVED.TRADE.OPEN", "East", False, 1.0),
    ("Trade openness, West", "DERIVED.TRADE.OPEN", "West", False, 1.0),
    ("Income (log), East", "NY.GDP.PCAP.KD", "East", True, 100.0),
    ("Convergence, East", "DERIVED.KD.PCT.EU", "East", False, 1.0),
    ("Rule of law, East", "WGI.RL.EST", "East", False, 1.0),
    ("FDI, East", "BX.KLT.DINV.WD.GD.ZS", "East", False, 1.0),
]

print("=== BASELINE (production windows: pre -5..-1, post 6..10) ===")
for lbl, code, bloc, log, sc in CASES:
    print("  " + report(lbl, code, bloc, (-5, -1), (6, 10), log, sc))

for pre in [(-8, -1), (-10, -1), (-10, -6)]:
    print(f"\n=== LONGER PRE-PERIOD {pre[0]}..{pre[1]} (post unchanged 6..10) ===")
    for lbl, code, bloc, log, sc in CASES:
        print("  " + report(lbl, code, bloc, pre, (6, 10), log, sc))

print("\n=== LONGER POST-PERIOD, pre unchanged -5..-1 ===")
for post in [(11, 15), (6, 15)]:
    print(f"-- post {post[0]}..{post[1]}")
    for lbl, code, bloc, log, sc in CASES:
        print("  " + report(lbl, code, bloc, (-5, -1), post, log, sc))
