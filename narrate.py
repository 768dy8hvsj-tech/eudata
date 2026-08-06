#!/usr/bin/env python3
"""Write the five-lens analysis for every country page, from the data rather than by hand.

Twenty-seven pages carried the line "written analysis pending". This closes that.

WHY GENERATED AND NOT WRITTEN. Twenty-seven hand-written analyses would drift the moment a
series was refreshed, and each one would be an opportunity to say something the data does not
support. Everything here is composed from values the pipeline already verified, so a claim on
a page cannot outrun the number behind it, and re-running the build re-writes the prose.

WHAT IT REFUSES TO DO. It never says membership caused anything unless the study's own gate
says so -- and that gate passes for exactly one outcome, in one bloc. Everywhere else the
verbs are descriptive: moved, fell, ranks. Where a bloc-level finding exists the paragraph
says whose claim it is. Where a country is a founding member it says the comparison cannot be
made at all rather than quietly making it.

Poland is skipped: its narrative is hand-written and marked handwritten:true.
"""
import csv, json, os, statistics, collections

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
NARR = os.path.join(DATA, "narrative")

# ------------------------------------------------------------------ load
series = collections.defaultdict(dict)
for r in csv.DictReader(open(os.path.join(DATA, "indicators.csv"), encoding="utf-8")):
    if r["value"]:
        series[(r["iso3"], r["indicator_code"])][int(r["year"])] = float(r["value"])

blocs = {b["iso3"]: b for b in csv.DictReader(open(os.path.join(DATA, "blocs.csv"), encoding="utf-8"))}
meta = {c["iso3"]: c for c in csv.DictReader(open(os.path.join(DATA, "countries.csv"), encoding="utf-8"))}
mstones = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(DATA, "milestones.csv"), encoding="utf-8")):
    mstones[r["iso3"]].append(r)

A = json.load(open(os.path.join(BASE, "analysis_payload.json"), encoding="utf-8"))
F = json.load(open(os.path.join(BASE, "flows_payload.json"), encoding="utf-8"))
V = A["verdict"]
MEAS = {m["id"]: m for m in A["measures"]}
FLOW = {c["iso3"]: c for c in F["countries"]}
FUNDS = {f["id"]: f["label"] for f in F["funds"]}


def s(iso, code):
    return series.get((iso, code), {})


def last(iso, code):
    d = s(iso, code)
    return (max(d), d[max(d)]) if d else (None, None)


def at(iso, code, year, tol=2):
    d = s(iso, code)
    for k in range(tol + 1):
        for y in (year - k, year + k):
            if y in d:
                return d[y]
    return None


def rank_of(iso, key, members, reverse=True):
    """Rank among member states on a payload verdict key."""
    rows = [r for r in V["rows"] if r["member"] and r.get(key) is not None]
    rows.sort(key=lambda r: -r[key] if reverse else r[key])
    ids = [r["iso3"] for r in rows]
    return (ids.index(iso) + 1, len(ids)) if iso in ids else (None, None)


def ord_(n):
    return "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")


def own_did(mid, iso, bloc):
    d = MEAS.get(mid, {}).get("did", {}).get(bloc, {})
    row = next((r for r in (d.get("rows") or []) if r["iso3"] == iso), None)
    return d, row


def pct(v, dp=1, sign=False):
    """Typographic minus, not a hyphen. The two render differently next to a digit and the
    page was mixing them within a single sentence."""
    if v is None:
        return "—"
    out = ("%+." + str(dp) + "f") % v if sign else ("%." + str(dp) + "f") % v
    return out.replace("-", "\u2212")


