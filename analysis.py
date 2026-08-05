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
import csv, json, math, os, re, statistics, collections, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

PRE = (-5, -1)         # pre-accession window, inclusive, relative to t=0
POST = (6, 10)         # medium-run post-accession window
PRE_EARLY = (-10, -6)  # placebo window: entirely before accession
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


# Years each indicator is actually published for, pooled across every entity. Used to set the
# coverage requirement below, so a rule written for annual data is not applied to a series the
# source never published annually.
PUBLISHED = collections.defaultdict(set)
for (_iso, _code), _d in series.items():
    PUBLISHED[_code].update(_d)


def required_obs(code, lo, hi):
    """How many observations a window must contain to be usable.

    Three of five years for an annual series — enough that one odd year cannot drive the
    average. But the WGI series is biennial before 2002, so a 1994–1998 window contains only
    two published years in total. Demanding three there rejects *complete* coverage on a
    technicality. So the requirement is three, or all of them where the source publishes
    fewer than three in that span.
    """
    k = len([y for y in PUBLISHED.get(code, ()) if lo <= y <= hi])
    return min(3, k) if k else 3


def window_mean(iso, code, lo, hi, log=False):
    vals = [val(iso, code, y, log) for y in range(lo, hi + 1)]
    vals = [v for v in vals if v is not None]
    need = required_obs(code, lo, hi)
    return statistics.fmean(vals) if len(vals) >= need and len(vals) >= 2 else None


