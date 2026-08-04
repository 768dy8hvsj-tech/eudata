#!/usr/bin/env python3
"""Build index.html — the comparison page, structured by region.

Twenty-eight countries on one chart is noise. Seven regions is a comparison.
Each region tab highlights that region against the other six in grey (the
emphasis pattern) rather than colouring seven series, which is past the point
where colour reliably distinguishes them.

Level measures default to GNI rather than GDP: Luxembourg's and Ireland's GDP
overstates resident income by roughly 47% because of profit-shifting and IP
relocation, which visibly breaks their own regional averages. GNI counts income
accruing to residents and largely removes the distortion. Region aggregates use
the MEDIAN, which is additionally robust to a single extreme member.
"""
import csv, json, os, re, datetime, statistics, collections

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
YEARS = list(range(1990, 2026))

LENSES = [
    {"id": "Financial", "label": "Financial",
     "note": "Income, earnings and the cost of borrowing."},
    {"id": "Commercial", "label": "Commercial",
     "note": "Trade, investment and tourism — the single market's most direct channels."},
    {"id": "Social", "label": "Social",
     "note": "Employment, migration and the distribution of income."},
    {"id": "Legal", "label": "Legal",
     "note": "The quality of the legal order, as assessed by outside experts."},
    {"id": "Political", "label": "Political",
     "note": "Democratic voice and the control of corruption."},
]

WGI_CAVEAT = (
    " <strong>Read this as a perception index, not a count of legal facts</strong> — it is "
    "aggregated from expert assessments and surveys, so a falling line means assessors judged "
    "conditions to have worsened. The scale runs roughly −2.5 to +2.5, and because it is "
    "bounded, a country already near the top has far less room to rise than one near the "
    "bottom. Comparing levels between countries is safer than reading small movements."
)

