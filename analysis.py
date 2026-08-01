#!/usr/bin/env python3
"""Comparative analysis: did EU membership change member states' trajectories,
relative to comparable non-members?

Method
------
1. EVENT TIME. Every country's series is re-indexed so t=0 is its accession year.
   Non-members have no accession, so they are aligned to each treated country's
   accession year in turn (the standard approach for staggered adoption).

2. BLOCS. West / South / East, because post-war starting points differ so much
   that pooling them would be meaningless.

3. DIFFERENCE-IN-DIFFERENCES. For each treated country i with accession year T:
       pre_i  = mean outcome over [T-5, T-1]
       post_i = mean outcome over [T+6, T+10]
       delta_i = post_i - pre_i
   and for each control c the SAME calendar windows are used, so common shocks
   (2008, 2020) hit both sides. The estimate is delta_i - mean_c(delta_c).
   For income this runs on log GDP per capita PPP, so the result reads as an
   approximate percentage difference.

What this can and cannot show is documented in the generated page. The headline
caveat: accession was not random, so part of any measured gap is selection —
countries joined because they already qualified.
"""
import csv, json, math, os, statistics, collections, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

PRE = (-5, -1)       # pre-accession window, inclusive, relative to t=0
POST = (6, 10)       # medium-run post-accession window
TREND_RANGE = (-8, 16)

# ---------------------------------------------------------------- load
series = collections.defaultdict(dict)
for r in csv.DictReader(open(os.path.join(DATA, "indicators.csv"), encoding="utf-8")):
    if r["value"]:
        series[(r["iso3"], r["indicator_code"])][int(r["year"])] = float(r["value"])

blocs = list(csv.DictReader(open(os.path.join(DATA, "blocs.csv"), encoding="utf-8")))
meta = {b["iso3"]: b for b in blocs}
members = [b for b in blocs if b["group"] == "member"]
controls = [b for b in blocs if b["group"] == "control"]


def val(iso, code, year, log=False):
    v = series.get((iso, code), {}).get(year)
    if v is None:
        return None
    if log:
        return math.log(v) if v > 0 else None
    return v


def window_mean(iso, code, lo, hi, log=False):
    vals = [val(iso, code, y, log) for y in range(lo, hi + 1)]
    vals = [v for v in vals if v is not None]
    # require at least 3 of the 5 years, else the window is not comparable
    return statistics.fmean(vals) if len(vals) >= 3 else None


# ---------------------------------------------------------------- DiD
def did(code, log=False, scale=1.0):
    """Return per-country DiD estimates grouped by bloc, plus control detail."""
    out = {}
    for bloc in ("West", "South", "East"):
        ctrls = [c for c in controls if c["control_for"] == bloc]
        rows, skipped = [], []
        for m in members:
            if m["bloc"] != bloc or not m["accession_year"]:
                continue
            T = int(m["accession_year"])
            pre = window_mean(m["iso3"], code, T + PRE[0], T + PRE[1], log)
            post = window_mean(m["iso3"], code, T + POST[0], T + POST[1], log)
            if pre is None or post is None:
                skipped.append({"iso3": m["iso3"], "name": m["name"], "accession": T,
                                "why": "no pre-accession data" if pre is None else "no post-accession data"})
                continue
            d_treat = (post - pre) * scale
            cdeltas = []
            for c in ctrls:
                cpre = window_mean(c["iso3"], code, T + PRE[0], T + PRE[1], log)
                cpost = window_mean(c["iso3"], code, T + POST[0], T + POST[1], log)
                if cpre is not None and cpost is not None:
                    cdeltas.append({"iso3": c["iso3"], "name": c["name"],
                                    "delta": (cpost - cpre) * scale})
            if not cdeltas:
                skipped.append({"iso3": m["iso3"], "name": m["name"], "accession": T,
                                "why": "no control country has data for this window"})
                continue
            cmean = statistics.fmean(d["delta"] for d in cdeltas)
            rows.append({"iso3": m["iso3"], "name": m["name"], "accession": T,
                         "treated": round(d_treat, 2), "control": round(cmean, 2),
                         "did": round(d_treat - cmean, 2),
                         "nControls": len(cdeltas)})
        rows.sort(key=lambda r: r["did"], reverse=True)
        ests = [r["did"] for r in rows]
        out[bloc] = {
            "rows": rows, "skipped": skipped,
            "controls": [c["name"] for c in ctrls],
            "mean": round(statistics.fmean(ests), 2) if ests else None,
            "median": round(statistics.median(ests), 2) if ests else None,
            "min": round(min(ests), 2) if ests else None,
            "max": round(max(ests), 2) if ests else None,
            "n": len(rows),
            "positive": sum(1 for e in ests if e > 0),
        }
    return out


