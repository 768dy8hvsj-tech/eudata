#!/usr/bin/env python3
"""Generate a standard data-first narrative/layout JSON for every country in
data/countries.csv that does not already have a hand-written one.

Hand-written files (currently POL.json) are never overwritten — the generator
skips any ISO3 whose narrative file contains "handwritten": true.
"""
import csv, json, os, collections

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
NARR = os.path.join(DATA, "narrative")
os.makedirs(NARR, exist_ok=True)

MONTHS = {m: i + 1 for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June",
     "July", "August", "September", "October", "November", "December"])}


def dec_year(text):
    """'1 May 2004' -> 2004.33 ; '' -> None"""
    if not text or not text.strip():
        return None
    parts = text.strip().split()
    if len(parts) != 3:
        return None
    day, mon, yr = parts
    if mon not in MONTHS:
        return None
    return round(int(yr) + (MONTHS[mon] - 1) / 12 + (int(day) - 1) / 365, 2)


# what data exists, per country
have = collections.defaultdict(set)
for r in csv.DictReader(open(os.path.join(DATA, "indicators.csv"), encoding="utf-8")):
    have[r["iso3"]].add(r["indicator_code"])

milestones = collections.defaultdict(list)
for r in csv.DictReader(open(os.path.join(DATA, "milestones.csv"), encoding="utf-8")):
    milestones[r["iso3"]].append(r)


STANDARD = {
    "NY.GDP.MKTP.KD.ZG", "NY.GDP.MKTP.CD", "NY.GDP.PCAP.PP.CD", "NY.GNP.PCAP.PP.CD",
    "FP.CPI.TOTL.ZG", "SL.UEM.TOTL.ZS", "NE.EXP.GNFS.ZS", "NE.IMP.GNFS.ZS",
    "BX.KLT.DINV.WD.GD.ZS", "ST.INT.ARVL", "SI.POV.GINI", "SM.POP.NETM",
}


def chart(title, sub, series, opts):
    return {"title": title, "sub": sub, "series": series, "opts": opts}