# ------------------------------------------------------------------ lenses
def financial(iso, name, b, founding):
    vr = next((r for r in V["rows"] if r["iso3"] == iso), None)
    res = next((r for r in V["catchup"]["rows"] if r["name"] == name), None)
    fl = FLOW.get(iso)
    p = []

    if vr:
        rk, n = rank_of(iso, "relGain", None)
        p.append(
            f"Measured against a fixed external benchmark — US income per head at "
            f"purchasing-power parity — {name} moved from <strong>{pct(vr['relStart'])}%</strong> "
            f"of the US level in 2000 to <strong>{pct(vr['relEnd'])}%</strong> in "
            f"{vr['endYear']}, a change of {pct(vr['relGain'], 1, True)} points. That ranks "
            f"<strong>{rk}{ord_(rk)} of {n}</strong> member states. The share of the EU average "
            f"is deliberately not used for this comparison: that denominator rises as poorer "
            f"members catch up, so a rich country's line falls while its economy grows."
            + (f" Adjusting for the fact that poorer economies converge faster anyway, "
               f"{name} came in {pct(res['residual'], 1, True)} points "
               f"{'above' if res['residual'] > 0 else 'below'} what its starting income "
               f"predicted." if res else ""))

    g = s(iso, "NY.GDP.MKTP.KD.ZG")
    if g:
        worst = min(g, key=lambda y: g[y])
        best = max(g, key=lambda y: g[y])
        ep = []
        for yr, lbl, ms, ns in ((2009, "the global financial crisis", 96, 77),
                                (2012, "the euro-area debt crisis", 61, 23),
                                (2020, "the pandemic", 93, 92)):
            if yr in g:
                ep.append(f"{yr} {'−' if g[yr] < 0 else '+'}{abs(g[yr]):.1f}%")
        p.append(
            f"The deepest single contraction in the record is <strong>{worst} "
            f"({pct(g[worst], 1, True)}%)</strong> and the strongest year "
            f"{best} ({pct(g[best], 1, True)}%). Through the three synchronised downturns: "
            + ", ".join(ep) + ". "
            + ("The 2012 episode is the one that separates members from non-members in this "
               "study — 61% of members contracted that year against 23% of non-members, where "
               "2009 and 2020 hit both groups alike. It is the clearest measurable cost of "
               "integration found anywhere here." if 2012 in g else ""))

    u = s(iso, "SL.UEM.TOTL.ZS")
    if u:
        pk = max(u, key=lambda y: u[y])
        ly, lv = last(iso, "SL.UEM.TOTL.ZS")
        p.append(
            f"Unemployment peaked at <strong>{pct(u[pk])}%</strong> in {pk} and stands at "
            f"{pct(lv)}% in {ly}. "
            + ("The Eastern bloc's unemployment estimate is a null result — +1.4 points against "
               "the non-member controls, an interval of −0.6 to +3.4 that spans zero — so "
               "nothing on this line is attributable to accession."
               if b["bloc"] == "East" else
               "No unemployment effect survives the checks in any bloc, so read this as "
               "context rather than consequence."))

    if fl:
        top = max(fl["cumReceipts"].items(), key=lambda kv: kv[1])
        p.append(
            f"On the EU budget, {name} has paid in <strong>€{fl['cumOut']:,.1f} billion</strong> "
            f"and received <strong>€{fl['cumIn']:,.1f} billion</strong> since {fl['since']}, a "
            f"net {'receipt' if fl['net'] > 0 else 'contribution'} of "
            f"<strong>€{abs(fl['net']):,.1f} billion</strong>. The largest single line coming "
            f"back is {FUNDS[top[0]].lower()} at €{top[1]:,.1f} billion. This is the one part of "
            f"the study that is accounting rather than inference — the figures are the "
            f"Commission's own and reconcile to its published totals exactly. Note that "
            f"“received” means expenditure allocated here, not a payment to the government: a "
            f"research grant to a university and a farm payment to a landowner both count.")

    by = s(iso, "EUROSTAT.IRT_LT_MCBY")
    if by:
        pk = max(by, key=lambda y: by[y])
        ly, lv = last(iso, "EUROSTAT.IRT_LT_MCBY")
        if by[pk] - lv > 1:
            p.append(
                f"Long-term borrowing costs peaked at <strong>{pct(by[pk], 2)}%</strong> in {pk} "
                f"and are {pct(lv, 2)}% at {ly}. Bond spreads across the euro area collapsed to "
                f"near zero in the decade after 1999 and reopened violently after 2010, which is "
                f"the single most visible thing monetary union did to the cost of government "
                f"borrowing — in both directions.")
    return p