# -------------------------------------------- convergence-adjusted DiD
def convergence_adjusted(code_growth, code_level, scale=100.0):
    """Naive DiD is biased by beta-convergence: poorer economies grow faster
    mechanically, and every available post-communist control is poorer than
    most Eastern members. So a plain treated-minus-control comparison penalises
    the richer members for a reason that has nothing to do with membership.

    Correction: use ALL non-members (EFTA and Western Balkans together, spanning
    roughly 30% to 160% of EU income) to fit the empirical relationship between
    starting income and subsequent growth, then ask how far each member sits
    above or below that non-member convergence line.

    The pooled fit is used only to estimate the slope of catch-up growth — not
    as a like-for-like counterpart, which is what the bloc-matched controls are
    for. With eight controls the slope is indicative, not precise; r2 is
    reported so the reader can judge it.
    """
    out = {}
    for bloc in ("West", "South", "East"):
        treated = [m for m in members if m["bloc"] == bloc and m["accession_year"]]
        rows, fits = [], {}
        for m in treated:
            T = int(m["accession_year"])
            pre = window_mean(m["iso3"], code_growth, T + PRE[0], T + PRE[1], log=True)
            post = window_mean(m["iso3"], code_growth, T + POST[0], T + POST[1], log=True)
            lvl = window_mean(m["iso3"], code_level, T + PRE[0], T + PRE[1])
            if pre is None or post is None or lvl is None:
                continue
            # fit growth ~ starting level across ALL non-members for this window
            if T not in fits:
                pts = []
                for c in controls:
                    cpre = window_mean(c["iso3"], code_growth, T + PRE[0], T + PRE[1], log=True)
                    cpost = window_mean(c["iso3"], code_growth, T + POST[0], T + POST[1], log=True)
                    clvl = window_mean(c["iso3"], code_level, T + PRE[0], T + PRE[1])
                    if None not in (cpre, cpost, clvl):
                        pts.append((clvl, (cpost - cpre) * scale, c["name"]))
                if len(pts) >= 4:
                    xs = [p[0] for p in pts]
                    ys = [p[1] for p in pts]
                    mx, my = statistics.fmean(xs), statistics.fmean(ys)
                    sxx = sum((x - mx) ** 2 for x in xs)
                    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
                    a = my - b * mx
                    ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
                    ss_tot = sum((y - my) ** 2 for y in ys)
                    fits[T] = {"a": a, "b": b, "n": len(pts),
                               "r2": round(1 - ss_res / ss_tot, 3) if ss_tot else None,
                               "points": [{"level": round(p[0], 1), "growth": round(p[1], 1),
                                           "name": p[2]} for p in pts]}
                else:
                    fits[T] = None
            f = fits[T]
            if not f:
                continue
            actual = (post - pre) * scale
            predicted = f["a"] + f["b"] * lvl
            rows.append({"iso3": m["iso3"], "name": m["name"], "accession": T,
                         "level": round(lvl, 1), "actual": round(actual, 1),
                         "predicted": round(predicted, 1),
                         "excess": round(actual - predicted, 1)})
        rows.sort(key=lambda r: r["excess"], reverse=True)
        ex = [r["excess"] for r in rows]
        out[bloc] = {
            "rows": rows, "n": len(rows),
            "mean": round(statistics.fmean(ex), 1) if ex else None,
            "median": round(statistics.median(ex), 1) if ex else None,
            "min": round(min(ex), 1) if ex else None,
            "max": round(max(ex), 1) if ex else None,
            "positive": sum(1 for e in ex if e > 0),
            "fits": {str(k): v for k, v in fits.items() if v},
        }
    return out


# ------------------------------------------------- event-time mean paths
def event_paths(code, log=False, rebase=True, scale=1.0):
    """Mean treated and mean control path in event time, per bloc.

    Controls are aligned to each treated country's accession year in turn, so
    the control path reflects the same calendar years as the treated group.
    Both paths are rebased to 0 at t=0 when `rebase`, so they start together
    and any divergence is visible.
    """
    out = {}
    es = list(range(TREND_RANGE[0], TREND_RANGE[1] + 1))
    for bloc in ("West", "South", "East"):
        ctrls = [c for c in controls if c["control_for"] == bloc]
        treated = [m for m in members if m["bloc"] == bloc and m["accession_year"]]
        tvals, cvals, per_country = {e: [] for e in es}, {e: [] for e in es}, []
        for m in treated:
            T = int(m["accession_year"])
            base = val(m["iso3"], code, T, log)
            if base is None:
                continue
            path = []
            for e in es:
                v = val(m["iso3"], code, T + e, log)
                pv = None if v is None else ((v - base) * scale if rebase else v * scale)
                path.append(None if pv is None else round(pv, 3))
                if pv is not None:
                    tvals[e].append(pv)
            if any(p is not None for p in path):
                per_country.append({"iso3": m["iso3"], "name": m["name"],
                                    "accession": T, "path": path})
            for c in ctrls:
                cbase = val(c["iso3"], code, T, log)
                if cbase is None:
                    continue
                for e in es:
                    v = val(c["iso3"], code, T + e, log)
                    if v is not None:
                        cvals[e].append((v - cbase) * scale if rebase else v * scale)
        out[bloc] = {
            "es": es,
            "treated": [round(statistics.fmean(tvals[e]), 3) if len(tvals[e]) >= 2 else None for e in es],
            "control": [round(statistics.fmean(cvals[e]), 3) if len(cvals[e]) >= 2 else None for e in es],
            "treatedN": [len(tvals[e]) for e in es],
            "controlN": [len(cvals[e]) for e in es],
            "countries": per_country,
            "controlNames": [c["name"] for c in ctrls],
        }
    return out