MEASURES = [
    {"id": "gniconv", "lens": "Financial", "code": "DERIVED.GNI.PCT.EU", "label": "Convergence (GNI vs EU average)",
     "unit": "%", "dp": 1, "suffix": "%", "ref": 100,
     "blurb": "GNI per capita (PPP) as a share of the EU-wide average. 100% is exactly at the EU "
              "average. This is the clearest single measure of whether a region is catching up with "
              "the Union, holding level, or slipping behind — and because the EU average itself rises "
              "as poorer members catch up, a rich region can decline here while still growing."},
    {"id": "gni", "lens": "Financial", "code": "NY.GNP.PCAP.PP.CD", "label": "GNI per capita (PPP)",
     "unit": "$", "dp": 0, "prefix": "$",
     "blurb": "Gross national income per head at purchasing power parity — income accruing to a "
              "country's residents. Preferred here over GDP, which in Luxembourg and Ireland is "
              "inflated roughly 47% by foreign-owned production and relocated intellectual property."},
    {"id": "unemp", "lens": "Social", "code": "SL.UEM.TOTL.ZS", "label": "Unemployment rate",
     "unit": "%", "dp": 1, "suffix": "%", "lowerIsBetter": True,
     "blurb": "Unemployment as a share of the labour force, ILO-modelled estimate. Lower is better."},
    {"id": "bond", "lens": "Financial", "code": "EUROSTAT.IRT_LT_MCBY", "label": "Long-term bond yield",
     "unit": "%", "dp": 2, "suffix": "%", "lowerIsBetter": True,
     "blurb": "Yield on ten-year government bonds — Eurostat's EMU convergence criterion series. "
              "This is what a government pays to borrow, and it is the sharpest market verdict on a "
              "country's credibility. Lower is better. Watch 2010–2012: Greece reaches 22.5% while "
              "Germany falls to 1.5%, the euro crisis rendered as a single number. Eurostat covers "
              "EU members and the UK only, so non-EU neighbours have no line on this measure."},
    {"id": "wages", "lens": "Financial", "code": "EUROSTAT.EARN_NT_NET", "label": "Net annual earnings",
     "unit": "\u20ac", "dp": 0, "prefix": "\u20ac",
     "blurb": "Annual net earnings for a single person without children on an average wage, in euro. "
              "The closest thing here to take-home pay. <strong>Eurostat flags 2024 as a break in "
              "series</strong>, and several countries shift sharply between 2023 and 2024 as a "
              "result — Germany falls from €37,908 to €30,145, Portugal rises from €15,301 to "
              "€18,835. Treat 2000–2023 and 2024–2025 as two segments, not one line."},
    {"id": "gdpconv", "lens": "Financial", "code": "DERIVED.PPP.PCT.EU", "label": "Convergence (GDP vs EU average)",
     "unit": "%", "dp": 1, "suffix": "%", "ref": 100,
     "blurb": "The same convergence measure computed on GDP rather than GNI, shown for comparison. "
              "Luxembourg and Ireland both exceed 235% here — an artefact of where profit is booked, "
              "not of what residents earn. Read the GNI version as the honest one."},

    {"id": "trade", "lens": "Commercial", "code": "DERIVED.TRADE.OPEN",
     "label": "Trade openness", "unit": "%", "dp": 1, "suffix": "%",
     "blurb": "Exports plus imports as a share of GDP — the standard openness measure, and the most "
              "direct commercial reading of single-market access. Values above 100% are normal rather "
              "than anomalous: a component crossing a border three times inside a supply chain is "
              "counted three times, so integration itself inflates the number. That makes this a good "
              "measure of <em>integration</em> and a poor one of <em>size</em>. Luxembourg exceeds 375% "
              "and Ireland's series is further distorted by contract manufacturing booked in Dublin "
              "without goods ever entering the country."},
    {"id": "fdi", "lens": "Commercial", "code": "BX.KLT.DINV.WD.GD.ZS",
     "label": "Foreign direct investment", "unit": "%", "dp": 1, "suffix": "%",
     "blurb": "Net FDI inflows as a share of GDP. Treat the top of this chart with real suspicion: in "
              "Luxembourg, Malta, Ireland, Cyprus and the Netherlands the series is dominated by "
              "special-purpose entities — holding companies routing capital onward the same quarter — "
              "so it measures conduit activity rather than factories built. It is also genuinely "
              "volatile: single corporate restructurings move a small country's annual figure by tens "
              "of percentage points, which is why the year-to-year line is jagged everywhere."},
    {"id": "tourism", "lens": "Commercial", "code": "ST.INT.ARVL",
     "label": "Tourist arrivals", "unit": "million", "dp": 1, "suffix": "m", "scale": 1e-6,
     "blurb": "International tourist arrivals, in millions. <strong>The series ends in 2020 for every "
              "country here</strong>, so the COVID collapse is visible but the recovery is not — read "
              "the final point as the pandemic, not as a trend. Croatia's figure counts border "
              "crossings rather than overnight stays, which makes it high relative to neighbours on "
              "definition alone. Unlike the other measures this is a raw count, so it partly tracks "
              "country size."},
    {"id": "migration", "lens": "Social", "code": "DERIVED.NETM.P1000",
     "label": "Net migration", "unit": "per 1,000", "dp": 1, "suffix": " per 1,000", "ref": 0,
     "blurb": "Net migration per 1,000 residents — arrivals minus departures, scaled so that countries "
              "of different sizes are comparable. Above the zero line a country is gaining people, "
              "below it losing them. This is the measure where free movement shows up most sharply: "
              "the Baltic states and Romania run deeply negative after 2004, while Germany's 2015 "
              "spike to +14 per 1,000 is the refugee year. These are modelled demographic estimates "
              "rather than administrative counts, so read the direction and scale, not the decimal."},
    {"id": "gini", "lens": "Social", "code": "SI.POV.GINI",
     "label": "Income inequality (Gini)", "unit": "index", "dp": 1,
     "lowerIsBetter": True,
     "blurb": "Gini index of disposable income, 0 = perfect equality, 100 = one household holds "
              "everything. Lower is better. This is <strong>survey data, not an annual statistic</strong> "
              "— points are irregular and some countries have long gaps, so the lines here are sparser "
              "than elsewhere and a missing year means no survey rather than no change. Comparisons "
              "across countries are also weaker than within one country over time, because national "
              "surveys differ in method even after harmonisation."},

    {"id": "ruleoflaw", "lens": "Legal", "code": "WGI.RL.EST",
     "label": "Rule of law", "unit": "points", "dp": 2, "ref": 0, "refLabel": "world average",
     "blurb": "World Bank governance estimate for rule of law — confidence in and abidance by the "
              "rules of society, contract enforcement, property rights, the police and the courts. "
              "This is the only measure of legal quality in the dataset that also covers non-members, "
              "which is the only reason a comparison is possible at all." + WGI_CAVEAT},
    {"id": "voice", "lens": "Political", "code": "WGI.VA.EST",
     "label": "Voice and accountability", "unit": "points", "dp": 2, "ref": 0, "refLabel": "world average",
     "blurb": "The extent to which citizens can participate in selecting their government, together "
              "with freedom of expression, freedom of association and a free press. The closest "
              "thing here to a measure of democratic quality." + WGI_CAVEAT},
    {"id": "corruption", "lens": "Political", "code": "WGI.CC.EST",
     "label": "Control of corruption", "unit": "points", "dp": 2, "ref": 0, "refLabel": "world average",
     "blurb": "The extent to which public power is exercised for private gain. Higher is better: a "
              "rising line means stronger control, not more corruption. Anti-corruption "
              "conditionality was an explicit part of accession negotiations for the 2004, 2007 and "
              "2013 waves." + WGI_CAVEAT},
]


