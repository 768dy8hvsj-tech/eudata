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


def window_mean(iso, code, lo, hi, log=False):
    vals = [val(iso, code, y, log) for y in range(lo, hi + 1)]
    vals = [v for v in vals if v is not None]
    # require at least 3 of the 5 years, else the window is not comparable
    return statistics.fmean(vals) if len(vals) >= 3 else None


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

def gate(code, log=False, scale=1.0):
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
    real = add_ci(did(code, log=log, scale=scale), "did")
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