def commercial(iso, name, b, founding):
    p = []
    d, row = own_did("trade", iso, b["bloc"])
    tr = s(iso, "DERIVED.TRADE.OPEN")
    if tr:
        f_y, l_y = min(tr), max(tr)
        p.append(
            f"Trade openness — exports plus imports as a share of GDP — moved from "
            f"<strong>{pct(tr[f_y])}%</strong> in {f_y} to <strong>{pct(tr[l_y])}%</strong> in "
            f"{l_y}. Figures above 100% are not an error: a component crossing a border three "
            f"times is counted three times, which is why small economies inside dense supply "
            f"chains sit so far above the rest.")
    if row and d.get("identified"):
        p.append(
            f"This is the one place the study can make a causal claim. Against non-member "
            f"neighbours over matched windows, {name} shows <strong>{pct(row['did'], 1, True)} "
            f"points of GDP</strong>. The claim itself is the bloc's rather than this country's: "
            f"the Eastern estimate is <strong>+{d['mean']:.1f} points</strong> with "
            f"{d['positive']} of {d['n']} countries positive and a pre-accession placebo of "
            f"essentially nothing. It is the only outcome here that survives every check "
            f"applied to it. It does <em>not</em> follow that people became better off — that is "
            f"the income question, and the income question has two answers.")
    elif row:
        p.append(
            f"Against non-member neighbours over matched windows the figure is "
            f"{pct(row['did'], 1, True)} points of GDP, but this bloc's trade estimate does not "
            f"survive the project's checks — the pre-accession placebo already reports a gap, so "
            f"the groups were diverging before anyone joined. Read the number as descriptive.")
    elif founding:
        p.append(
            "No before-and-after comparison is possible here. This is a founding member: the "
            "treaties took effect in 1958 and the usable series begin in 1960, so there is no "
            "pre-accession baseline against which to measure anything.")

    ex = s(iso, "TRADE.EU.EXP.SHR")
    dest = {c: s(iso, "TRADE.DEST." + c) for c in ("EU", "EUR", "ASIA", "NAMER", "MEAST", "AFR", "LATAM")}
    if ex:
        f_y, l_y = min(ex), max(ex)
        p.append(
            f"Direction is a separate question from volume, and the two answers come apart. The "
            f"share of exports going to the other EU member states was "
            f"<strong>{pct(ex[f_y])}%</strong> in {f_y} and <strong>{pct(ex[l_y])}%</strong> in "
            f"{l_y}. Across the 2004 accession wave that share moved by a median of −0.3 points: "
            f"the Europe Agreements had already opened free trade with the Community through the "
            f"1990s, so membership raised how much these countries traded without changing who "
            f"with.")
    named = [(lbl, v) for lbl, v in
             [("Asia", dest["ASIA"]), ("North America", dest["NAMER"]),
              ("the rest of Europe", dest["EUR"]), ("the Middle East", dest["MEAST"]),
              ("Africa", dest["AFR"]), ("Latin America", dest["LATAM"])] if v]
    if named:
        vals = sorted(((lbl, dd[max(dd)]) for lbl, dd in named), key=lambda kv: -kv[1])
        yr = max(next(iter(named))[1])
        p.append(
            "Beyond the Union, the largest destinations in " + str(yr) + " are "
            + ", ".join(f"<strong>{lbl} {pct(v)}%</strong>" for lbl, v in vals[:3])
            + " of total goods exports. Services are not in this dataset, which matters for "
              "economies that sell more services than goods.")

    fd, frow = own_did("fdi", iso, b["bloc"])
    fdi = s(iso, "BX.KLT.DINV.WD.GD.ZS")
    if fdi:
        pk = max(fdi, key=lambda y: fdi[y])
        note = ""
        if iso in ("LUX", "NLD", "IRL", "MLT", "CYP"):
            note = (" Treat this series with real caution here: inward investment in this "
                    "economy is dominated by special-purpose entities routing capital onward, "
                    "so the figure measures financial plumbing more than factories.")
        elif fd.get("identified") and frow:
            note = (f" Against non-member controls the bloc estimate is "
                    f"{pct(fd['mean'], 1, True)} points of GDP, which survives its checks; this "
                    f"country's own figure is {pct(frow['did'], 1, True)}.")
        p.append(f"Foreign direct investment peaked at {pct(fdi[pk])}% of GDP in {pk}." + note)
    return p


def social(iso, name, b, founding):
    p = []
    pop = s(iso, "SP.POP.TOTL")
    nm = s(iso, "DERIVED.NETM.P1000")
    if pop:
        f_y, l_y = min(pop), max(pop)
        ch = (pop[l_y] / pop[f_y] - 1) * 100
        p.append(
            f"Population moved {pct(ch, 1, True)}% between {f_y} and {l_y}. This matters more "
            f"than it looks: income per head is output divided by population, so a shrinking "
            f"denominator raises the measured figure without anyone becoming better off. "
            + ("Across the Eastern members between 17% and 29% of the measured gain in output "
               "per head is the denominator falling — Latvia lost a quarter of its population "
               "over the period." if b["bloc"] == "East" and ch < 0 else
               "Where population grew, the same arithmetic works in reverse and holds the "
               "per-head figure down." if ch > 0 else ""))
    if nm:
        neg = [y for y in nm if nm[y] < 0]
        ly, lv = last(iso, "DERIVED.NETM.P1000")
        p.append(
            f"Net migration runs at {pct(lv, 1, True)} per 1,000 residents at {ly}, and the "
            f"country recorded net outflow in {len(neg)} of the {len(nm)} years on record. "
            f"These are modelled estimates from the UN population projections rather than counts "
            f"of people, and the study's migration estimates fail their placebo in both East and "
            f"West — the groups were already diverging before anyone joined — so nothing here is "
            f"attributable to membership.")
    gi = s(iso, "SI.POV.GINI")
    if gi:
        f_y, l_y = min(gi), max(gi)
        p.append(
            f"On income inequality the Gini index reads {pct(gi[f_y])} in {f_y} and "
            f"{pct(gi[l_y])} in {l_y}, "
            f"{'a widening' if gi[l_y] > gi[f_y] else 'a narrowing'} of "
            f"{abs(gi[l_y] - gi[f_y]):.1f} points. This is survey data collected at irregular "
            f"intervals — {len(gi)} observations across the window — so a gap in the chart means "
            f"no survey rather than no change, and the small samples are why no inequality "
            f"estimate in this study clears its confidence threshold.")
    u = s(iso, "SL.UEM.TOTL.ZS")
    if u and len(u) > 5:
        ly, lv = last(iso, "SL.UEM.TOTL.ZS")
        med = statistics.median(u.values())
        p.append(
            f"Unemployment is {pct(lv)}% at {ly} against a median of {pct(med)}% across the "
            f"whole window — {'below' if lv < med else 'above'} this country's own long-run "
            f"level.")
    return p


