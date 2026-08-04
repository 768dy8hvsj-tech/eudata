#!/usr/bin/env python3
"""Brexit run in reverse: the one country that left.

Design notes that matter more than the arithmetic.

1. TWO DATES, NOT ONE. The referendum was June 2016 — the moment expectations changed,
   sterling fell and investment decisions started being taken. Actual departure from the
   single market and customs union was 1 January 2021. Anything measured only from 2021
   misses four and a half years of anticipation; anything measured only from 2016 attributes
   to Brexit a period when the UK was still a full member. Both are reported.

2. COVID IS THE PROBLEM, AND THE COMPARATORS ARE THE SOLUTION. The transition ended on
   31 December 2020, one calendar quarter after the deepest global recession in living memory.
   No before/after comparison of the UK against itself can separate the two. But COVID hit
   every European country in the same years, so a difference against comparators in the SAME
   calendar years removes it — that is precisely what a common shock does in this design.

3. COMPARATORS. Two sets, deliberately. The tight set is Denmark and Sweden: rich, western,
   EU members that kept their own currency, which is what the UK was. The broad set adds the
   large western economies. If the two disagree, the result is about composition, not Brexit.
"""
import csv, math, statistics, collections, json

s = collections.defaultdict(dict)
for r in csv.DictReader(open("data/indicators.csv", encoding="utf-8")):
    if r["value"]:
        s[(r["iso3"], r["indicator_code"])][int(r["year"])] = float(r["value"])

TIGHT = ["DNK", "SWE"]
BROAD = ["DNK", "SWE", "FRA", "DEU", "ITA", "ESP", "NLD", "BEL"]
NAMES = {"DNK": "Denmark", "SWE": "Sweden", "FRA": "France", "DEU": "Germany",
         "ITA": "Italy", "ESP": "Spain", "NLD": "Netherlands", "BEL": "Belgium"}

MEASURES = [
    ("Trade openness", "DERIVED.TRADE.OPEN", "pp of GDP", 1, False),
    ("GNI vs EU average", "DERIVED.GNI.PCT.EU", "pp", 1, False),
    ("Income per head (log)", "NY.GDP.PCAP.KD", "%", 1, True),
    ("FDI inflows", "BX.KLT.DINV.WD.GD.ZS", "pp of GDP", 1, False),
    ("Net migration", "DERIVED.NETM.P1000", "per 1,000", 2, False),
    ("Unemployment", "SL.UEM.TOTL.ZS", "pp", 1, False),
]

WINDOWS = [
    ("Referendum", (2011, 2015), (2016, 2019),
     "2011–15 against 2016–19: the anticipation period, ending before COVID so the estimate "
     "is clean of it entirely."),
    ("Left the single market", (2011, 2015), (2021, 2025),
     "2011–15 against 2021–25: after actual departure. Spans the COVID recovery, which is why "
     "the comparators matter — they lived through the same years."),
]


def wmean(iso, code, lo, hi, log=False):
    d = s.get((iso, code), {})
    v = [d[y] for y in range(lo, hi + 1) if y in d]
    if log:
        v = [math.log(x) for x in v if x > 0]
    return statistics.fmean(v) if len(v) >= 3 else None


def run(code, pre, post, pool, log=False):
    scale = 100.0 if log else 1.0
    uk_pre, uk_post = wmean("GBR", code, *pre, log), wmean("GBR", code, *post, log)
    if uk_pre is None or uk_post is None:
        return None
    uk = (uk_post - uk_pre) * scale
    cs = []
    for c in pool:
        a, b = wmean(c, code, *pre, log), wmean(c, code, *post, log)
        if a is not None and b is not None:
            cs.append(((b - a) * scale, c))
    if len(cs) < 2:
        return None
    cm = statistics.fmean(x for x, _ in cs)
    return {"uk": round(uk, 2), "ctrl": round(cm, 2), "diff": round(uk - cm, 2),
            "n": len(cs), "detail": [(NAMES[c], round(x, 2)) for x, c in sorted(cs)]}


out = {}
for wlabel, pre, post, note in WINDOWS:
    print(f"\n=== {wlabel}: {pre[0]}–{pre[1]} vs {post[0]}–{post[1]} ===")
    print(f"    {note}")
    print(f"    {'measure':24s} {'UK':>8s} {'tight':>8s} {'diff':>8s}   {'broad':>8s} {'diff':>8s}")
    for label, code, unit, dp, log in MEASURES:
        t = run(code, pre, post, TIGHT, log)
        b = run(code, pre, post, BROAD, log)
        if not t and not b:
            print(f"    {label:24s} no data")
            continue
        tf = f"{t['ctrl']:+8.2f} {t['diff']:+8.2f}" if t else "     n/a      n/a"
        bf = f"{b['ctrl']:+8.2f} {b['diff']:+8.2f}" if b else "     n/a      n/a"
        uk = t["uk"] if t else b["uk"]
        print(f"    {label:24s} {uk:+8.2f} {tf}   {bf}   ({unit})")
        out[(wlabel, label)] = {"tight": t, "broad": b}

# placebo: the same estimator on a period when nothing happened
print("\n=== PLACEBO: 2006–2010 vs 2011–2015, when the UK was an unremarkable member ===")
for label, code, unit, dp, log in MEASURES:
    t = run(code, (2006, 2010), (2011, 2015), TIGHT, log)
    b = run(code, (2006, 2010), (2011, 2015), BROAD, log)
    if not t and not b:
        continue
    tf = f"{t['diff']:+8.2f}" if t else "     n/a"
    bf = f"{b['diff']:+8.2f}" if b else "     n/a"
    print(f"    {label:24s} tight {tf}   broad {bf}   ({unit})")