def load():
    series = collections.defaultdict(dict)
    names = {}
    for r in csv.DictReader(open(os.path.join(DATA, "indicators.csv"), encoding="utf-8")):
        if r["value"]:
            series[(r["iso3"], r["indicator_code"])][int(r["year"])] = float(r["value"])
            names[r["iso3"]] = r["country"]
    return series, names


def main():
    series, names = load()
    regs = list(csv.DictReader(open(os.path.join(DATA, "regions.csv"), encoding="utf-8")))
    meta = {r["iso3"]: r for r in csv.DictReader(open(os.path.join(DATA, "countries.csv"), encoding="utf-8"))}

    # members first inside each region, then non-EU neighbours
    order, members = [], collections.OrderedDict()
    for r in sorted(regs, key=lambda x: (int(x["region_order"]),
                                         0 if x["group"] == "member" else 1, x["name"])):
        members.setdefault(r["region"], []).append(r)
        if r["region"] not in order:
            order.append(r["region"])

    payload = {"generated": datetime.date.today().isoformat(), "years": YEARS,
               "regionOrder": order, "regions": {}, "measures": [], "lenses": LENSES}

    for reg in order:
        ms = members[reg]
        mem = [m for m in ms if m["group"] == "member"]
        nbr = [m for m in ms if m["group"] != "member"]
        payload["regions"][reg] = {
            "name": reg, "n": len(mem), "nNeighbours": len(nbr),
            "countries": [{
                "iso3": m["iso3"], "name": m["name"],
                "member": m["group"] == "member",
                "accession": int(m["accession_year"]) if m["accession_year"] else None,
                "note": m.get("note", ""),
                "slug": (re.sub(r"[^a-z0-9]+", "-", m["name"].lower()).strip("-") + "-dashboard.html")
                        if m["group"] == "member" else "",
                "euro": meta.get(m["iso3"], {}).get("euro_adopted", ""),
            } for m in ms],
            "waves": sorted({int(m["accession_year"]) for m in mem if m["accession_year"]}),
        }

    for spec in MEASURES:
        code = spec["code"]
        # counts are stored raw in the CSV and scaled only for display, so the
        # data store stays in the source's own units
        sc = spec.get("scale", 1.0)
        regionPaths, countryPaths, ranked, changes = {}, {}, [], []
        for reg in order:
            isos = [m["iso3"] for m in members[reg] if m["group"] == "member"]
            allisos = [m["iso3"] for m in members[reg]]
            path = []
            for y in YEARS:
                vals = [series.get((i, code), {}).get(y) for i in isos]
                vals = [v * sc for v in vals if v is not None]
                # require at least half the region present, else the median jumps
                # around as countries enter and leave the series
                path.append(round(statistics.median(vals), 2) if len(vals) >= max(1, len(isos) // 2) else None)
            regionPaths[reg] = path
            for i in allisos:
                d = series.get((i, code), {})
                if d:
                    countryPaths[i] = [None if d.get(y) is None else round(d[y] * sc, 4)
                                       for y in YEARS]
            present = [(y, v) for y, v in zip(YEARS, path) if v is not None]
            if present:
                ranked.append({"region": reg, "value": present[-1][1], "year": present[-1][0],
                               "n": len(isos)})
                base = next((v for y, v in present if y >= 1996), present[0][1])
                # round endpoints and the change at the SAME precision as the measure is
                # displayed at, so "0.70 to 0.60" and "-0.2" cannot appear side by side
                dp = spec["dp"]
                frm, to = round(base, dp), round(present[-1][1], dp)
                changes.append({"region": reg, "change": round(to - frm, dp),
                                "from": frm, "to": to,
                                "fromYear": max(1996, present[0][0]), "toYear": present[-1][0]})
        ranked.sort(key=lambda r: r["value"], reverse=not spec.get("lowerIsBetter"))
        changes.sort(key=lambda r: r["change"], reverse=not spec.get("lowerIsBetter"))
        eu = series.get(("EUU", code))
        payload["measures"].append({
            "id": spec["id"], "label": spec["label"], "blurb": spec["blurb"],
            "lens": spec.get("lens", "Financial"),
            "unit": spec["unit"], "dp": spec["dp"],
            "prefix": spec.get("prefix", ""), "suffix": spec.get("suffix", ""),
            "lowerIsBetter": bool(spec.get("lowerIsBetter")),
            "ref": spec.get("ref"), "refLabel": spec.get("refLabel"),
            "regionPaths": regionPaths, "countryPaths": countryPaths,
            "ranked": ranked, "changes": changes,
            "euLine": [None if eu.get(y) is None else round(eu[y] * sc, 4)
                       for y in YEARS] if eu else None,
        })

    # a neighbour may legitimately border EU states in two regions; record which,
    # so the page can say so rather than leaving it looking like an error
    seen = collections.defaultdict(list)
    for r in regs:
        if r["group"] != "member":
            seen[r["iso3"]].append(r["region"])
    payload["sharedNeighbours"] = {k: v for k, v in seen.items() if len(v) > 1}
    payload["names"] = {i: n for i, n in names.items()}
    html = open(os.path.join(BASE, "regions_template.html"), encoding="utf-8").read()
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    open(os.path.join(BASE, "index.html"), "w", encoding="utf-8").write(html.replace("__PAYLOAD__", blob))
    nm = sum(1 for v in members.values() for m in v if m["group"] == "member")
    nn = sum(1 for v in members.values() for m in v if m["group"] != "member")
    print(f"built index.html — {len(order)} regions, {nm} members + {nn} neighbour slots, "
          f"{len(payload['measures'])} measures")
    for c in payload["measures"][0]["changes"]:
        print(f"   {c['region']:18s} {c['from']:6.1f}% -> {c['to']:6.1f}%  ({c['change']:+5.1f}pp)")


if __name__ == "__main__":
    main()