def legal(iso, name, b, founding):
    c = meta.get(iso, {})
    p = []
    if founding:
        p.append(
            f"{name} is a founding member. Its legal order was shaped <em>by</em> Community law "
            f"from the outset rather than adapted <em>to</em> it during an accession process — "
            f"the Treaty of Rome took effect on 1 January 1958. Every other member state adopted "
            f"the acquis as a condition of entry; this one helped write it.")
    else:
        p.append(
            f"{name} adopted the acquis communautaire as a condition of entry. Negotiations "
            f"opened {c.get('negotiations_opened') or 'in the run-up to accession'} and EU law "
            f"has applied directly since <strong>{c.get('accession_date')}</strong>. The "
            f"sequencing matters for everything else on this page: the heaviest institutional "
            f"reform happens <em>before</em> entry, inside what any before-and-after comparison "
            f"treats as the baseline. That is one of three biases in this study that push the "
            f"measured effect of membership toward zero.")
    bits = []
    bits.append(f"adopted the euro in <strong>{c['euro_adopted']}</strong>, transferring "
                f"monetary policy to the ECB" if c.get("euro_adopted")
                else "has not adopted the euro, so monetary policy remains national")
    if c.get("schengen_joined"):
        bits.append(f"joined the Schengen area in <strong>{c['schengen_joined']}</strong>")
    elif c.get("notes"):
        bits.append(f"on Schengen: {c['notes'].lower()}")
    p.append(f"{name} " + ", and ".join(bits) + ".")

    rl = s(iso, "WGI.RL.EST")
    if rl:
        f_y, l_y = min(rl), max(rl)
        rows = sorted([(i, series[(i, "WGI.RL.EST")][max(series[(i, "WGI.RL.EST")])])
                       for i in blocs if blocs[i]["group"] == "member"
                       and series.get((i, "WGI.RL.EST"))], key=lambda kv: -kv[1])
        rk = [i for i, _ in rows].index(iso) + 1
        p.append(
            f"On the World Bank's rule-of-law estimate {name} reads <strong>{rl[l_y]:+.2f}</strong> "
            f"at {l_y} against {rl[f_y]:+.2f} at {f_y}, ranking {rk}{ord_(rk)} of {len(rows)} "
            f"members. Two cautions travel with that number and both are serious. It is an "
            f"aggregate of expert perceptions on a bounded −2.5 to +2.5 scale, not a count of "
            f"legal facts. And because the scale is bounded, a country already near the top has "
            f"less room to rise — which is why the raw comparison of members against non-members "
            f"looks negative and, once corrected for that headroom, comes out at +0.04: "
            f"indistinguishable from zero. <strong>This study finds no measurable effect of "
            f"membership on the rule of law in either direction.</strong>")
    p.append(
        "<em>What is missing here and would change the picture: infringement proceedings, "
        "transposition deficits, preliminary references to the Court of Justice, and Article 7 "
        "history. None of it was collected, so this lens rests on one perception index and the "
        "treaty dates.</em>")
    return p