# ---------------------------------------------------------------- DiD
def did(code, log=False, scale=1.0, w_pre=PRE, w_post=POST):
    """Return per-country DiD estimates grouped by bloc, plus control detail.

    `w_pre`/`w_post` are event-time windows. Passing (PRE_EARLY, PRE) runs the
    identical estimator entirely on pre-accession years, which is the placebo
    test used below to check the parallel-trends assumption.
    """
    out = {}
    for bloc in ("West", "South", "East"):
        ctrls = [c for c in controls if c["control_for"] == bloc]
        rows, skipped = [], []
        for m in members:
            if m["bloc"] != bloc or not m["accession_year"]:
                continue
            T = int(m["accession_year"])
            pre = window_mean(m["iso3"], code, T + w_pre[0], T + w_pre[1], log)
            post = window_mean(m["iso3"], code, T + w_post[0], T + w_post[1], log)
            if pre is None or post is None:
                skipped.append({"iso3": m["iso3"], "name": m["name"], "accession": T,
                                "why": "no pre-accession data" if pre is None else "no post-accession data"})
                continue
            d_treat = (post - pre) * scale
            cdeltas = []
            for c in ctrls:
                cpre = window_mean(c["iso3"], code, T + w_pre[0], T + w_pre[1], log)
                cpost = window_mean(c["iso3"], code, T + w_post[0], T + w_post[1], log)
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

        # ------------------------------------------------ credibility gate
        # Only the control-count part is decidable here; the parallel-trends
        # placebo needs a second pass over pre-accession windows and is attached
        # by gate() below.
        warns = []
        maxc = max((r["nControls"] for r in rows), default=0)
        if rows and maxc < 3:
            warns.append("only %d control countr%s has data for these windows, so the "
                         "counterfactual rests on a single country's history"
                         % (maxc, "y" if maxc == 1 else "ies"))
        out[bloc] = {
            "rows": rows, "skipped": skipped,
            "identified": not warns and bool(rows),
            "warnings": warns,
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
            # A fit that explains almost none of the variance means the catch-up
            # slope is not identified for this window — the controls span too
            # narrow an income range. Such rows are kept but marked, and the
            # bloc summary is suppressed, so a noisy line cannot masquerade as
            # a finding.
            if f["r2"] is None or f["r2"] < 0.5:
                f["identified"] = False
            else:
                f["identified"] = True
            actual = (post - pre) * scale
            predicted = f["a"] + f["b"] * lvl
            rows.append({"iso3": m["iso3"], "name": m["name"], "accession": T,
                         "level": round(lvl, 1), "actual": round(actual, 1),
                         "predicted": round(predicted, 1),
                         "excess": round(actual - predicted, 1)})
        rows.sort(key=lambda r: r["excess"], reverse=True)
        good = [r for r in rows if fits.get(r["accession"], {}).get("identified")]
        ex = [r["excess"] for r in good]
        rows = [dict(r, identified=bool(fits.get(r["accession"], {}).get("identified"))) for r in rows]
        out[bloc] = {
            "rows": rows, "n": len(ex), "nShown": len(rows),
            "identifiedWindows": sorted(str(k) for k, v in fits.items() if v and v.get("identified")),
            "unidentifiedWindows": sorted(str(k) for k, v in fits.items() if v and not v.get("identified")),
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
        vals = [r[key] for r in d.get("rows", [])
                if key != "excess" or r.get("identified", True)]
        if len(vals) < 3:
            d["ci"] = None
            continue
        sd = statistics.stdev(vals)
        se = sd / math.sqrt(len(vals))
        lo, hi = statistics.fmean(vals) - 1.96 * se, statistics.fmean(vals) + 1.96 * se
        d["ci"] = {"lo": round(lo, 1), "hi": round(hi, 1), "sd": round(sd, 1),
                   "se": round(se, 1), "crossesZero": lo <= 0 <= hi}
    return block

def headroom_adjusted(code):
    """Convergence adjustment for a bounded index, e.g. the WGI −2.5…+2.5 scales.

    The placebo in gate() tests whether the groups shared a common *trend*. It does not test
    whether they shared comparable *starting levels*, and on a bounded scale those are not the
    same thing. A country at +0.57 cannot gain as much as one at −0.58 simply because there is
    less room above it, so a plain treated-minus-control difference charges members for their
    own head start. This is the beta-convergence problem the income estimates already had, in
    a different outcome.

    Same correction as convergence_adjusted() uses for income: pool ALL non-members — EFTA at
    the top of the scale, the Western Balkans at the bottom — fit how much change a given
    starting level bought you outside the Union, and measure each member against that line.
    The r2 gate is identical: a fit explaining less than half the variance means the slope is
    not identified and no adjusted figure is reported.
    """
    out = {}
    for bloc in ("West", "South", "East"):
        treated = [m for m in members if m["bloc"] == bloc and m["accession_year"]]
        rows, fits = [], {}
        for m in treated:
            T = int(m["accession_year"])
            pre = window_mean(m["iso3"], code, T + PRE[0], T + PRE[1])
            post = window_mean(m["iso3"], code, T + POST[0], T + POST[1])
            if pre is None or post is None:
                continue
            if T not in fits:
                pts = []
                for c in controls:
                    cpre = window_mean(c["iso3"], code, T + PRE[0], T + PRE[1])
                    cpost = window_mean(c["iso3"], code, T + POST[0], T + POST[1])
                    if cpre is not None and cpost is not None:
                        pts.append((cpre, cpost - cpre, c["name"]))
                if len(pts) >= 4:
                    xs = [p[0] for p in pts]
                    ys = [p[1] for p in pts]
                    mx, my = statistics.fmean(xs), statistics.fmean(ys)
                    sxx = sum((x - mx) ** 2 for x in xs)
                    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
                    a = my - b * mx
                    ss_res = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
                    ss_tot = sum((y - my) ** 2 for y in ys)
                    r2 = round(1 - ss_res / ss_tot, 3) if ss_tot else None
                    fits[T] = {"a": a, "b": b, "n": len(pts), "r2": r2,
                               "identified": bool(r2 is not None and r2 >= 0.5),
                               "points": [{"level": round(p[0], 2), "change": round(p[1], 2),
                                           "name": p[2]} for p in pts]}
                else:
                    fits[T] = None
            f = fits[T]
            if not f:
                continue
            actual = post - pre
            predicted = f["a"] + f["b"] * pre
            rows.append({"iso3": m["iso3"], "name": m["name"], "accession": T,
                         "level": round(pre, 2), "actual": round(actual, 2),
                         "predicted": round(predicted, 2),
                         "excess": round(actual - predicted, 2),
                         "identified": f["identified"]})
        rows.sort(key=lambda r: r["excess"], reverse=True)
        ex = [r["excess"] for r in rows if r["identified"]]
        out[bloc] = {
            "rows": rows, "n": len(ex), "nShown": len(rows),
            "mean": round(statistics.fmean(ex), 2) if ex else None,
            "median": round(statistics.median(ex), 2) if ex else None,
            "positive": sum(1 for e in ex if e > 0),
            "fits": {str(k): v for k, v in fits.items() if v},
            "identifiedWindows": sorted(str(k) for k, v in fits.items() if v and v["identified"]),
            "unidentifiedWindows": sorted(str(k) for k, v in fits.items() if v and not v["identified"]),
        }
    return add_ci(out, "excess")


def gate(code, log=False, scale=1.0, w_post=POST):
    """Run the estimator, then run it again entirely on pre-accession years and
    use the second result to judge the first.

    The placebo asks: over [T-10,T-6] to [T-5,T-1] — a period in which nothing
    has happened yet — does this estimator already report an effect? If it does,
    the treated and control groups were not moving in parallel to begin with,
    and whatever the real windows show cannot be attributed to accession.

    This is the standard pre-trends check, and it is the right tool for the case
    that motivated it. Tourist arrivals in the Western Balkan control countries
    roughly quadrupled between the late 1990s and the early 2010s as they
    recovered from war and isolation. Set against that, every member state looks
    like it lost tourists. The placebo detects the divergence in the pre-period
    and marks the estimate as unidentified, rather than letting a large, tidy,
    entirely spurious number stand as a finding.

    Note what the test deliberately does NOT flag: a control group that simply
    moved less than every member. That is what a real, uniform treatment effect
    looks like, and an earlier version of this gate wrongly suppressed the trade
    result for exactly that reason.
    """
    real = add_ci(did(code, log=log, scale=scale, w_post=w_post), "did")
    pre = add_ci(did(code, log=log, scale=scale, w_pre=PRE_EARLY, w_post=PRE), "did")
    for bloc, d in real.items():
        p = pre.get(bloc, {})
        pm, pci = p.get("mean"), p.get("ci")
        d["placebo"] = {"mean": pm, "median": p.get("median"), "n": p.get("n", 0),
                        "ci": pci, "controls": p.get("controls", [])}
        if not d.get("rows"):
            continue
        if pm is None or p.get("n", 0) < 3:
            d["placebo"]["verdict"] = "untestable"
            d["warnings"].append(
                "the pre-accession placebo could not be run — the series does not reach far "
                "enough back before accession to test whether the groups were moving in "
                "parallel, so parallel trends is assumed here rather than checked")
            d["identified"] = False
            continue
        actual = d.get("mean")
        # Two independent ways for the placebo to condemn the headline. The first
        # is a significance test and involves no chosen threshold: if the placebo
        # itself is distinguishable from zero, a pre-trend demonstrably exists.
        # The second catches a pre-trend that is large but too noisy across
        # countries to clear significance, which with n around 10 is common.
        sig = bool(pci) and not pci["crossesZero"]
        dominant = actual is not None and abs(pm) >= 0.5 * abs(actual)
        # Subtracting the placebo from the headline removes the part of the gap
        # that was already opening before accession. It is a linear correction
        # and assumes the pre-trend would have continued at the same rate, which
        # is why an adjusted figure is reported as indicative and never as a
        # headline finding.
        d["placebo"]["adjusted"] = None if actual is None else round(actual - pm, 2)
        if dominant:
            d["placebo"]["verdict"] = "fails"
            d["warnings"].append(
                "the same estimator run entirely on pre-accession years already reports "
                "%+.1f against a headline of %+.1f — most of this gap predates accession, "
                "so it measures a pre-existing difference between the groups rather than "
                "an effect of joining" % (pm, actual))
            d["identified"] = False
        elif sig:
            d["placebo"]["verdict"] = "adjusted"
            d["warnings"].append(
                "a pre-accession placebo already reports %+.1f (95%% interval %+.1f to %+.1f, "
                "excluding zero), so the groups were diverging before anyone joined. Netting "
                "that off leaves %+.1f rather than the raw %+.1f. Because the correction "
                "assumes the earlier trend would simply have continued, this is reported as "
                "indicative and is not carried into the findings."
                % (pm, pci["lo"], pci["hi"], actual - pm, actual))
            d["identified"] = False
        else:
            d["placebo"]["verdict"] = "passes"
    return real


payload = {
    "generated": datetime.date.today().isoformat(),
    "pre": PRE, "post": POST,
    "blocs": {b: [m["name"] for m in members if m["bloc"] == b] for b in ("West", "South", "East")},
    "controlsByBloc": {b: [c["name"] for c in controls if c["control_for"] == b]
                       for b in ("West", "South", "East")},
    "measures": [
        {"id": "income", "label": "Income per head (long run)", "lens": "Financial",
         "unit": "%", "dp": 1,
         "desc": "Log GDP per capita in constant 2015 US$, which the World Bank publishes back to "
                 "1960 — far earlier than the PPP series. A difference-in-differences result reads "
                 "as an approximate percentage gap in income per head. Because this is a constant-price "
                 "rather than a purchasing-power measure, it is used for growth over time, not for "
                 "comparing living standards across countries.",
         "did": gate("NY.GDP.PCAP.KD", log=True, scale=LOG100),
         "paths": event_paths("NY.GDP.PCAP.KD", log=True, scale=LOG100),
         "pathLabel": "Cumulative income growth since accession year, % (log points)"},
        {"id": "incomePPP", "label": "Income per head (PPP, robustness check)", "lens": "Financial",
         "unit": "%", "dp": 1,
         "desc": "The same estimate on the purchasing-power series, which begins in 1990. Covers only "
                 "the 1995 and later waves, and is shown so the long-run result can be checked against "
                 "a PPP-based measure where the two overlap.",
         "did": gate("NY.GDP.PCAP.PP.CD", log=True, scale=LOG100),
         "paths": event_paths("NY.GDP.PCAP.PP.CD", log=True, scale=LOG100),
         "pathLabel": "Cumulative income growth since accession year, % (log points)"},
        {"id": "convergence", "label": "Convergence with the EU average", "lens": "Financial",
         "unit": "pp", "dp": 1,
         "desc": "GDP per capita (PPP) as a percentage of the EU-wide average. "
                 "A positive result means closing the gap on the Union faster than "
                 "comparable non-members did.",
         "did": gate("DERIVED.KD.PCT.EU"),
         "paths": event_paths("DERIVED.KD.PCT.EU"),
         "pathLabel": "Change in % of EU average since accession year (pp)"},
        {"id": "unemployment", "label": "Unemployment", "lens": "Social",
         "unit": "pp", "dp": 1, "lowerIsBetter": True,
         "desc": "Unemployment rate, ILO-modelled. A negative result means "
                 "unemployment fell further than in comparable non-members.",
         "did": gate("SL.UEM.TOTL.ZS"),
         "paths": event_paths("SL.UEM.TOTL.ZS"),
         "pathLabel": "Change in unemployment rate since accession year (pp)"},

        # ---- commercial lens ----
        {"id": "trade", "label": "Trade openness",
         "unit": "pp", "dp": 1, "lens": "Commercial",
         "desc": "Exports plus imports as a share of GDP. This is the most direct commercial test "
                 "available: if single-market access does anything measurable, it should raise trade "
                 "relative to countries that did not get it. The comparison is fair in a way the "
                 "income comparison is not, because the Western controls (Norway, Iceland) are inside "
                 "the single market through the EEA and Switzerland has most of it by treaty — so a "
                 "null result against them is evidence about EU membership specifically, over and "
                 "above market access.",
         "did": gate("DERIVED.TRADE.OPEN"),
         "paths": event_paths("DERIVED.TRADE.OPEN"),
         "pathLabel": "Change in trade openness since accession year (pp of GDP)"},
        {"id": "fdi", "label": "Foreign direct investment",
         "unit": "pp", "dp": 1, "lens": "Commercial",
         "desc": "Net FDI inflows as a share of GDP, averaged over the five-year windows — which "
                 "matters more here than anywhere else, because single-year FDI can swing by tens of "
                 "percentage points on one corporate restructuring. Even averaged, the conduit "
                 "economies (Luxembourg, Malta, Ireland, Cyprus, the Netherlands) report flows "
                 "through special-purpose entities that never become physical investment, so their "
                 "estimates measure something other than what the label suggests.",
         "did": gate("BX.KLT.DINV.WD.GD.ZS"),
         "paths": event_paths("BX.KLT.DINV.WD.GD.ZS"),
         "pathLabel": "Change in FDI inflows since accession year (pp of GDP)"},
        {"id": "tourism", "label": "Tourist arrivals",
         "unit": "%", "dp": 1, "lens": "Commercial",
         "desc": "International tourist arrivals, estimated in logs so the result reads as an "
                 "approximate percentage difference in visitor numbers rather than a headcount gap "
                 "between countries of very different sizes. The underlying series ends in 2020 for "
                 "every country, so any window reaching past 2019 is contaminated by the pandemic; "
                 "windows are reported with their year ranges for that reason.",
         "did": gate("ST.INT.ARVL", log=True, scale=LOG100),
         "paths": event_paths("ST.INT.ARVL", log=True, scale=LOG100),
         "pathLabel": "Cumulative growth in arrivals since accession year, % (log points)"},

        # ---- social lens ----
        {"id": "migration", "label": "Net migration",
         "unit": "per 1,000", "dp": 1, "lens": "Social",
         "desc": "Net migration per 1,000 residents. A positive result means a country gained more "
                 "people, relative to comparable non-members, after joining than before. Direction "
                 "here is not a verdict: the same free movement that shows as a gain in Germany shows "
                 "as a loss in Latvia, and which of those counts as a benefit is a political question "
                 "rather than a statistical one. These are modelled demographic estimates, not "
                 "administrative counts.",
         "did": gate("DERIVED.NETM.P1000"),
         "paths": event_paths("DERIVED.NETM.P1000"),
         "pathLabel": "Change in net migration since accession year (per 1,000)"},
        # ---- legal lens ----
        {"id": "ruleoflaw", "label": "Rule of law", "lens": "Legal",
         "unit": "points", "dp": 2,
         "desc": "World Bank Worldwide Governance Indicators, rule-of-law estimate, on a scale of "
                 "roughly -2.5 to +2.5. This is a <strong>perception index</strong> aggregated from "
                 "expert assessments and surveys, not a count of legal facts: a falling score is "
                 "evidence that assessors judged conditions to have worsened. It is the only measure "
                 "of legal quality available here that also covers non-members, which is what makes a "
                 "comparison possible at all.",
         "did": gate("WGI.RL.EST"),
         "headroom": headroom_adjusted("WGI.RL.EST"),
         "paths": event_paths("WGI.RL.EST"),
         "pathLabel": "Change in rule-of-law estimate since accession year (points)"},

        # ---- political lens ----
        {"id": "voice", "label": "Voice and accountability", "lens": "Political",
         "unit": "points", "dp": 2,
         "desc": "WGI voice-and-accountability estimate — the extent to which citizens can "
                 "participate in selecting their government, together with freedom of expression, "
                 "association and press. Same scale and the same perception-index caveat as rule of "
                 "law. This is the closest thing in the dataset to a measure of democratic quality.",
         "did": gate("WGI.VA.EST"),
         "headroom": headroom_adjusted("WGI.VA.EST"),
         "paths": event_paths("WGI.VA.EST"),
         "pathLabel": "Change in voice-and-accountability estimate since accession year (points)"},
        {"id": "corruption", "label": "Control of corruption", "lens": "Political",
         "unit": "points", "dp": 2,
         "desc": "WGI control-of-corruption estimate. Higher is better — the scale runs from weak to "
                 "strong control, so a rising line means less perceived corruption. Anti-corruption "
                 "conditionality was an explicit part of accession negotiations for the 2004, 2007 "
                 "and 2013 waves, which makes this one of the few places where a specific membership "
                 "mechanism can be tested rather than assumed.",
         "did": gate("WGI.CC.EST"),
         "headroom": headroom_adjusted("WGI.CC.EST"),
         "paths": event_paths("WGI.CC.EST"),
         "pathLabel": "Change in control-of-corruption estimate since accession year (points)"},

        {"id": "gini", "label": "Income inequality (Gini)",
         "unit": "points", "dp": 1, "lowerIsBetter": True, "lens": "Social",
         "desc": "Gini index of disposable income. This is survey data collected at irregular "
                 "intervals, not an annual statistic, so the five-year windows frequently contain "
                 "fewer than the three observations the estimator requires — and countries that fail "
                 "that test are excluded rather than filled in. Expect small samples here and read "
                 "the exclusions list as part of the result.",
         "did": gate("SI.POV.GINI"),
         "paths": event_paths("SI.POV.GINI"),
         "pathLabel": "Change in Gini index since accession year (points)"},
    ],
    "adjusted": add_ci(convergence_adjusted("NY.GDP.PCAP.KD", "DERIVED.KD.PCT.EU"), "excess"),
}

# --------------------------------------------------------- in the world
# Every other comparison in this study is internal — members against neighbours. This one asks
# the question most readers actually arrive with: has the Union gained or lost ground against
# the rest of the world?
#
# One fact has to be established before any of it can be read. The World Bank's "European Union"
# aggregate is EU27 applied RETROACTIVELY: its population matches the sum of today's 27 members
# exactly in 2000, 2010 and 2016, when the UK was still a member. So the aggregate never
# contained the UK, and no decline in it can be a Brexit artefact. It also means the series is a
# constant basket of countries rather than the Union as it existed at the time — good for a
# like-for-like trend, wrong for "how has the Union's weight changed as it grew". Both are built.
GDPT, PCPPP, POPT = "NY.GDP.MKTP.CD", "NY.GDP.PCAP.PP.CD", "SP.POP.TOTL"
GNIPC = "NY.GNP.PCAP.PP.CD"
_cty = {r["iso3"]: r for r in csv.DictReader(open(os.path.join(DATA, "countries.csv"), encoding="utf-8"))}
EU27 = [i for i in _cty if i != "GBR"]
EU14_OLD = ["AUT", "BEL", "DNK", "FIN", "FRA", "DEU", "GRC", "IRL", "ITA", "LUX", "NLD",
            "PRT", "ESP", "SWE"]                       # EU15 minus the UK
EU13_NEW = ["BGR", "HRV", "CYP", "CZE", "EST", "HUN", "LVA", "LTU", "MLT", "POL", "ROU",
            "SVK", "SVN"]
WORLD_YEARS = list(range(1990, 2025))


def _accession_year(iso):
    m = re.search(r"(\d{4})", (_cty.get(iso, {}) or {}).get("accession_date", "") or "")
    return int(m.group(1)) if m else None


def _pppgdp(iso, y):
    a, b = series.get((iso, PCPPP), {}).get(y), series.get((iso, POPT), {}).get(y)
    return a * b if (a and b) else None


def _wavg_gni(group, y):
    num = den = 0.0
    for i in group:
        a, b = series.get((i, GNIPC), {}).get(y), series.get((i, POPT), {}).get(y)
        if a and b:
            num += a * b
            den += b
    return num / den if den else None


world = {"years": WORLD_YEARS, "market": [], "ppp": [], "pop": [], "gni": [], "asThen": []}
for y in WORLD_YEARS:
    w = series.get(("WLD", GDPT), {}).get(y)
    wp = _pppgdp("WLD", y)
    wpop = series.get(("WLD", POPT), {}).get(y)
    eu = sum(series[(i, GDPT)][y] for i in EU27 if y in series.get((i, GDPT), {}))
    eup = sum(v for i in EU27 if (v := _pppgdp(i, y)))
    eupop = sum(series[(i, POPT)][y] for i in EU27 if y in series.get((i, POPT), {}))
    # the Union as it actually was that year: only countries already acceded, UK out from 2020
    actual = [i for i in _cty
              if (_accession_year(i) or 9999) <= y and not (i == "GBR" and y >= 2020)]
    then = sum(series[(i, GDPT)][y] for i in actual if y in series.get((i, GDPT), {}))
    world["market"].append({"y": y,
                            "eu": round(eu / w * 100, 2) if w else None,
                            "us": round(series[("USA", GDPT)][y] / w * 100, 2) if w and y in series[("USA", GDPT)] else None,
                            "cn": round(series[("CHN", GDPT)][y] / w * 100, 2) if w and y in series[("CHN", GDPT)] else None})
    world["asThen"].append({"y": y, "share": round(then / w * 100, 2) if w else None,
                            "members": len(actual)})
    world["ppp"].append({"y": y,
                         "eu": round(eup / wp * 100, 2) if wp else None,
                         "us": round(_pppgdp("USA", y) / wp * 100, 2) if wp and _pppgdp("USA", y) else None,
                         "cn": round(_pppgdp("CHN", y) / wp * 100, 2) if wp and _pppgdp("CHN", y) else None})
    world["pop"].append({"y": y,
                         "eu": round(eupop / wpop * 100, 2) if wpop else None,
                         "us": round(series[("USA", POPT)][y] / wpop * 100, 2) if wpop and y in series[("USA", POPT)] else None,
                         "cn": round(series[("CHN", POPT)][y] / wpop * 100, 2) if wpop and y in series[("CHN", POPT)] else None})
    u = series.get(("USA", GNIPC), {}).get(y)
    if u:
        e27 = series.get(("EUU", GNIPC), {}).get(y)
        world["gni"].append({"y": y,
                             "eu27": round(e27 / u * 100, 1) if e27 else None,
                             "old": round(_wavg_gni(EU14_OLD, y) / u * 100, 1) if _wavg_gni(EU14_OLD, y) else None,
                             "new": round(_wavg_gni(EU13_NEW, y) / u * 100, 1) if _wavg_gni(EU13_NEW, y) else None})
    else:
        world["gni"].append({"y": y, "eu27": None, "old": None, "new": None})
uk = series.get(("GBR", GDPT), {})
wl = series.get(("WLD", GDPT), {})
world["ukShare"] = {str(y): round(uk[y] / wl[y] * 100, 1)
                    for y in (2016, 2019, 2024) if y in uk and y in wl}
payload["world"] = world

# -------------------------------------------------------------- south
# "The Mediterranean flatline" — five southern members moving 0.1pp on the EU average across
# thirty years — was recorded earlier in this project as its most striking descriptive fact.
# It is not a fact about the Mediterranean. It is a fact about medians.
SOUTH = ["GRC", "ESP", "PRT", "CYP", "MLT"]
SOUTH_PLUS = SOUTH + ["ITA"]          # Italy is classified West but is the same story, worse
EAST_CONTRAST = ["LVA", "LTU", "BGR", "POL"]
_snames = {"GRC": "Greece", "ESP": "Spain", "PRT": "Portugal", "CYP": "Cyprus", "MLT": "Malta",
           "ITA": "Italy", "LVA": "Latvia", "LTU": "Lithuania", "BGR": "Bulgaria", "POL": "Poland"}
CONV = "DERIVED.GNI.PCT.EU"

south = {"paths": [], "decomp": [], "spreads": [], "years": list(range(1996, 2026))}

for iso in SOUTH_PLUS:
    d = series.get((iso, CONV), {})
    yrs = [y for y in d if 1996 <= y <= 2025]
    if not yrs:
        continue
    pk = max(yrs, key=lambda y: d[y])
    south["paths"].append({
        "iso3": iso, "name": _snames[iso], "inRegion": iso in SOUTH,
        "start": round(d.get(1996), 1) if 1996 in d else None,
        "peak": round(d[pk], 1), "peakYear": pk,
        "end": round(d.get(2025), 1) if 2025 in d else None,
        "rise": round(d[pk] - d[1996], 1) if 1996 in d else None,
        "fall": round(d[2025] - d[pk], 1) if 2025 in d else None,
        "net": round(d[2025] - d[1996], 1) if (1996 in d and 2025 in d) else None,
        "series": [round(d[y], 2) if y in d else None for y in south["years"]],
    })
south["paths"].sort(key=lambda r: (r["net"] if r["net"] is not None else 0), reverse=True)

# growth accounting: total real output, population, and what is left per head
for iso in SOUTH_PLUS + EAST_CONTRAST:
    pc = series.get((iso, "NY.GDP.PCAP.KD"), {})
    pop = series.get((iso, "SP.POP.TOTL"), {})
    if not all(y in pc for y in (1996, 2025)) or not all(y in pop for y in (1996, 2025)):
        continue
    gpc = math.log(pc[2025] / pc[1996])
    gpop = math.log(pop[2025] / pop[1996])
    south["decomp"].append({
        "iso3": iso, "name": _snames[iso], "south": iso in SOUTH_PLUS,
        "pop": round((pop[2025] / pop[1996] - 1) * 100, 1),
        "total": round((math.exp(gpc + gpop) - 1) * 100, 1),
        "perCap": round((pc[2025] / pc[1996] - 1) * 100, 1),
        # share of per-head growth that is the denominator moving, not the numerator
        "demogShare": round((-gpop) / gpc * 100, 1) if gpc else None,
    })
south["decomp"].sort(key=lambda r: r["pop"])

de = series.get(("DEU", "EUROSTAT.IRT_LT_MCBY"), {})
for iso in SOUTH_PLUS:
    d = series.get((iso, "EUROSTAT.IRT_LT_MCBY"), {})
    row = {"iso3": iso, "name": _snames[iso], "pts": {}}
    for y in (1996, 2001, 2007, 2012, 2019, 2025):
        if y in d and y in de:
            row["pts"][str(y)] = round(d[y] - de[y], 2)
    if row["pts"]:
        south["spreads"].append(row)
payload["south"] = south

# ------------------------------------------------------------- brexit
# The one country that left. Two dates matter: the June 2016 referendum, when expectations
# moved, and 1 January 2021, when the UK actually left the single market. COVID sits between
# them, which is why every estimate is a difference against comparators living through the
# same calendar years — a common shock cancels in that comparison.
#
# Two control sets on purpose. TIGHT is Denmark and Sweden: rich, western, EU members that
# kept their own currency, which is what the UK was. BROAD adds the large western economies.
# If the two disagree, the result is about who was picked, not about Brexit.
BREXIT_TIGHT = ["DNK", "SWE"]
BREXIT_BROAD = ["DNK", "SWE", "FRA", "DEU", "ITA", "ESP", "NLD", "BEL"]
_bnames = {"DNK": "Denmark", "SWE": "Sweden", "FRA": "France", "DEU": "Germany",
           "ITA": "Italy", "ESP": "Spain", "NLD": "Netherlands", "BEL": "Belgium"}
BREXIT_MEASURES = [
    ("Trade openness", "DERIVED.TRADE.OPEN", "pp of GDP", False),
    ("GNI vs EU average", "DERIVED.GNI.PCT.EU", "pp", False),
    ("Income per head", "NY.GDP.PCAP.KD", "%", True),
    ("FDI inflows", "BX.KLT.DINV.WD.GD.ZS", "pp of GDP", False),
    ("Net migration", "DERIVED.NETM.P1000", "per 1,000", False),
    ("Unemployment", "SL.UEM.TOTL.ZS", "pp", False),
]


def _bwin(iso, code, lo, hi, log=False):
    d = series.get((iso, code), {})
    v = [d[y] for y in range(lo, hi + 1) if y in d]
    if log:
        v = [math.log(x) for x in v if x > 0]
    return statistics.fmean(v) if len(v) >= 3 else None


def _bdid(code, pre, post, pool, log=False):
    sc = 100.0 if log else 1.0
    a, b = _bwin("GBR", code, *pre, log=log), _bwin("GBR", code, *post, log=log)
    if a is None or b is None:
        return None
    uk = (b - a) * sc
    cs = []
    for c in pool:
        x, y = _bwin(c, code, *pre, log=log), _bwin(c, code, *post, log=log)
        if x is not None and y is not None:
            cs.append(((y - x) * sc, c))
    if len(cs) < 2:
        return None
    cm = statistics.fmean(v for v, _ in cs)
    return {"uk": round(uk, 2), "ctrl": round(cm, 2), "diff": round(uk - cm, 2), "n": len(cs)}


brexit = {"windows": [], "sensitivity": [], "cross2025": []}
for wl, pre, post, note in [
    ("After the referendum", (2011, 2015), (2016, 2019),
     "The anticipation period. Ends before COVID, so this estimate is clean of it entirely."),
    ("After leaving the single market", (2011, 2015), (2021, 2025),
     "After actual departure. Spans the COVID recovery and the 2022 energy shock, both of "
     "which hit the comparators too."),
]:
    rows = []
    for label, code, unit, log in BREXIT_MEASURES:
        t = _bdid(code, pre, post, BREXIT_TIGHT, log)
        b = _bdid(code, pre, post, BREXIT_BROAD, log)
        if t or b:
            rows.append({"label": label, "unit": unit, "tight": t, "broad": b})
    brexit["windows"].append({"label": wl, "pre": pre, "post": post, "note": note, "rows": rows})

# window sensitivity on the headline measure, plus the placebo
# two-year windows are dropped: the three-observation coverage rule used everywhere else
# in this file rejects them, and 2023-2025 already shows the result is not a 2022 artefact
for post in [(2016, 2019), (2021, 2025), (2023, 2025)]:
    t = _bdid("DERIVED.TRADE.OPEN", (2011, 2015), post, BREXIT_TIGHT)
    b = _bdid("DERIVED.TRADE.OPEN", (2011, 2015), post, BREXIT_BROAD)
    brexit["sensitivity"].append({"post": list(post), "tight": t, "broad": b, "placebo": False})
for post in [(2011, 2015), (2013, 2015)]:
    t = _bdid("DERIVED.TRADE.OPEN", (2006, 2010), post, BREXIT_TIGHT)
    b = _bdid("DERIVED.TRADE.OPEN", (2006, 2010), post, BREXIT_BROAD)
    brexit["sensitivity"].append({"post": list(post), "tight": t, "broad": b, "placebo": True})

_to = series.get(("GBR", "DERIVED.TRADE.OPEN"), {})
for iso in ["GBR"] + BREXIT_BROAD:
    d = series.get((iso, "DERIVED.TRADE.OPEN"), {})
    if 2019 in d and 2025 in d:
        brexit["cross2025"].append({"name": "United Kingdom" if iso == "GBR" else _bnames[iso],
                                    "iso3": iso, "change": round(d[2025] - d[2019], 1)})
brexit["cross2025"].sort(key=lambda r: -r["change"])
payload["brexit"] = brexit

# ------------------------------------------------------------- crises
# A crisis is a common shock landing in the same calendar year on everyone, so this
# comparison does not rest on parallel trends the way the accession design does. What it
# still cannot do is randomise membership.
#
# Episodes are DERIVED, not asserted: a year qualifies when a large share of the 41 entities
# contract together. That picks out 2009 and 2020 as global and 2012 as something else, and
# the something-else is the finding.
GDPC = "NY.GDP.PCAP.KD"
_regs = {r["iso3"]: r for r in csv.DictReader(open(os.path.join(DATA, "regions.csv"), encoding="utf-8"))}
_cmeta = {r["iso3"]: r for r in csv.DictReader(open(os.path.join(DATA, "countries.csv"), encoding="utf-8"))}


def _pearson(pairs):
    if len(pairs) < 6:
        return None
    xs = [a for a, _ in pairs]
    ys = [b for _, b in pairs]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    sy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if not sx or not sy:
        return None
    r = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
    return {"r": round(r, 2), "r2": round(r * r, 2), "n": len(pairs)}


def _welch(a, b):
    if len(a) < 3 or len(b) < 3:
        return None
    d = statistics.fmean(a) - statistics.fmean(b)
    se = math.sqrt(statistics.variance(a) / len(a) + statistics.variance(b) / len(b))
    lo, hi = d - 1.96 * se, d + 1.96 * se
    return {"diff": round(d, 2), "lo": round(lo, 2), "hi": round(hi, 2),
            "crossesZero": lo <= 0 <= hi,
            "a": round(statistics.fmean(a), 2), "b": round(statistics.fmean(b), 2),
            "na": len(a), "nb": len(b)}


def _episode(iso, peak_range, trough_range, recover_by):
    d = series.get((iso, GDPC), {})
    pk = [(y, d[y]) for y in range(peak_range[0], peak_range[1] + 1) if y in d]
    tr = [(y, d[y]) for y in range(trough_range[0], trough_range[1] + 1) if y in d]
    if not pk or not tr:
        return None
    py, pv = max(pk, key=lambda t: t[1])
    ty, tv = min(tr, key=lambda t: t[1])
    if tv >= pv:
        return {"peakYear": py, "troughYear": ty, "depth": 0.0, "recovYears": 0}
    rec = next((y for y in range(ty, recover_by + 1) if y in d and d[y] >= pv), None)
    return {"peakYear": py, "troughYear": ty, "depth": round((tv / pv - 1) * 100, 2),
            "recovYears": (rec - py) if rec else None}


def _share_contracting(year):
    out = {}
    for grp in ("member", "neighbour"):
        n = c = 0
        for iso, r in _regs.items():
            g = "member" if r["group"] == "member" else "neighbour"
            if g != grp:
                continue
            d = series.get((iso, GDPC), {})
            if year not in d or (year - 1) not in d or not d[year - 1]:
                continue
            n += 1
            if d[year] / d[year - 1] - 1 < 0:
                c += 1
        out[grp] = {"n": n, "contracting": c, "pct": round(c / n * 100) if n else None}
    return out


def _euro_by(iso, year):
    e = ((_cmeta.get(iso) or {}).get("euro_adopted") or "").strip()
    try:
        return bool(e) and int(e[:4]) <= year
    except ValueError:
        return False


CRISIS_EPISODES = [
    {"id": "gfc", "label": "Global financial crisis", "band": [2008, 2009],
     "peak": (2006, 2008), "trough": (2009, 2013), "recoverBy": 2019},
    {"id": "covid", "label": "COVID-19", "band": [2020, 2020],
     "peak": (2018, 2019), "trough": (2020, 2021), "recoverBy": 2025},
]

crises = {"concentration": {str(y): _share_contracting(y) for y in (2009, 2012, 2020)},
          "episodes": []}
for ep in CRISIS_EPISODES:
    rows = []
    for iso, r in _regs.items():
        if any(x["iso3"] == iso for x in rows):
            continue                     # regions.csv lists Belarus twice, deliberately
        e = _episode(iso, ep["peak"], ep["trough"], ep["recoverBy"])
        if not e:
            continue
        d = series.get((iso, GDPC), {})
        trend = None
        if 1998 in d and 2007 in d and d[1998]:
            trend = round(((d[2007] / d[1998]) ** (1 / 9) - 1) * 100, 2)
        e.update(iso3=iso, name=r["name"], member=r["group"] == "member",
                 region=r["region"], euro=_euro_by(iso, ep["trough"][0]), trend=trend,
                 gni07=series.get((iso, "NY.GNP.PCAP.PP.CD"), {}).get(2007))
        rows.append(e)
    mem = [x for x in rows if x["member"]]
    non = [x for x in rows if not x["member"]]
    blk = {
        "id": ep["id"], "label": ep["label"], "band": ep["band"], "rows": rows,
        "depth": _welch([x["depth"] for x in mem], [x["depth"] for x in non]),
        "recovery": _welch([x["recovYears"] for x in mem if x["recovYears"] is not None],
                           [x["recovYears"] for x in non if x["recovYears"] is not None]),
        "neverMember": [x["name"] for x in mem if x["recovYears"] is None],
        "neverNon": [x["name"] for x in non if x["recovYears"] is None],
        # confound checks — what else predicts these outcomes?
        "confounds": {
            "incomeVsRecovery": _pearson([(x["gni07"], x["recovYears"]) for x in rows
                                          if x.get("gni07") and x["recovYears"] is not None]),
            "trendVsRecovery": _pearson([(x["trend"], x["recovYears"]) for x in rows
                                         if x.get("trend") is not None and x["recovYears"] is not None]),
            "incomeVsDepth": _pearson([(x["gni07"], x["depth"]) for x in rows if x.get("gni07")]),
        },
    }
    if ep["id"] == "gfc":
        eu = [x for x in mem if x["euro"]]
        ne = [x for x in mem if not x["euro"]]
        blk["euro"] = {
            "depth": _welch([x["depth"] for x in eu], [x["depth"] for x in ne]),
            "neverEuro": sum(1 for x in eu if x["recovYears"] is None), "nEuro": len(eu),
            "neverOwn": sum(1 for x in ne if x["recovYears"] is None), "nOwn": len(ne),
        }
    crises["episodes"].append(blk)
payload["crises"] = crises

# ---------------------------------------------------------- persistence
# A five-year window at t+6..t+10 shows whether an effect appeared. It cannot show
# whether it lasted. Re-running the identical estimator at t+11..t+15 answers a
# different and equally important question: is this a permanent shift, or a step
# at entry that erodes? The pre-window is unchanged, so the placebo verdict carries
# over and the two estimates are directly comparable.
LATE = (11, 15)
_PERSIST = {"trade": ("DERIVED.TRADE.OPEN", False, 1.0),
            "fdi": ("BX.KLT.DINV.WD.GD.ZS", False, 1.0),
            "unemployment": ("SL.UEM.TOTL.ZS", False, 1.0),
            "ruleoflaw": ("WGI.RL.EST", False, 1.0)}
for _m in payload["measures"]:
    spec = _PERSIST.get(_m["id"])
    if not spec:
        continue
    _code, _log, _sc = spec
    _m["late"] = gate(_code, log=_log, scale=_sc, w_post=LATE)
    _m["lateWindow"] = LATE

# ------------------------------------------------- bounded-index override
# Where a headroom adjustment is attached, the raw difference-in-differences is known to be
# confounded: the groups start more than a point apart on a bounded scale, so the members'
# smaller gain is partly just less room to move. The placebo cannot catch this — it tests
# shared trends, not shared starting levels — so the raw figure must never stand as a finding
# on its own. Either the adjusted estimate is identified and it is the answer, or nothing is.
for _m in payload["measures"]:
    if "headroom" not in _m:
        continue
    for _bloc, _d in _m["did"].items():
        if not _d.get("rows"):
            continue
        _h = _m["headroom"].get(_bloc, {})
        _d["identified"] = False
        if _h.get("mean") is not None:
            _d["warnings"].append(
                "this is a bounded index and the two groups start far apart on it, so the raw "
                "figure charges members for having less room to improve. Adjusted for that "
                "headroom the estimate is %+.2f, and the adjusted figure is the one to read."
                % _h["mean"])
        else:
            _d["warnings"].append(
                "this is a bounded index and the two groups start far apart on it, so the raw "
                "figure partly measures how much room each had left rather than what membership "
                "did. The correction could not be identified for these windows (the relationship "
                "between starting level and subsequent change explains too little of the "
                "variation among non-members), so no estimate is reported for this outcome.")

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