def build(c):
    iso, name = c["iso3"], c["name"]
    hv = have.get(iso, set())
    start = int(c["window_start"])
    acc = dec_year(c["accession_date"])
    neg = dec_year(c["negotiations_opened"])
    founding = acc is not None and acc < start

    window = {"start": start, "end": 2025,
              "negotiationsOpen": neg if neg else start,
              "negotiationsClose": acc if acc else start,
              "accession": acc if (acc and not founding) else None,
              "accessionLabel": "EU entry"}
    if iso == "GBR":
        window["exit"] = 2020.08
        window["exitLabel"] = "Brexit"

    # ---- subtitle ----
    if founding:
        sub = (f"{name} is a founding member — the EEC treaties entered into force on "
               f"1 January 1958, before this data window opens. The whole series is therefore "
               f"post-accession; there is no pre-membership baseline to compare against.")
    elif iso == "GBR":
        sub = (f"The United Kingdom joined the European Communities on 1 January 1973 and left "
               f"the EU on 31 January 2020. The window opens in {start}, two years before accession "
               f"negotiations, and the red marker shows the Brexit referendum year so the "
               f"post-2016 trajectory can be read against it.")
    else:
        sub = (f"Annual view from {start} — two years before accession negotiations opened "
               f"({c['negotiations_opened']}) — through negotiations, entry on {c['accession_date']}, "
               f"and up to today. Shaded band = negotiation period; vertical line = EU entry.")

    # ---- KPI tiles ----
    kpis = []
    if "DERIVED.PPP.PCT.EU" in hv:
        kpis.append({"label": "GDP per capita (PPP), vs EU average",
                     "valueFrom": {"code": "DERIVED.PPP.PCT.EU", "year": "last", "dp": 0, "suffix": "%"},
                     "delta": "World Bank, latest available year"})
    if "NY.GDP.PCAP.PP.CD" in hv:
        kpis.append({"label": "GDP per capita, PPP",
                     "valueFrom": {"code": "NY.GDP.PCAP.PP.CD", "year": "last", "dp": 0, "prefix": "$"},
                     "delta": "current international $ · World Bank"})
    if "SL.UEM.TOTL.ZS" in hv:
        kpis.append({"label": "Unemployment (ILO)",
                     "valueFrom": {"code": "SL.UEM.TOTL.ZS", "year": "last", "dp": 1, "suffix": "%"},
                     "delta": "% of labour force · World Bank"})
    if "NE.EXP.GNFS.ZS" in hv:
        kpis.append({"label": "Exports, % of GDP",
                     "valueFrom": {"code": "NE.EXP.GNFS.ZS", "year": "last", "dp": 0, "suffix": "%"},
                     "delta": "goods and services · World Bank"})

    hero = chart(
        "Convergence with the EU: GDP per capita (PPP) as % of EU average",
        "Income level relative to the EU-wide average, current international $ at purchasing "
        "power parity. The EU aggregate series begins in 1996, so this chart starts there "
        "regardless of the window above.",
        [{"code": "DERIVED.PPP.PCT.EU", "name": f"{name}, % of EU average"}],
        {"unit": "%", "dp": 1, "area": True}) if "DERIVED.PPP.PCT.EU" in hv else chart(
        "GDP per capita, PPP", "Current international $.",
        [{"code": "NY.GDP.PCAP.PP.CD", "name": name}], {"unit": " $", "dp": 0, "area": True})

    # ---- tabs ----
    fin_row1, fin_row2 = [], []
    if "NY.GDP.MKTP.KD.ZG" in hv:
        fin_row1.append(chart("Real GDP growth, %", "Annual change in real GDP.",
                              [{"code": "NY.GDP.MKTP.KD.ZG", "name": "Real GDP growth"}],
                              {"unit": "%", "dp": 1, "zero": True}))
    if "FP.CPI.TOTL.ZG" in hv:
        fin_row1.append(chart("Inflation (CPI), %", "Annual consumer-price inflation.",
                              [{"code": "FP.CPI.TOTL.ZG", "name": "CPI inflation"}],
                              {"unit": "%", "dp": 1, "zero": True}))
    if "SL.UEM.TOTL.ZS" in hv:
        fin_row2.append(chart("Unemployment, % of labour force", "ILO-modelled estimate.",
                              [{"code": "SL.UEM.TOTL.ZS", "name": "Unemployment"}],
                              {"unit": "%", "dp": 1}))
    if "NY.GDP.PCAP.PP.CD" in hv:
        fin_row2.append(chart("GDP per capita, PPP vs EU average",
                              "Current international $. EU aggregate available from 1996.",
                              [{"iso3": "EUU", "code": "NY.GDP.PCAP.PP.CD", "name": "EU average",
                                "colorVar": "--series-2"},
                               {"code": "NY.GDP.PCAP.PP.CD", "name": name}],
                              {"unit": " $", "dp": 0, "endLabelBelow": 2}))

    fin_row3 = []
    if "EUROSTAT.IRT_LT_MCBY" in hv:
        fin_row3.append(chart("Long-term government bond yield, %",
                              "Eurostat EMU convergence-criterion series: yield on ten-year "
                              "government bonds. What this government pays to borrow.",
                              [{"code": "EUROSTAT.IRT_LT_MCBY", "name": "10-year yield"}],
                              {"unit": "%", "dp": 2}))
    if "EUROSTAT.EARN_NT_NET" in hv:
        fin_row3.append(chart("Net annual earnings, €",
                              "Single person, no children, on 100% of the average wage. "
                              "Eurostat flags 2024 as a break in series.",
                              [{"code": "EUROSTAT.EARN_NT_NET", "name": "Net annual earnings"}],
                              {"unit": " €", "dp": 0}))

    financial = [{"type": "prose", "title": "Financial", "paras": [
        "Charts below are the collected World Bank series for this country across the whole "
        "observation window. Written analysis of what membership did to these numbers is "
        "pending — this page is currently data-first."]}]
    if fin_row1:
        financial.append({"type": "chartRow", "charts": fin_row1})
    if fin_row2:
        financial.append({"type": "chartRow", "charts": fin_row2})
    if fin_row3:
        financial.append({"type": "chartRow", "charts": fin_row3})

    commercial = [{"type": "prose", "title": "Commercial", "paras": [
        "Trade openness, investment and tourism. Written analysis pending."]}]
    if "NE.EXP.GNFS.ZS" in hv and "NE.IMP.GNFS.ZS" in hv:
        commercial.append(chart("Trade in goods &amp; services, % of GDP",
                                "Exports and imports of goods and services.",
                                [{"code": "NE.EXP.GNFS.ZS", "name": "Exports"},
                                 {"code": "NE.IMP.GNFS.ZS", "name": "Imports", "colorVar": "--series-2"}],
                                {"unit": "%", "dp": 1, "endLabelBelow": 2}) | {"type": "chart"})
    crow = []
    if "BX.KLT.DINV.WD.GD.ZS" in hv:
        crow.append(chart("FDI net inflows, % of GDP", "Foreign direct investment, net inflows.",
                          [{"code": "BX.KLT.DINV.WD.GD.ZS", "name": "FDI net inflows"}],
                          {"unit": "%", "dp": 1, "zero": True}))
    if "ST.INT.ARVL" in hv:
        crow.append(chart("International arrivals, millions",
                          "World Bank / UNWTO border arrivals. Series generally ends 2019–2020.",
                          [{"code": "ST.INT.ARVL", "name": "Arrivals"}],
                          {"unit": "m", "dp": 1, "scale": 1e-6}))
    if crow:
        commercial.append({"type": "chartRow", "charts": crow})

    social = [{"type": "prose", "title": "Social", "paras": [
        "Migration and income distribution. Written analysis pending."]}]
    if "SM.POP.NETM" in hv:
        social.append(chart("Net migration, thousands of people",
                            "UN World Population Prospects estimates via World Bank. Blue = net "
                            "inflow, red = net outflow.",
                            [{"code": "SM.POP.NETM", "name": "Net migration"}],
                            {"type": "bar", "unit": "k", "dp": 1, "zero": True, "scale": 1e-3}) | {"type": "chart"})
    srow = []
    if "SI.POV.GINI" in hv:
        srow.append(chart("Income inequality (Gini index)",
                          "World Bank estimate (0 = perfect equality). Survey-based, so points "
                          "are irregular and gaps mean no survey rather than no change.",
                          [{"code": "SI.POV.GINI", "name": "Gini index"}], {"unit": "", "dp": 1}))
    if "DERIVED.NETM.P1000" in hv:
        srow.append(chart("Net migration per 1,000 residents",
                          "The same flow scaled by population, which is the comparable form — the "
                          "chart above is a headcount and so partly tracks country size.",
                          [{"code": "DERIVED.NETM.P1000", "name": "Net migration per 1,000"}],
                          {"unit": "", "dp": 1, "zero": True}))
    if srow:
        social.append({"type": "chartRow", "charts": srow})

    # legal / political prose from verified metadata
    legal_paras = []
    if founding:
        legal_paras.append(
            f"{name} is a founding member. Its legal order has been shaped by Community law from "
            f"the outset rather than adapted to it during an accession process — the Treaty of Rome "
            f"took effect on 1 January 1958.")
    else:
        legal_paras.append(
            f"{name} adopted the acquis communautaire during accession negotiations that opened on "
            f"{c['negotiations_opened']}, and EU law has applied directly since "
            f"{c['accession_date']}.")
    if c["euro_adopted"]:
        legal_paras.append(f"Euro adopted in <strong>{c['euro_adopted']}</strong>, transferring "
                           f"monetary policy to the ECB.")
    else:
        legal_paras.append("Has not adopted the euro; monetary policy remains national.")
    if c["schengen_joined"]:
        legal_paras.append(f"Joined the Schengen area in <strong>{c['schengen_joined']}</strong>.")
    elif c["notes"]:
        legal_paras.append(f"Schengen status: {c['notes']}.")
    legal_paras.append("<em>Detailed legal analysis — acquis chapters, constitutional "
                       "accommodation, infringement and Article 7 history — is pending for this "
                       "country.</em>")

    ref = [m for m in milestones.get(iso, []) if "referendum" in m["label"].lower()]
    pol_kpis = [{"label": m["label"], "value": m["date"], "delta": m["description"]} for m in ref[:3]]
    political = []
    if pol_kpis:
        political.append({"type": "kpis", "items": pol_kpis})
    political.append({"type": "prose", "title": "Political", "paras": [
        f"Verified milestones for {name} are listed on the Overview tab. Written analysis of how "
        f"membership reshaped the domestic political landscape is pending for this country."]})

    # Governance estimates give the legal and political tabs actual measurement rather than
    # metadata alone. The caveat travels with every one of them: these are expert perceptions,
    # on a bounded scale, and small movements are not news.
    WGI_SUB = ("World Bank governance estimate, roughly −2.5 to +2.5. Aggregated from expert "
               "assessments and surveys — perceptions of governance, not a count of legal facts.")
    legal = [{"type": "prose", "title": "Legal", "paras": legal_paras}]
    if "WGI.RL.EST" in hv:
        legal.append(chart("Rule of law", WGI_SUB + " Confidence in and abidance by the rules of "
                           "society: contract enforcement, property rights, police and courts.",
                           [{"code": "WGI.RL.EST", "name": "Rule of law"}],
                           {"unit": "", "dp": 2, "zero": True}) | {"type": "chart"})
    prow = []
    if "WGI.VA.EST" in hv:
        prow.append(chart("Voice and accountability", WGI_SUB + " Participation in selecting "
                          "government, plus freedom of expression, association and the press.",
                          [{"code": "WGI.VA.EST", "name": "Voice and accountability"}],
                          {"unit": "", "dp": 2, "zero": True}))
    if "WGI.CC.EST" in hv:
        prow.append(chart("Control of corruption", WGI_SUB + " Higher is better — a rising line "
                          "means stronger control of corruption, not more of it.",
                          [{"code": "WGI.CC.EST", "name": "Control of corruption"}],
                          {"unit": "", "dp": 2, "zero": True}))
    if prow:
        political.append({"type": "chartRow", "charts": prow})

    return {
        "iso3": iso, "name": name, "handwritten": False,
        "window": window, "subtitle": sub, "kpis": kpis, "heroChart": hero,
        "tabs": {"legal": legal,
                 "financial": financial, "commercial": commercial,
                 "political": political, "social": social},
        "sources": [
            {"label": "Time series", "text": "World Bank Open Data (api.worldbank.org), retrieved "
             "27 Jul 2026. Indicator codes travel with every value in "
             "<code class=\"ind\">data/indicators.csv</code>."},
            {"label": "Milestones", "text": "European Commission, Council of the EU, EUR-Lex, ECB "
             "and national electoral commissions — the source for each row is recorded in "
             "<code class=\"ind\">data/milestones.csv</code>."},
            {"label": "Country metadata", "text": "Accession, euro and Schengen dates in "
             "<code class=\"ind\">data/countries.csv</code>, each verified against a credited source."},
        ],
        "method": [
            {"title": "Window", "text":
                (f"{name} is a founding member, so the −2-years-before-negotiations rule does not "
                 f"apply; the window opens in {start}, the earliest year with broad World Bank "
                 f"coverage." if founding else
                 f"Negotiations opened {c['negotiations_opened']}, so the window starts {start} "
                 f"(−2 years) and runs to the latest available year.")},
            {"title": "Status", "text": "This is a <strong>data-first</strong> page: the series, "
             "milestones and metadata are collected and verified, but the written five-lens "
             "analysis is still pending. Poland is the completed reference page."},
            {"title": "Convergence series", "text": "The EU aggregate used as the comparison "
             "denominator is only available from 1996, so convergence charts start there even "
             "where the country window opens earlier."},
            {"title": "Attribution caution", "text": "The charts show what happened around "
             "membership, not what membership alone caused. Read them as context, not proof."},
        ] + ([{"title": "Incomplete collection", "text":
              "These standard indicators are <strong>not yet collected</strong> for this country "
              "and their charts are absent rather than estimated: "
              + ", ".join(f"<code class=\"ind\">{c}</code>" for c in sorted(STANDARD - hv))
              + ". Every other country in the set carries them, so this page is thinner than the "
                "rest until collection is re-run."}] if (STANDARD - hv) else []),
    }


