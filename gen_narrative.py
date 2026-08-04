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

print("generated:", " ".join(written))
print("kept hand-written:", " ".join(skipped) or "none")
print("no data yet:", " ".join(nodata) or "none")
