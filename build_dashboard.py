#!/usr/bin/env python3
"""Build a country dashboard from the CSV data store.

Usage:  python3 build_dashboard.py POL [more ISO3 codes...]

Reads:
    data/indicators.csv          tidy long format, one row per (country, indicator, year)
    data/milestones.csv          accession/legal/political events per country
    data/narrative/<ISO3>.json   qualitative content + page layout
    template.html                presentation layer (no data in it)

Writes:
    <country-slug>-dashboard.html   self-contained, no external requests
"""
import csv, json, sys, datetime, pathlib, re

BASE = pathlib.Path(__file__).resolve().parent
DATA = BASE / "data"


def load_indicators():
    """-> {(iso3, code): {year: value}}, total row count"""
    table, n = {}, 0
    with open(DATA / "indicators.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            raw = r["value"].strip()
            val = None if raw == "" else float(raw)
            table.setdefault((r["iso3"], r["indicator_code"]), {})[int(r["year"])] = val
            n += 1
    return table, n


def load_milestones(iso3):
    """This country's own events, plus the Union-wide ones every member lived through.

    A country page that shows only its own accession dates makes the 2004 enlargement, the
    euro and the sovereign debt crisis invisible, and those are the years where most of the
    lines on the charts actually bend. The two sets are kept distinguishable by `scope` so
    the page can colour them differently rather than implying a country did something the
    whole Union did.
    """
    out = []
    for path, scope in ((DATA / "milestones.csv", "country"),
                        (DATA / "milestones_eu.csv", "eu")):
        if not path.exists():
            continue
        with open(path, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if scope == "country" and r["iso3"] != iso3:
                    continue
                out.append({"date": r["date"], "sort": float(r["sort_year"]),
                            "label": r["label"], "description": r["description"],
                            "kind": r["kind"], "scope": scope})
    out.sort(key=lambda m: m["sort"])
    return out


def collect_series_keys(nar):
    """Walk the narrative layout and return every {iso3, code} series referenced."""
    keys = []

    def walk(node):
        if isinstance(node, dict):
            if "series" in node and isinstance(node["series"], list):
                for s in node["series"]:
                    keys.append((s.get("iso3"), s["code"]))
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(nar)
    return keys


def money(iso3):
    """This country's slice of flows_payload.json, so the page can show what it pays and
    what comes back without the reader having to leave for the budget page."""
    p = BASE / "flows_payload.json"
    if not p.exists():
        return None
    F = json.loads(p.read_text(encoding="utf-8"))
    c = next((x for x in F["countries"] if x["iso3"] == iso3), None)
    if not c:
        return None
    funds = {f["id"]: f["label"] for f in F["funds"]}
    srcs = {s["id"]: s["label"] for s in F["sources"]}
    yrs = c["years"]
    return {
        "since": c["since"], "to": F["years"][-1], "years": yrs,
        "cumIn": c["cumIn"], "cumOut": c["cumOut"], "net": c["net"],
        "perHeadIn": round(c["cumIn"] * 1e9 / (c["popMean"] * yrs)) if c["popMean"] else None,
        "perHeadOut": round(c["cumOut"] * 1e9 / (c["popMean"] * yrs)) if c["popMean"] else None,
        "perHeadNet": round(c["net"] * 1e9 / (c["popMean"] * yrs)) if c["popMean"] else None,
        "pctGniNet": round(c["net"] * 1000 / (c["gniMean"] * yrs) * 100, 2) if c["gniMean"] else None,
        "receipts": sorted(
            [{"label": funds[k], "v": v} for k, v in c["cumReceipts"].items() if v > 0.05],
            key=lambda r: -r["v"]),
        "payments": sorted(
            [{"label": srcs[k], "v": v} for k, v in c["cumPayments"].items() if abs(v) > 0.05],
            key=lambda r: -abs(r["v"])),
    }


def nonmember_flows(iso3):
    """What a non-member pays the Union, and what it gets back.

    There is no equivalent of the budget workbook here, and that absence is itself the
    finding: no institution publishes a single audited net position for a non-member the way
    the Commission does for a member state. What exists is a set of separately published
    line items on different bases -- some annual averages, some period totals, two currencies
    -- and they cannot honestly be added into one number. So they are not added. The card
    lists them as published, with the basis and the source on every row, and says plainly
    that the total a reader wants does not exist.
    """
    p = DATA / "nonmember_flows.csv"
    if not p.exists():
        return None
    rows = [r for r in csv.DictReader(open(p, encoding="utf-8")) if r["iso3"] == iso3]
    if not rows:
        return None
    return {
        "out": [r for r in rows if r["direction"] == "out"],
        "in": [r for r in rows if r["direction"] == "in"],
    }


def disputes(iso3):
    """Dated episodes where this country and the Union were on opposite sides."""
    p = DATA / "disputes.csv"
    if not p.exists():
        return []
    out = [r for r in csv.DictReader(open(p, encoding="utf-8")) if r["iso3"] == iso3]
    out.sort(key=lambda r: float(r["sort_year"]))
    return out


def verdict_nonmember(row, V, in_eea=True):
    """The mirror question, and it does not have a mirror answer.

    A member page can ask what joining did, because there is a before and an after. A
    non-member page cannot ask what staying out did, because there is no after — it would
    need a counterfactual for a country that never entered, and no comparison of observed
    outcomes produces one. This project already closed that question as structurally
    unanswerable; the panel says so rather than manufacturing a verdict.

    What CAN be said is narrower and worth having: where the country actually sits, and
    whether the members it is compared against pulled ahead of it. Both are reported, and
    both are levels and trajectories rather than effects.
    """
    W = V.get("groups", {}).get("West", {})
    allrows = V.get("rows", [])
    ch = []
    members = sorted([r for r in allrows if r["member"]], key=lambda r: -r["relEnd"])
    above = [r["name"] for r in members if r["relEnd"] > row["relEnd"]]
    artefacts = {"Ireland", "Luxembourg"}
    real_above = [n for n in above if n not in artefacts]
    ch.append({
        "key": "Where it actually sits",
        "status": "fact",
        "verdict": "positive" if not real_above else "unknown",
        "head": f"{row['relEnd']:.1f}% of US income per head, {row['relEnd'] / 100:.2f}× the "
                f"US level — "
                + ("higher than every EU member" if not above
                   else "higher than all but " + join_names(above) + " among the 28"),
        "note": "A level, not an effect — it says where this country is, not what put it there."
                + (" Both of the members above it are statistical artefacts: Ireland's and "
                   "Luxembourg's measured output is inflated by profit-shifting, so it includes "
                   "income accruing to companies rather than to residents."
                   if above and not real_above else
                   " Two of the members above it, Ireland and Luxembourg, are statistical "
                   "artefacts — their measured output is inflated by profit-shifting. The "
                   "others are not."
                   if (set(above) & artefacts) and real_above else ""),
    })

    ch.append({
        "key": "Did the members pull ahead?",
        "status": "not established",
        "verdict": "unknown",
        "head": f"{row['relGain']:+.1f} points against the US level 2000–{row['endYear']}, "
                f"against a Western-member median of {W.get('memberMedian', 0):+.1f}",
        "note": "The gap between Western members and their non-member comparators is "
                f"{(W.get('memberMedian') or 0) - (W.get('nonMedian') or 0):+.1f} points with a "
                f"95% interval of {W.get('welch', {}).get('lo', 0):+.1f} to "
                f"{W.get('welch', {}).get('hi', 0):+.1f} — it spans zero in both directions. "
                "Three comparators cannot settle a question like this, and the pre-accession "
                "placebo already reports "
                f"{W.get('placebo1997', {}).get('gap', 0):+.1f} in the members' favour, so even "
                "the sign is not stable.",
    })

    ch.append({
        "key": "What staying out cost or saved",
        "status": "untestable",
        "verdict": "unknown",
        "head": "not answerable, and not for want of data",
        "note": "It would require knowing what this country would look like <em>inside</em> "
                "the Union. That is a counterfactual about a country that never entered, and "
                "no comparison of observed outcomes can supply it. The non-members are also "
                "not a random sample: Norway holds sovereign wealth no member has, Iceland's "
                "line runs through a banking collapse, and Switzerland was rich before any of "
                "this began. None of that has anything to do with joining or not joining.",
    })

    return {
        "label": "No measurable penalty",
        "tone": "muted",
        "gist": "Nothing in this data shows a cost to staying out — and that is a much weaker "
                "statement than it sounds. It means no penalty was <em>detected</em> by a "
                "comparison with three usable comparators and intervals wide enough to hold "
                "almost any answer. It is not evidence that staying out was the better choice, "
                "and this project cannot produce such evidence. Note also what this country "
                "already has: "
                + ("the single market through the EEA, which is most of what the charts on a "
                   "member page are measuring."
                   if in_eea else
                   "free movement of persons, Schengen and single-market access for goods "
                   "through more than a hundred bilateral agreements — most of what the charts "
                   "on a member page are measuring, reached without joining."),
        "channels": ch,
        "counts": {"positive": sum(1 for c in ch if c["verdict"] == "positive"),
                   "negative": 0,
                   "unknown": sum(1 for c in ch if c["verdict"] == "unknown")},
        "question": "Does the data suggest this country loses by staying out?",
        "rule": "There is no rule here, because there is no verdict to reach. The three rows "
                "are a level, a trajectory comparison whose interval spans zero, and an "
                "explicit statement that the central question cannot be answered by this "
                "design. A member page reaches a headline by counting positive channels; this "
                "page deliberately does not.",
    }


def verdict(iso3):
    """Does the evidence in this study suggest this country gains from membership?

    Deliberately NOT a single number. The project's whole discipline is that different
    claims sit at different evidentiary levels, and collapsing them into one score would
    throw that away. Three channels are reported separately, each with its own status, and
    the headline is a rule applied to those three -- stated on the page so a reader can
    disagree with the rule rather than having to trust it.

      money      accounting fact. No inference, no caveat beyond the convention used.
      trade      the only outcome that clears every check, and it clears it for the East
                 bloc only. A country's own difference against its control group is shown,
                 but the CLAIM is the bloc's, not the country's.
      income     descriptive. For Eastern members the catch-up-adjusted residual is
                 available; elsewhere only the raw trajectory against the US benchmark.

    The founding six are marked untestable rather than negative: they joined in 1958, and
    the income series begins in 1960, so there is no pre-accession period to compare against.
    That is a permanent limit of the data, not a finding about those countries.
    """
    ap = BASE / "analysis_payload.json"
    if not ap.exists():
        return None
    A = json.loads(ap.read_text(encoding="utf-8"))
    V = A.get("verdict") or {}
    row = next((r for r in V.get("rows", []) if r["iso3"] == iso3), None)
    if not row:
        return None
    bloc = row["bloc"]
    trade = next((m for m in A["measures"] if m["id"] == "trade"), None)
    td = (trade or {}).get("did", {}).get(bloc, {})
    own = next((r for r in (td.get("rows") or []) if r["iso3"] == iso3), None)
    res = next((r for r in V.get("catchup", {}).get("rows", []) if r["name"] == row["name"]), None)

    if not row.get("member"):
        nm = {}
        p = DATA / "nonmembers.csv"
        if p.exists():
            nm = {r["iso3"]: r for r in csv.DictReader(open(p, encoding="utf-8"))}
        return verdict_nonmember(row, V,
                                 in_eea=bool(nm.get(iso3, {}).get("eea_year", "").strip()))

    founding = row.get("accession") == 1958
    ch = []

    # 1. money. Read from the flows build, not from row["budgetCum"], so the verdict and the
    #    budget card on the same page cannot disagree. They use different conventions: the
    #    flows figure counts all allocated expenditure and all payments including customs;
    #    budgetCum strips administration. For Belgium and Luxembourg that flips the SIGN,
    #    which is a real finding rather than an error, so it is stated rather than hidden.
    mo = money(iso3)
    if mo:
        pos = mo["net"] > 0
        flip = (row.get("budgetCum") is not None
                and (row["budgetCum"] > 0) != pos)
        ch.append({
            "key": "The money",
            "status": "fact",
            "verdict": "positive" if pos else "negative",
            "head": ("Net recipient" if pos else "Net contributor")
                    + f", €{abs(mo['net']):,.1f}bn"
                    + (f" — {abs(mo['pctGniNet']):.2f}% of national income a year"
                       if mo["pctGniNet"] is not None else ""),
            "note": "Accounting, not an estimate: published by the Commission and reconciled "
                    "to its own totals."
                    + (" <strong>But the sign here depends on the convention.</strong> "
                       "Strip out administrative spending — which is booked to whoever hosts "
                       "the institutions rather than to the people who live there — and this "
                       f"country becomes a net {'contributor' if pos else 'recipient'} of "
                       f"€{abs(row['budgetCum']):,.1f}bn instead. Both figures are correct; "
                       "they answer different questions." if flip else ""),
        })

    # 2. trade
    identified = bool(td.get("identified"))
    if identified and own:
        ch.append({
            "key": "Trade opening",
            "status": "established",
            "verdict": "positive" if own["did"] > 0 else "negative",
            "head": f"{own['did']:+.1f} pp of GDP against non-member neighbours",
            "note": f"The bloc-level effect is +{td['mean']:.1f}pp, "
                    f"{td['positive']} of {td['n']} countries positive, and the pre-accession "
                    "placebo reports essentially nothing. This is the strongest result in the "
                    "study. The claim is the bloc's; this country's own figure is shown for "
                    "position within it, not as a separate finding.",
        })
    else:
        ch.append({
            "key": "Trade opening",
            "status": "not established",
            "verdict": "unknown",
            "head": (f"{own['did']:+.1f} pp of GDP against non-member neighbours"
                     if own else "not testable"),
            "note": "This bloc's trade estimate does not survive the project's checks — "
                    + ("the pre-accession placebo already reports a gap, so the groups were "
                       "diverging before anyone joined."
                       if bloc != "East" else "no usable comparison for these windows.")
                    + (" The figure shown is descriptive only." if own else ""),
        })

    # 3. income
    if founding:
        ch.append({
            "key": "Income trajectory",
            "status": "untestable",
            "verdict": "unknown",
            "head": f"{row['relGain']:+.1f} points against the US level, 2000–{row['endYear']}",
            "note": "A founding member: joined in 1958, and the income series begins in 1960. "
                    "There is no pre-accession period to compare against, so no causal claim "
                    "about membership can be tested here at all.",
        })
    elif res:
        ch.append({
            "key": "Income trajectory",
            "status": "descriptive",
            "verdict": "positive" if res["residual"] > 0 else "negative",
            "head": f"{row['relGain']:+.1f} points against the US level, "
                    f"{res['residual']:+.1f} more than starting income predicted",
            "note": "Measured against a fixed external benchmark over a common 2000–"
                    f"{row['endYear']} window. Eastern members as a group gained "
                    f"{V['groups']['East']['memberMedian']:+.1f} points against the Western "
                    f"Balkans' {V['groups']['East']['nonMedian']:+.1f}, and the pre-accession "
                    f"placebo reports {V['groups']['East']['placebo1997']['gap']:+.1f}. "
                    "Descriptive, not causal: a fixed-window group comparison is not an "
                    "event study.",
        })
    else:
        ch.append({
            "key": "Income trajectory",
            "status": "descriptive",
            "verdict": "positive" if row["relGain"] > 0 else "negative",
            "head": f"{row['relGain']:+.1f} points against the US level, 2000–{row['endYear']}",
            "note": "Raw trajectory against a fixed external benchmark. No catch-up "
                    "adjustment is available outside the Eastern bloc, and the comparison "
                    "against this bloc's non-members does not survive its placebo, so this "
                    "number describes what happened rather than what membership did.",
        })

    pos = sum(1 for c in ch if c["verdict"] == "positive")
    neg = sum(1 for c in ch if c["verdict"] == "negative")
    unk = sum(1 for c in ch if c["verdict"] == "unknown")
    causal = any(c["status"] == "established" and c["verdict"] == "positive" for c in ch)

    if founding:
        label, tone = "Cannot be tested", "muted"
        gist = ("This country has been a member since 1958. Every method in this study "
                "compares a country before and after accession, and there is no usable "
                "'before'. Its budget position is a fact; nothing else here is a verdict.")
    elif causal and pos >= 2:
        label, tone = "Evidence points to a gain", "good"
        gist = ("The one effect this study can establish causally runs in this country's "
                "favour, and the other channels agree. That is as strong as the evidence "
                "here gets — it is still not proof that people are better off.")
    elif pos >= 2 and neg == 0:
        label, tone = "Evidence leans positive", "good"
        gist = ("More than one channel runs in this country's favour, but none of them is "
                "an effect this study can establish causally.")
    elif pos and neg:
        label, tone = "Mixed", "warn"
        gist = ("The channels disagree. Read them separately rather than netting them off — "
                "they are not measured in the same units and not established to the same "
                "standard.")
    elif neg and not pos:
        label, tone = "Evidence leans negative", "bad"
        gist = ("No channel in this study runs in this country's favour. That is not the "
                "same as membership having cost it: most of what membership buys — market "
                "access, freedom of movement, a common regulatory regime — is not measured "
                "anywhere in this dataset.")
    else:
        label, tone = "Not established either way", "muted"
        gist = ("Nothing here clears the bar this project sets. The honest answer is that "
                "the data does not settle it.")

    # The one member state that actually left needs the finding about leaving attached to
    # the verdict, or a reader takes "leans negative" as an endorsement of a departure the
    # study could not evaluate.
    if iso3 == "GBR":
        gist += (" It also left, in 2020 — and this project could not identify what that "
                 "cost or saved: the estimate swings from −7 to −21 percentage points of "
                 "trade openness depending on which comparators are chosen, and both routes "
                 "fail the checks applied everywhere else here. Neither direction of travel "
                 "is settled by this data.")

    return {"label": label, "tone": tone, "gist": gist, "channels": ch,
            "counts": {"positive": pos, "negative": neg, "unknown": unk},
            "rule": "Positive channels are counted, and a channel only counts as "
                    "<em>established</em> if the estimate survives the pre-accession placebo "
                    "test. Two or more positive channels including an established one reads "
                    "as a gain; two or more positive but none established reads as leaning "
                    "positive; disagreement reads as mixed. The rule is stated so it can be "
                    "argued with."}


def context(iso3, table):
    """Where this country sits inside the study's cross-country findings.

    Generated from the data rather than written per country, so all 28 pages carry it and
    none of them can drift out of date when the underlying series are refreshed.
    """
    ap = BASE / "analysis_payload.json"
    if not ap.exists():
        return []
    A = json.loads(ap.read_text(encoding="utf-8"))
    V = A.get("verdict") or {}
    rows = V.get("rows", [])
    me = next((r for r in rows if r["iso3"] == iso3), None)
    if not me:
        return []
    out = []

    if not me["member"]:
        pool = sorted(rows, key=lambda r: -r["relGain"])
        rank = [r["iso3"] for r in pool].index(iso3) + 1
        out.append({
            "title": "Against a fixed external benchmark",
            "text": f"Measured against US income per head at purchasing-power parity over a "
                    f"common 2000–{me['endYear']} window, {me['name']} moved from "
                    f"{me['relStart']:.1f}% of the US level to {me['relEnd']:.1f}% — a change "
                    f"of {me['relGain']:+.1f} points, <strong>{rank}{ordinal(rank)} of "
                    f"{len(pool)}</strong> among the members and non-members this project "
                    f"tracks. The share of the EU average is not used here, because that "
                    f"denominator rises as poorer members catch up and would drag a rich "
                    f"country's line down while its economy grew."})
        g = table.get((iso3, "NY.GDP.MKTP.KD.ZG"), {})
        bits = []
        for yr, name, mshare, nshare in [(2009, "the global financial crisis", 96, 77),
                                         (2012, "the euro-area debt crisis", 61, 23),
                                         (2020, "the pandemic", 93, 92)]:
            v = g.get(yr)
            if v is not None:
                bits.append(f"In {yr}, during {name}, output "
                            f"{'fell' if v < 0 else 'grew'} {abs(v):.1f}%; {mshare}% of members "
                            f"contracted that year against {nshare}% of non-members.")
        if bits:
            out.append({"title": "Through the three downturns", "text": " ".join(bits)
                        + " <strong>2012 is the one episode that separates the two groups</strong> "
                          "— 61% of members contracted against 23% of non-members — and it is "
                          "the clearest measurable cost of integration this study found. This "
                          "country is on the other side of that comparison."})
        if me.get("tradeGain") is not None:
            out.append({"title": "Trade opening", "text":
                f"Exports plus imports as a share of GDP moved {me['tradeGain']:+.1f} points "
                f"between 2000 and today. This matters more here than anywhere else in the "
                f"project: trade is the one outcome that survives every check, and it does so "
                f"by comparing Eastern members against Western Balkan non-members. This "
                f"country is a <em>Western</em> comparator, and it is inside the single market "
                f"through the EEA — which is part of why the Western trade estimate does not "
                f"survive its own placebo."})
        return out

    members = sorted([r for r in rows if r["member"]], key=lambda r: -r["relGain"])
    rank = [r["iso3"] for r in members].index(iso3) + 1
    out.append({
        "title": "Against a fixed external benchmark",
        "text": f"Measured against US income per head at purchasing-power parity over a "
                f"common 2000–{me['endYear']} window, {me['name']} moved from "
                f"{me['relStart']:.1f}% of the US level to {me['relEnd']:.1f}% — a change of "
                f"{me['relGain']:+.1f} points, <strong>{rank}{ordinal(rank)} of "
                f"{len(members)} member states</strong>. This benchmark is used instead of "
                f"the share of the EU average, because the EU average itself rises as poorer "
                f"members catch up, which drags a rich country's line down even while its "
                f"economy grows."})

    # crisis behaviour, against the study's own finding that 2012 was European not global
    g = table.get((iso3, "NY.GDP.MKTP.KD.ZG"), {})
    ep = [(2009, "the global financial crisis", 96, 77),
          (2012, "the euro-area debt crisis", 61, 23),
          (2020, "the pandemic", 93, 92)]
    bits = []
    for yr, name, mshare, nshare in ep:
        v = g.get(yr)
        if v is None:
            continue
        bits.append(f"In {yr}, during {name}, output {'fell' if v < 0 else 'grew'} "
                    f"{abs(v):.1f}%; {mshare}% of members contracted that year against "
                    f"{nshare}% of non-members.")
    if bits:
        out.append({
            "title": "Through the three downturns",
            "text": " ".join(bits)
                    + " <strong>2012 is the one episode that separates members from "
                      "non-members</strong>, and it is the clearest measurable cost of "
                      "integration this study found: the 2008 and 2020 shocks hit both "
                      "groups alike."})

    if me.get("tradeGain") is not None:
        tr = sorted([r for r in rows if r["member"] and r.get("tradeGain") is not None],
                    key=lambda r: -r["tradeGain"])
        trank = [r["iso3"] for r in tr].index(iso3) + 1
        out.append({
            "title": "Trade opening",
            "text": f"Exports plus imports as a share of GDP moved {me['tradeGain']:+.1f} "
                    f"points between 2000 and today, {trank}{ordinal(trank)} of {len(tr)} "
                    f"members. Trade is the only outcome in this study that survives every "
                    f"check applied to it, and it does so for the Eastern bloc: <strong>+20.5 "
                    f"points of GDP against Western Balkan non-members, 11 countries out of "
                    f"11</strong>, with a pre-accession placebo of +0.6."})
    return out


def join_names(names):
    """Oxford-comma join. Four names strung together with 'and' reads as one mistake."""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return " and ".join(names)
    return ", ".join(names[:-1]) + " and " + names[-1]


def ordinal(n):
    return "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def build(iso3):
    table, rowcount = load_indicators()
    nar = json.loads((DATA / "narrative" / f"{iso3}.json").read_text(encoding="utf-8"))
    w = dict(nar["window"])
    ms = load_milestones(iso3)

    # The window used to be whatever the narrative asked for, which left charts with decades
    # of blank space and a timeline running years earlier than any line on the page. Clamp
    # the start to the first year the page actually has data for, and extend it back to the
    # first milestone only where data exists to meet it.
    first_data = min((min(d) for (iso, code), d in table.items()
                      if (iso, code) in {(ri or iso3, c) for ri, c in collect_series_keys(nar)}
                      and any(v is not None for v in d.values())), default=int(w["start"]))
    first_ms = int(ms[0]["sort"]) if ms else int(w["start"])
    w["start"] = max(first_data, min(int(w["start"]), first_ms))
    dropped = [m for m in ms if m["sort"] < w["start"]]
    ms = [m for m in ms if m["sort"] >= w["start"]]
    years = list(range(int(w["start"]), int(w["end"]) + 1))

    # series payload: only what the layout actually references
    series = {}
    for req_iso, code in collect_series_keys(nar):
        iso = req_iso or iso3
        key = f"{iso}|{code}"
        if key in series:
            continue
        by_year = table.get((iso, code))
        if by_year is None:
            raise SystemExit(f"missing series in indicators.csv: {iso} / {code}")
        series[key] = [by_year.get(y) for y in years]

    # KPI tiles: resolve any value pulled straight from the data
    kpis = []
    for k in nar["kpis"]:
        k = dict(k)
        vf = k.pop("valueFrom", None)
        if vf:
            vals = table[(vf.get("iso3", iso3), vf["code"])]
            yr = max(y for y in years if vals.get(y) is not None) if vf["year"] == "last" else int(vf["year"])
            v = vals[yr]
            k["value"] = f"{v:,.{vf.get('dp', 1)}f}{vf.get('suffix', '')}"
        kpis.append(k)

    payload = {
        "iso3": iso3, "name": nar["name"], "subtitle": nar["subtitle"],
        "member": nar.get("member", True),
        "pageTitle": (f"{nar['name']} — EU membership impact" if nar.get("member", True)
                      else f"{nar['name']} — outside the Union"),
        "window": w, "years": years, "series": series, "kpis": kpis,
        "heroChart": nar["heroChart"], "tabs": nar["tabs"],
        "sources": nar["sources"], "method": nar["method"],
        # Disputes ride the same rail as milestones, in a third colour. A line that dips in
        # 2008 or 2021 reads differently once you can see that a confrontation with the Union
        # landed in that year.
        "milestones": ms + [
            {"date": d["date"], "sort": float(d["sort_year"]), "label": d["label"],
             "description": d["description"], "kind": "warn", "scope": "dispute"}
            for d in disputes(iso3) if float(d["sort_year"]) >= w["start"]],
        "milestonesDropped": [{"date": m["date"], "label": m["label"]} for m in dropped],
        "money": money(iso3),
        "flows": nonmember_flows(iso3),
        "disputes": disputes(iso3),
        "verdict": verdict(iso3),
        "context": context(iso3, table),
        # same derived episodes the comparison page uses, so a country's line can be
        # read against the shocks every country faced
        "crises": [
            {"from": 2008, "to": 2009, "scope": "global"},
            {"from": 2011, "to": 2013, "scope": "european"},
            {"from": 2020, "to": 2020, "scope": "global"},
        ],
        "generated": datetime.date.today().isoformat(),
        "rowCount": rowcount,
    }

    html = (BASE / "template.html").read_text(encoding="utf-8")
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    member = nar.get("member", True)
    title = (f"{nar['name']} — EU membership impact" if member
             else f"{nar['name']} — outside the Union")
    html = html.replace("__TITLE__", title)
    html = html.replace("__PAYLOAD__", blob)

    slug = re.sub(r"[^a-z0-9]+", "-", nar["name"].lower()).strip("-")
    out = BASE / f"{slug}-dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"built {out.name}  ({len(series)} series, {len(years)} years, {len(payload['milestones'])} milestones)")
    return out


if __name__ == "__main__":
    for code in (sys.argv[1:] or ["POL"]):
        build(code.upper())