def build_nonmember(c):
    """A profile page for a country that never joined.

    These are the control group. They carry the same charts as a member page, minus the ones
    that only exist for members (budget flows, Eurostat's euro-convergence bond series), and
    the page is framed round a different question: not what membership did, but what staying
    out looks like next to the countries that went in.

    The accession marker becomes an EEA marker. Both of these countries entered the single
    market on 1 January 1994 without joining the Union, which is the single most important
    fact about reading their lines — most of what the charts here measure is single-market
    integration, and they have that.
    """
    iso, name = c["iso3"], c["name"]
    hv = have.get(iso, set())
    start = int(c["window_start"])
    # Switzerland is the odd one out and the marker has to say so. Norway and Iceland entered
    # the single market through the EEA on 1 January 1994; Switzerland rejected the EEA by
    # referendum six weeks after signing it and reached free movement a decade later through
    # a bilateral treaty instead. Same destination, different vehicle, different date.
    in_eea = bool(c["eea_year"].strip())
    marker = float(c["eea_year"]) if in_eea else 2002.42
    window = {"start": start, "end": 2025,
              "negotiationsOpen": start, "negotiationsClose": start,
              "accession": None, "accessionLabel": "",
              "eea": marker, "eeaLabel": "EEA" if in_eea else "Free movement"}

    sub = (f"{name} is <strong>not an EU member</strong>. It sits in this project as a control "
           f"— one of the comparison countries every estimate is measured against. {c['status']} "
           + ("The vertical line marks entry into the European Economic Area on 1 January 1994: "
              "the single market without the Union."
              if in_eea else
              "The vertical line marks 1 June 2002, when free movement of persons and the "
              "first package of bilateral agreements took effect."))

    kpis = []
    if "DERIVED.GNI.PCT.EU" in hv:
        kpis.append({"label": "GNI per capita (PPP), vs EU average",
                     "valueFrom": {"code": "DERIVED.GNI.PCT.EU", "year": "last", "dp": 0, "suffix": "%"},
                     "delta": "World Bank · not a member, shown against the EU average"})
    if "NY.GNP.PCAP.PP.CD" in hv:
        kpis.append({"label": "GNI per capita, PPP",
                     "valueFrom": {"code": "NY.GNP.PCAP.PP.CD", "year": "last", "dp": 0},
                     "delta": "current international $ · World Bank"})
    if "SL.UEM.TOTL.ZS" in hv:
        kpis.append({"label": "Unemployment (ILO)",
                     "valueFrom": {"code": "SL.UEM.TOTL.ZS", "year": "last", "dp": 1, "suffix": "%"},
                     "delta": "% of labour force · World Bank"})
    if "DERIVED.TRADE.OPEN" in hv:
        kpis.append({"label": "Trade openness",
                     "valueFrom": {"code": "DERIVED.TRADE.OPEN", "year": "last", "dp": 0, "suffix": "%"},
                     "delta": "exports + imports, % of GDP · World Bank"})

    hero = chart(
        "Income relative to the EU average",
        "GNI per capita at purchasing-power parity as a share of the EU-wide average. GNI "
        "rather than GDP, because GDP overstates income in economies where a lot of output "
        "accrues to non-residents. " + (c.get("hero_note") or ""),
        [{"code": "DERIVED.GNI.PCT.EU", "name": f"{name}, % of EU average"}],
        {"unit": "%", "dp": 1, "area": True})

    financial = [{"type": "prose", "title": "Financial", "paras": [
        "The same World Bank series collected for every member state. Two charts that appear "
        "on member pages are absent here and cannot be filled in: EU budget flows, because a "
        "non-member neither pays into the budget nor receives from it, and the Eurostat "
        "long-term bond series, which is a euro-convergence indicator collected for member "
        "states only."]}]
    r1 = []
    if "NY.GDP.MKTP.KD.ZG" in hv:
        r1.append(chart("Real GDP growth, %", "Annual change in real GDP.",
                        [{"code": "NY.GDP.MKTP.KD.ZG", "name": "Real GDP growth"}],
                        {"unit": "%", "dp": 1, "zero": True}))
    if "SL.UEM.TOTL.ZS" in hv:
        r1.append(chart("Unemployment, % of labour force", "ILO-modelled estimate.",
                        [{"code": "SL.UEM.TOTL.ZS", "name": "Unemployment"}], {"unit": "%", "dp": 1}))
    if r1:
        financial.append({"type": "chartRow", "charts": r1})
    r2 = []
    if "NY.GNP.PCAP.PP.CD" in hv:
        r2.append(chart("GNI per capita, PPP vs the EU average",
                        "Current international $. The EU aggregate is available from 1996.",
                        [{"iso3": "EUU", "code": "NY.GNP.PCAP.PP.CD", "name": "EU average",
                          "colorVar": "--series-2"},
                         {"code": "NY.GNP.PCAP.PP.CD", "name": name}],
                        {"unit": " $", "dp": 0, "endLabelBelow": 2}))
    if "DERIVED.KD.PCT.EU" in hv:
        r2.append(chart("Real income per head, % of the EU average",
                        "Constant 2015 US$, so this one is not moved by exchange rates or "
                        "inflation — useful as a cross-check on the headline chart.",
                        [{"code": "DERIVED.KD.PCT.EU", "name": "% of EU average"}],
                        {"unit": "%", "dp": 1}))
    if r2:
        financial.append({"type": "chartRow", "charts": r2})

    commercial = [{"type": "prose", "title": "Commercial", "paras": [
        "Trade openness is the outcome this project can establish causally for EU members, "
        "and it is also the one where the EEA does most of its work: these countries are "
        "inside the single market for goods and services without being inside the Union. "
        "Read these lines as the counterfactual the trade estimate is measured against."]}]
    if "NE.EXP.GNFS.ZS" in hv and "NE.IMP.GNFS.ZS" in hv:
        commercial.append(chart("Trade in goods &amp; services, % of GDP",
                                "Exports and imports of goods and services.",
                                [{"code": "NE.EXP.GNFS.ZS", "name": "Exports"},
                                 {"code": "NE.IMP.GNFS.ZS", "name": "Imports",
                                  "colorVar": "--series-2"}],
                                {"unit": "%", "dp": 1, "endLabelBelow": 2}) | {"type": "chart"})
    crow = []
    if "BX.KLT.DINV.WD.GD.ZS" in hv:
        crow.append(chart("FDI net inflows, % of GDP", "Foreign direct investment, net inflows.",
                          [{"code": "BX.KLT.DINV.WD.GD.ZS", "name": "FDI net inflows"}],
                          {"unit": "%", "dp": 1, "zero": True}))
    if "ST.INT.ARVL" in hv:
        crow.append(chart("International arrivals, millions",
                          "World Bank / UNWTO border arrivals. Series generally ends 2019–2020.",
                          [{"code": "ST.INT.ARVL", "name": "Arrivals"}],
                          {"unit": "m", "dp": 1, "scale": 1e-6}))
    if crow:
        commercial.append({"type": "chartRow", "charts": crow})

    social = [{"type": "prose", "title": "Social", "paras": [
        "Free movement of people applies here through the EEA and Schengen exactly as it does "
        "inside the Union, so the migration series is not measuring a difference in regime."]}]
    if "SM.POP.NETM" in hv:
        social.append(chart("Net migration, thousands of people",
                            "UN World Population Prospects estimates via World Bank. Blue = net "
                            "inflow, red = net outflow.",
                            [{"code": "SM.POP.NETM", "name": "Net migration"}],
                            {"type": "bar", "unit": "k", "dp": 1, "zero": True,
                             "scale": 1e-3}) | {"type": "chart"})
    srow = []
    if "SI.POV.GINI" in hv:
        srow.append(chart("Income inequality (Gini index)",
                          "World Bank estimate (0 = perfect equality). Survey-based, so gaps "
                          "mean no survey rather than no change.",
                          [{"code": "SI.POV.GINI", "name": "Gini index"}], {"unit": "", "dp": 1}))
    if "DERIVED.NETM.P1000" in hv:
        srow.append(chart("Net migration per 1,000 residents",
                          "The same flow scaled by population, which is the comparable form.",
                          [{"code": "DERIVED.NETM.P1000", "name": "Net migration per 1,000"}],
                          {"unit": "", "dp": 1, "zero": True}))
    if srow:
        social.append({"type": "chartRow", "charts": srow})

    if in_eea:
        legal_paras = [
            f"{name} is <strong>not bound by the EU treaties</strong>, and is bound by a great "
            f"deal of EU law anyway. The EEA Agreement, in force since 1 January 1994, extends "
            f"the single market's rules on goods, services, capital and labour — together with "
            f"competition, state aid, consumer protection, employment and environmental law — "
            f"to {name} without giving it a vote on any of them. This is the arrangement "
            f"usually described from inside the Union as rule-taking.",
            "Outside the EEA's reach: the common agricultural and fisheries policies, the "
            "customs union and common external tariff, the common commercial policy, monetary "
            "union, and justice and home affairs beyond what Schengen covers.",
            f"Schengen has applied since <strong>{c['schengen_joined']}</strong>, so border "
            f"checks with the Union are gone even though the border itself is a customs "
            f"border. {name} is a member of EFTA and disputes under the EEA go to the EFTA "
            f"Court rather than the Court of Justice of the EU.",
            "<em>Detailed legal analysis — how much of the acquis actually applies, and how "
            "EEA law is incorporated domestically — is pending.</em>",
        ]
    else:
        legal_paras = [
            f"{name} took the third road. It rejected the EEA by referendum on 6 December 1992 "
            f"— by 50.3%, six weeks after signing the agreement — and then spent thirty years "
            f"building an equivalent relationship one treaty at a time. There are now well over "
            f"a hundred bilateral agreements, and no single framework binding them together.",
            "That is the whole argument. The EU has spent a decade trying to attach an "
            "institutional framework — dynamic adoption of new law, and a role for the Court of "
            "Justice in disputes — to a structure that deliberately has none. Talks on such a "
            "framework collapsed on 26 May 2021. A new package was signed on <strong>2 March "
            "2026</strong> and is not ratified: parliament is still deciding which referendum "
            "threshold applies, and a public vote is not expected before 2028.",
            f"Free movement of persons has applied since <strong>1 June 2002</strong> and "
            f"Schengen since <strong>{c['schengen_joined']}</strong>. There is no customs "
            f"union, no EEA membership and no EFTA Court jurisdiction over the bilateral "
            f"agreements — which is precisely the gap the framework negotiations were about.",
            "<em>Detailed legal analysis of which agreements carry which obligations is "
            "pending.</em>",
        ]
    WGI_SUB = ("World Bank governance estimate, roughly −2.5 to +2.5. Aggregated from expert "
               "assessments and surveys — perceptions of governance, not a count of legal facts.")
    legal = [{"type": "prose", "title": "Legal", "paras": legal_paras}]
    if "WGI.RL.EST" in hv:
        legal.append(chart("Rule of law", WGI_SUB + " Both of these countries sit near the top "
                           "of this scale throughout, which is the headroom problem the "
                           "governance estimates run into everywhere in this project.",
                           [{"code": "WGI.RL.EST", "name": "Rule of law"}],
                           {"unit": "", "dp": 2, "zero": True}) | {"type": "chart"})

    ref = [m for m in milestones.get(iso, []) if "referendum" in m["label"].lower()]
    political = []
    if ref:
        political.append({"type": "kpis", "items": [
            {"label": m["label"], "value": m["date"], "delta": m["description"][:120]}
            for m in ref[:3]]})
    political.append({"type": "prose", "title": "Political", "paras": [
        f"The verified timeline is on the Overview tab. {c['status']}",
        "The political question here is the mirror of the one every member page asks. A member "
        "page asks what joining did. This one asks what staying out did — and that is a "
        "counterfactual about a country that never entered, which no comparison of observed "
        "outcomes can supply. See the panel at the top of the Overview tab."]})
    prow = []
    if "WGI.VA.EST" in hv:
        prow.append(chart("Voice and accountability", WGI_SUB,
                          [{"code": "WGI.VA.EST", "name": "Voice and accountability"}],
                          {"unit": "", "dp": 2, "zero": True}))
    if "WGI.CC.EST" in hv:
        prow.append(chart("Control of corruption", WGI_SUB + " Higher is better.",
                          [{"code": "WGI.CC.EST", "name": "Control of corruption"}],
                          {"unit": "", "dp": 2, "zero": True}))
    if prow:
        political.append({"type": "chartRow", "charts": prow})

    return {
        "iso3": iso, "name": name, "handwritten": False, "member": False,
        "window": window, "subtitle": sub, "kpis": kpis, "heroChart": hero,
        "tabs": {"legal": legal, "financial": financial, "commercial": commercial,
                 "political": political, "social": social},
        "sources": [
            {"label": "Time series", "text": "World Bank Open Data (api.worldbank.org). "
             "Indicator codes travel with every value in "
             "<code class=\"ind\">data/indicators.csv</code>."},
            {"label": "Milestones", "text": "Statistics Norway, the Norwegian Government, the "
             "Council of the EU, the European Commission (DG NEAR), EFTA, Iceland's National "
             "Electoral Commission and RÚV. The source for each row is recorded in "
             "<code class=\"ind\">data/milestones.csv</code>, and where two credited sources "
             "disagree the row says so rather than picking one."},
            {"label": "Relationship metadata", "text": "EEA, Schengen and EFTA status in "
             "<code class=\"ind\">data/nonmembers.csv</code>."},
        ],
        "method": [
            {"title": "Why this page exists", "text":
                f"{name} is one of the non-member countries every estimate in this project is "
                f"measured against. A control group that is never shown is a control group "
                f"nobody can check."},
            {"title": "What is missing, and why", "text":
                "EU budget flows and the Eurostat bond series are absent because they do not "
                "exist for a non-member — not because collection failed. Everything else on a "
                "member page is here."},
            {"title": "The EEA changes what the comparison means", "text":
                "Both non-member profiles in this set are inside the single market through the "
                "EEA. So the contrast with a member state is <em>not</em> integration against "
                "isolation; it is integration without membership against integration with it. "
                "That makes them a demanding control, and it is one reason the trade estimate "
                "for the Western bloc does not survive its checks."},
            {"title": "Attribution caution", "text":
                "Nothing on this page shows what not joining caused. That would need a "
                "counterfactual for a country that never entered, which this design cannot "
                "produce."},
        ],
    }