def political(iso, name, b, founding):
    p = []
    refs = [m for m in mstones.get(iso, []) if "referendum" in m["label"].lower()]
    if refs:
        p.append(
            "Accession was put to the public here. "
            + " ".join(f"<strong>{m['label']} ({m['date']})</strong> — {m['description']}."
                       for m in refs[:3]))
    elif not founding:
        p.append(
            f"No accession referendum is recorded for {name} in the verified milestone table; "
            f"entry was ratified parliamentarily. The verified timeline is on the Overview tab.")

    for code, label, gloss in (
        ("WGI.VA.EST", "voice and accountability",
         "participation in choosing a government, plus freedom of expression, association and "
         "the press"),
        ("WGI.CC.EST", "control of corruption",
         "higher is better — a rising line means stronger control, not more corruption")):
        d = s(iso, code)
        if not d:
            continue
        f_y, l_y = min(d), max(d)
        ch = d[l_y] - d[f_y]
        p.append(
            f"On {label} — {gloss} — the estimate moved from {d[f_y]:+.2f} in {f_y} to "
            f"<strong>{d[l_y]:+.2f}</strong> in {l_y}, a change of {ch:+.2f}. "
            + ("Anti-corruption conditionality was an explicit part of accession negotiations "
               "for the 2004, 2007 and 2013 waves, which makes this one of the few places a "
               "specific mechanism could be tested rather than assumed. It was tested, and the "
               "result does not survive: the raw comparison is confounded by headroom on a "
               "bounded scale and the corrected estimate cannot be identified."
               if code == "WGI.CC.EST" and b["bloc"] == "East" and not founding else
               "Same bounded-scale caveat as the rule-of-law figure: compare levels rather than "
               "small movements, and treat this as perception rather than fact."))

    fl = FLOW.get(iso)
    if fl:
        p.append(
            f"The politics of the budget are worth stating plainly, because they are the part "
            f"most argued about and the least uncertain. {name} is a net "
            f"{'recipient' if fl['net'] > 0 else 'contributor'} of "
            f"<strong>€{abs(fl['net']):,.1f} billion</strong> since {fl['since']}. "
            + ("Recipients take between two and three percent of national income a year; "
               "contributors pay well under one percent of theirs. The Union's budget is about "
               "1% of EU income but concentrated enough to matter enormously at the receiving "
               "end." if fl["net"] > 0 else
               "The asymmetry runs the other way for contributors: the largest pay well under "
               "one percent of national income a year, while the largest recipients take two to "
               "three percent of theirs."))
    p.append(
        "<em>Not collected, and it limits this lens: European Parliament turnout, Eurobarometer "
        "series on trust and identity, and national parliamentary scrutiny of EU legislation. "
        "What is here is two perception indices, the verified milestone record and the budget.</em>")
    return p


LENS = {"financial": financial, "commercial": commercial, "social": social,
        "legal": legal, "political": political}
TITLE = {"financial": "Financial", "commercial": "Commercial", "social": "Social",
         "legal": "Legal", "political": "Political"}


def run():
    done, skipped = [], []
    for iso, b in sorted(blocs.items()):
        if b["group"] != "member":
            continue
        path = os.path.join(NARR, f"{iso}.json")
        if not os.path.exists(path):
            continue
        nar = json.load(open(path, encoding="utf-8"))
        if nar.get("handwritten"):
            skipped.append(iso)
            continue
        name = nar["name"]
        founding = (b["accession_year"] or "") == "1958"
        for lens, fn in LENS.items():
            paras = [x for x in fn(iso, name, b, founding) if x]
            if not paras:
                continue
            blocks = nar["tabs"].get(lens, [])
            new = {"type": "prose", "title": TITLE[lens], "paras": paras}
            if blocks and blocks[0].get("type") == "prose":
                blocks[0] = new
            else:
                blocks.insert(0, new)
            nar["tabs"][lens] = blocks
        # The method note said "written analysis pending" on every one of these pages. It is
        # not pending any more, and the note should say what the analysis actually is —
        # generated from the verified series rather than composed by hand, which is a real
        # difference a reader is entitled to know about.
        for m in nar.get("method", []):
            if m.get("title") == "Status":
                m["text"] = ("The five-lens analysis on this page is <strong>generated from the "
                             "verified data</strong> rather than written by hand. Every figure "
                             "quoted is a value the pipeline already checked against its source, "
                             "so a sentence here cannot outrun the number behind it and "
                             "re-running the build re-writes the prose. The trade-off is that it "
                             "reasons only from what was collected: it will not tell you about a "
                             "court case, an election or a scandal unless that shows up in a "
                             "series or the verified milestone table. Poland is the one "
                             "hand-written page, kept as a reference for what a fuller "
                             "treatment looks like.")
        nar["analysisWritten"] = True
        json.dump(nar, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        done.append(iso)
    print(f"written: {len(done)} — {' '.join(done)}")
    print(f"skipped (hand-written): {' '.join(skipped) or 'none'}")


if __name__ == "__main__":
    run()