# ---------------------------------------------------------------- build
LOG100 = 100.0  # log-difference × 100 ≈ percent


def add_ci(block, key):
    """Attach a 95% interval for the mean across treated countries.

    This is the spread of country-level estimates, not a model standard error:
    it answers "is the average effect distinguishable from zero given how much
    countries differ from each other". With n around 10 it is wide by
    construction, which is the honest situation rather than a defect.
    """
    for bloc, d in block.items():
        vals = [r[key] for r in d.get("rows", [])]
        if len(vals) < 3:
            d["ci"] = None
            continue
        sd = statistics.stdev(vals)
        se = sd / math.sqrt(len(vals))
        lo, hi = statistics.fmean(vals) - 1.96 * se, statistics.fmean(vals) + 1.96 * se
        d["ci"] = {"lo": round(lo, 1), "hi": round(hi, 1), "sd": round(sd, 1),
                   "se": round(se, 1), "crossesZero": lo <= 0 <= hi}
    return block

payload = {
    "generated": datetime.date.today().isoformat(),
    "pre": PRE, "post": POST,
    "blocs": {b: [m["name"] for m in members if m["bloc"] == b] for b in ("West", "South", "East")},
    "controlsByBloc": {b: [c["name"] for c in controls if c["control_for"] == b]
                       for b in ("West", "South", "East")},
    "measures": [
        {"id": "income", "label": "Income per head",
         "unit": "%", "dp": 1,
         "desc": "Log GDP per capita (PPP), so a difference-in-differences result reads as "
                 "an approximate percentage gap in income per head.",
         "did": add_ci(did("NY.GDP.PCAP.PP.CD", log=True, scale=LOG100), "did"),
         "paths": event_paths("NY.GDP.PCAP.PP.CD", log=True, scale=LOG100),
         "pathLabel": "Cumulative income growth since accession year, % (log points)"},
        {"id": "convergence", "label": "Convergence with the EU average",
         "unit": "pp", "dp": 1,
         "desc": "GDP per capita (PPP) as a percentage of the EU-wide average. "
                 "A positive result means closing the gap on the Union faster than "
                 "comparable non-members did.",
         "did": add_ci(did("DERIVED.PPP.PCT.EU"), "did"),
         "paths": event_paths("DERIVED.PPP.PCT.EU"),
         "pathLabel": "Change in % of EU average since accession year (pp)"},
        {"id": "unemployment", "label": "Unemployment",
         "unit": "pp", "dp": 1, "lowerIsBetter": True,
         "desc": "Unemployment rate, ILO-modelled. A negative result means "
                 "unemployment fell further than in comparable non-members.",
         "did": add_ci(did("SL.UEM.TOTL.ZS"), "did"),
         "paths": event_paths("SL.UEM.TOTL.ZS"),
         "pathLabel": "Change in unemployment rate since accession year (pp)"},
    ],
    "adjusted": add_ci(convergence_adjusted("NY.GDP.PCAP.PP.CD", "DERIVED.PPP.PCT.EU"), "excess"),
}

out = os.path.join(BASE, "analysis_payload.json")
json.dump(payload, open(out, "w", encoding="utf-8"), ensure_ascii=False)

print("analysis_payload.json written\n")
for m in payload["measures"]:
    print(f"--- {m['label']} ---")
    for bloc in ("West", "South", "East"):
        d = m["did"][bloc]
        if d["n"]:
            print(f"  {bloc:6s} n={d['n']:2d}  DiD mean {d['mean']:+7.2f} {m['unit']}"
                  f"  median {d['median']:+7.2f}  range [{d['min']:+.1f}, {d['max']:+.1f}]"
                  f"  positive {d['positive']}/{d['n']}  vs {len(d['controls'])} controls")
        else:
            print(f"  {bloc:6s} n= 0  — no country has both windows covered")
        if d["skipped"]:
            print(f"         excluded: " + ", ".join(f"{s['iso3']}({s['why'][:22]})" for s in d["skipped"]))

# ---------------------------------------------------------------- render
tpl = os.path.join(BASE, "analysis_template.html")
if os.path.exists(tpl):
    html = open(tpl, encoding="utf-8").read()
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    open(os.path.join(BASE, "analysis.html"), "w", encoding="utf-8").write(
        html.replace("__PAYLOAD__", blob))
    print("\nanalysis.html written")