rows = list(csv.DictReader(open(os.path.join(DATA, "countries.csv"), encoding="utf-8")))
written, skipped, nodata = [], [], []
for c in rows:
    iso = c["iso3"]
    if iso not in have:
        nodata.append(iso)
        continue
    path = os.path.join(NARR, f"{iso}.json")
    if os.path.exists(path):
        try:
            if json.load(open(path, encoding="utf-8")).get("handwritten"):
                skipped.append(iso)
                continue
        except Exception:
            pass
    with open(path, "w", encoding="utf-8") as f:
        json.dump(build(c), f, ensure_ascii=False, indent=1)
    written.append(iso)

nm_path = os.path.join(DATA, "nonmembers.csv")
if os.path.exists(nm_path):
    for c in csv.DictReader(open(nm_path, encoding="utf-8")):
        if c["iso3"] not in have:
            nodata.append(c["iso3"])
            continue
        with open(os.path.join(NARR, f"{c['iso3']}.json"), "w", encoding="utf-8") as f:
            json.dump(build_nonmember(c), f, ensure_ascii=False, indent=1)
        written.append(c["iso3"] + " (non-member)")

print("generated:", " ".join(written))
print("kept hand-written:", " ".join(skipped) or "none")
print("no data yet:", " ".join(nodata) or "none")
