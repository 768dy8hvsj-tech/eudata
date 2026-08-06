#!/usr/bin/env python3
"""What each member state pays into the EU budget, and what comes back, by fund.

Two things make this harder than reading a spreadsheet.

First, the hierarchy: see tree.py, which recovers it and proves the recovered leaves sum to
the Commission's published total for every country in every year.

Second, the naming. The Commission renames and reshuffles its programmes at every seven-year
budget round. "Structural funds - Total ERDF" (2000-06), "Convergence objective" (2007-13),
"Less developed regions" (2014-20) and "European Regional Development Fund (ERDF)" (2021-24)
are four labels for money doing the same job. FUNDS below is the crosswalk, written as an
ordered list of matchers so it can be read and argued with rather than trusted.

The crosswalk is checked two ways. Nothing may match twice (the first matcher wins, and a
line matching none of them lands in "Other programmes"), and the funds must still sum to
the published total per country per year -- the same test the hierarchy had to pass.

ONE LIMITATION IS STRUCTURAL AND CANNOT BE FIXED HERE. Between 2007 and 2020 the workbook
does not separate the Regional Development Fund from the Social Fund: it reports them
together under objective headings ("Convergence objective", "Less developed regions"). They
are separable in 2000-06 and again from 2021. So this build carries ONE combined fund,
"Regional & social funds", across all twenty-five years rather than a split that would
silently change meaning in 2007 and again in 2021.
"""
import csv, collections, json, os, re, statistics
import tree

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

# ------------------------------------------------------------------ the crosswalk
# (fund id, label, [regex matched against the leaf label], [regex matched against heading])
# Order matters: the first fund whose pattern matches claims the line.
FUNDS = [
    ("farm", "Farm payments and market support",
     r"direct aid|export refunds|^storage$|agricultural guarantee|agriculture markets|"
     r"animal and plant health|food and feed", None),
    ("rural", "Rural development",
     r"rural development|agricultural fund for rural|total eaggf", None),
    ("fish", "Fisheries and maritime",
     r"fisheries|total fifg|maritime", None),
    ("cf", "Cohesion Fund",
     r"^cohesion fund|cohesion fund \(cf\)|contribution to the connecting europe facility \(cef\)$",
     None),
    ("regional", "Regional and social funds",
     r"total erdf|total esf|regional development fund|social fund \(esf\)|convergence objective|"
     r"less developed regions|transition regions|more developed regions|outermost and sparsely|"
     r"regional competitiveness|territorial cooperation|investment for growth", None),
    ("research", "Research and innovation",
     r"research framework|horizon|euratom|thermonuclear|research and technological development|"
     r"decommissioning \(direct research\)", None),
    ("infra", "Infrastructure, digital and space",
     r"connecting europe|^ten$|^transport$|^energy$|satellite navigation|copernicus|galileo|"
     r"space programme|marco polo|digital europe|investeu|strategic investments|"
     r"trans-european|single market programme|competitiveness of enterprises|"
     r"informations and communications|energy projects to aid|secure connectivity", None),
    ("edu", "Education, youth and culture",
     r"erasmus|lifelong learning|creative europe|culture 200|media 200|youth in action|"
     r"europe for citizens|solidarity corps|training, youth, culture", None),
    ("social", "Social, employment and health",
     r"employment and social innovation|youth employment initiative|most deprived|eu4health|"
     r"field of health|public health|consumer programme|social policy agenda", None),
    ("recovery", "Recovery, resilience and solidarity",
     r"recovery and resilience|brexit adjustment|solidarity and emergency|globalisation adjustment|"
     r"global adjustment|european solidarity fund|civil protection|emergency support|"
     r"recovery instrument \(euri\)|special instruments", None),
    ("security", "Migration, security, justice and defence",
     r"asylum, migration|internal security|border management|management of migration flows|"
     r"security and safeguarding|defence|military mobility|edirpa|nuclear decommissioning|"
     r"nuclear safety|it systems|^justice|justice programme|fundamental rights|rights and values|"
     r"rights, equality", None),
    ("external", "External action and enlargement",
     r"pre-accession|preaccession|neighbourhood, development|humanitarian aid|foreign and security|"
     r"overseas countries|nuclear safety \(eins\)|instrument for nuclear safety|mfa\+|"
     r"reform and growth facility|turkish-cypriot", r"external actions|pre-accession strategy|"
     r"global partner|global europe|neighbourhood"),
    ("env", "Environment and climate",
     r"environment and climate|^life\+?$|just transition|euratom nuclear safeguards", None),
    ("admin", "Administration",
     r"^administration$|^commission$|other institutions|european schools and pensions",
     r"^administration$|european public administration"),
]
OTHER = ("other", "Other programmes and reserves")

# Rules where BOTH the label and the heading must match, applied before FUNDS. There is one
# job here: the workbook books a line called simply "Other" under each era's agriculture
# heading -- 73bn of market intervention, storage and disposal that is plainly farm support
# and would otherwise fall into the residual bucket. Matching "Other" on the label alone
# would swallow "Other internal policies" and every "Other actions and programmes" line too,
# so the heading has to be part of the test.
BOTH = [
    ("farm", r"^other$|^export refunds$|^storage$",
     r"^agriculture$|preservation and management of natural|sustainable growth: natural|"
     r"^natural resources and environment$"),
]

# ------------------------------------------------------------------ revenue side
# Every era in one vocabulary. TOR is the traditional own resources line -- customs duties
# and levies, net of the 20-25% the collecting state keeps -- reported directly through 2020
# and as separate customs and sugar lines from 2021.
SOURCES = [
    ("gni", "GNI-based contribution", r"^gn[ip]-based own resource|own resources based on gni$"),
    ("vat", "VAT-based contribution", r"^vat-based own resource|own resources based on vat$"),
    ("tor", "Customs duties and levies (net)",
     r"^traditional own resources|^customs duties$|^sugar levies$"),
    ("plastic", "Plastic packaging levy", r"plastic packaging"),
    ("rebate", "Rebates, corrections and adjustments",
     r"uk correction|lump sum reduction|jha adjustment|fsj adjustment|gross reduction|"
     r"restitutions|adjustment re|adjustment retro|retro-active implementation|"
     r"netting of adjustments|balances and adjustments|adjustment relating|adjustment related"),
]
TOTAL_CONTRIB = r"^total national contribution"
GNI_ROW = r"gross national income"


def matcher(label, heading, pats):
    lab, head = label.lower(), (heading or "").lower()
    for fid, lp, hp in BOTH:
        if re.search(lp, lab) and re.search(hp, head):
            return fid
    for fid, name, lp, hp in pats:
        if lp and re.search(lp, lab):
            return fid
        if hp and re.search(hp, head):
            return fid
    return None


def main():
    sheet, agg, pc, lv = tree.build()

    names, accession = {}, {}
    for r in csv.DictReader(open(os.path.join(DATA, "blocs.csv"), encoding="utf-8")):
        names[r["iso3"]] = r["name"]
        if r["accession_year"].strip().isdigit():
            accession[r["iso3"]] = int(r["accession_year"])

    pop = collections.defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(DATA, "indicators.csv"), encoding="utf-8")):
        if r["indicator_code"] == "SP.POP.TOTL" and r["value"]:
            pop[r["iso3"]][int(r["year"])] = float(r["value"])

    years = sorted(lv)
    fund_ids = [f[0] for f in FUNDS] + [OTHER[0]]
    src_ids = [s[0] for s in SOURCES]

    # ---- expenditure, mapped ----
    rec = collections.defaultdict(float)        # (iso, year, fund) -> EUR m
    unmatched = collections.Counter()
    for y in years:
        for i in lv[y]:
            m = sheet[y][i]
            fid = matcher(m["label"], m["heading"], FUNDS) or OTHER[0]
            if fid == OTHER[0]:
                unmatched[m["label"]] += agg[(y, i)]
            for iso, v in pc[(y, i)].items():
                rec[(iso, y, fid)] += v

    # ---- revenue, mapped ----
    rows = list(csv.DictReader(open(tree.DETAIL, encoding="utf-8")))
    pay = collections.defaultdict(float)
    published_contrib, gni = collections.defaultdict(float), collections.defaultdict(float)
    rev_unmatched = collections.Counter()
    for r in rows:
        if r["block"] != "revenue":
            continue
        y, iso, lab, v = int(r["year"]), r["iso3"], r["label"].lower(), float(r["value"])
        if re.search(GNI_ROW, lab):
            gni[(iso, y)] = v
            continue
        if re.match(TOTAL_CONTRIB, lab) or lab.startswith("total national contributions"):
            published_contrib[(iso, y)] = v
            continue
        # Deliberate exclusions, not failures to map:
        #  - TOTAL rows are sums of the lines above them;
        #  - the gross "(100%)" customs, agricultural duty and sugar lines and the matching
        #    "amounts retained" line are the components of the net TOR figure already taken;
        #  - surpluses and guarantee-fund returns are other revenue, not a national payment.
        if (lab.startswith("total ") or lab.startswith("amounts (")
                or "retained as tor" in lab or "(100%)" in lab
                or lab.startswith("surplus")):
            continue
        sid = None
        for s, _n, p in SOURCES:
            if re.search(p, lab):
                sid = s
                break
        if sid is None:
            rev_unmatched[r["label"]] += abs(v)
            continue
        pay[(iso, y, sid)] += v

    # ---- verification ----------------------------------------------------------------
    isos = sorted({k[0] for k in rec})
    worst_exp = worst_rev = 0.0
    wit_exp = wit_rev = ""
    for y in years:
        tot_row = next((i for i in sheet[y]
                        if sheet[y][i]["label"].upper().startswith("TOTAL EXPENDITURE")), None)
        for iso in isos:
            t = pc[(y, tot_row)].get(iso, 0.0) if tot_row else 0.0
            if abs(t) > 1:
                s = sum(rec[(iso, y, f)] for f in fund_ids)
                d = abs(s - t) / abs(t) * 100
                if d > worst_exp:
                    worst_exp, wit_exp = d, f"{iso} {y}"
            c = published_contrib.get((iso, y), 0.0)
            if abs(c) > 1:
                s = sum(pay[(iso, y, sid)] for sid in ("gni", "vat", "plastic", "rebate"))
                d = abs(s - c) / abs(c) * 100
                if d > worst_rev:
                    worst_rev, wit_rev = d, f"{iso} {y}"
    print(f"expenditure: funds sum to published total, worst error {worst_exp:.4f}% ({wit_exp})")
    print(f"revenue:     sources sum to published national contribution, "
          f"worst error {worst_rev:.4f}% ({wit_rev})")
    print(f"\nunmapped expenditure landing in 'Other programmes': "
          f"{sum(unmatched.values())/1000:.1f}bn of {sum(agg[(y,i)] for y in years for i in lv[y])/1000:.1f}bn")
    for lab, v in unmatched.most_common(10):
        print(f"    {v/1000:7.1f}bn  {lab[:74]}")
    if rev_unmatched:
        print("\nunmapped revenue lines (should be empty):")
        for lab, v in rev_unmatched.most_common(10):
            print(f"    {v/1000:7.1f}bn  {lab[:74]}")

    # ---- payload ---------------------------------------------------------------------
    fund_meta = [{"id": f[0], "label": f[1]} for f in FUNDS] + \
                [{"id": OTHER[0], "label": OTHER[1]}]
    src_meta = [{"id": s[0], "label": s[1]} for s in SOURCES]

    countries = []
    for iso in isos:
        if iso not in names:
            continue
        start = max(2000, accession.get(iso, 2000))
        yrs = [y for y in years if y >= start]
        if not yrs:
            continue
        tin, tout = [], []
        for y in years:
            tin.append(round(sum(rec[(iso, y, f)] for f in fund_ids), 1) if y in yrs else None)
            tout.append(round(sum(pay[(iso, y, s)] for s in src_ids) + 0.0, 1)
                        if y in yrs else None)
        # Rounded per fund for display, but the totals are summed from the unrounded values.
        # Fifteen funds each rounded to the nearest million put a visible 0.1% error on the
        # total for a small member state, which then shows up as a false failure in
        # verify_flows.py -- a check that is only useful if it does not cry wolf.
        raw_r = {f: sum(rec[(iso, y, f)] for y in yrs) / 1000 for f in fund_ids}
        raw_p = {s: sum(pay[(iso, y, s)] for y in yrs) / 1000 for s in src_ids}
        cum_r = {f: round(v, 3) for f, v in raw_r.items()}
        cum_p = {s: round(v, 3) for s, v in raw_p.items()}
        tot_in, tot_out = sum(raw_r.values()), sum(raw_p.values())
        g = [gni.get((iso, y)) for y in yrs if gni.get((iso, y))]
        p = [pop[iso].get(y) for y in yrs if pop[iso].get(y)]
        countries.append({
            "iso3": iso, "name": names[iso], "since": start,
            "accession": accession.get(iso),
            "receipts": {f: [round(rec[(iso, y, f)], 1) if y in yrs else None for y in years]
                         for f in fund_ids},
            "payments": {s: [round(pay[(iso, y, s)], 1) if y in yrs else None for y in years]
                         for s in src_ids},
            "totalIn": tin, "totalOut": tout,
            "cumReceipts": cum_r, "cumPayments": cum_p,
            "cumIn": round(tot_in, 3), "cumOut": round(tot_out, 3),
            "net": round(tot_in - tot_out, 3),
            "gniMean": round(statistics.fmean(g), 1) if g else None,
            "popMean": round(statistics.fmean(p)) if p else None,
            "years": len(yrs),
        })

    # per-fund cross-country view: cumulative, per head per year, and as % of national income
    byfund = {}
    for f in fund_ids:
        rowsf = []
        for c in countries:
            cum = c["cumReceipts"][f]
            rowsf.append({
                "iso3": c["iso3"], "name": c["name"], "cum": cum,
                "perHead": round(cum * 1e9 / (c["popMean"] * c["years"]), 1)
                           if c["popMean"] else None,
                "pctGni": round(cum * 1000 / (c["gniMean"] * c["years"]) * 100, 3)
                          if c["gniMean"] else None,
            })
        byfund[f] = sorted(rowsf, key=lambda r: -(r["pctGni"] or -1))

    bysource = {}
    for s in src_ids:
        rowss = []
        for c in countries:
            cum = c["cumPayments"][s]
            rowss.append({
                "iso3": c["iso3"], "name": c["name"], "cum": cum,
                "perHead": round(cum * 1e9 / (c["popMean"] * c["years"]), 1)
                           if c["popMean"] else None,
                "pctGni": round(cum * 1000 / (c["gniMean"] * c["years"]) * 100, 3)
                          if c["gniMean"] else None,
            })
        bysource[s] = sorted(rowss, key=lambda r: -(r["pctGni"] or -1))

    payload = {
        "years": years, "funds": fund_meta, "sources": src_meta,
        "countries": sorted(countries, key=lambda c: c["name"]),
        "byFund": byfund, "bySource": bysource,
        "check": {"expenditure": round(worst_exp, 4), "revenue": round(worst_rev, 4),
                  "otherShare": round(sum(unmatched.values())
                                      / sum(agg[(y, i)] for y in years for i in lv[y]) * 100, 2)},
        "source": "European Commission, EU spending and revenue 2000-2024 "
                  "(workbook published 25 September 2025)",
    }
    json.dump(payload, open(os.path.join(BASE, "flows_payload.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    print(f"\nflows_payload.json: {len(countries)} countries, {len(fund_ids)} funds, "
          f"{len(src_ids)} revenue sources")

    tpl = os.path.join(BASE, "flows_template.html")
    if os.path.exists(tpl):
        html = open(tpl, encoding="utf-8").read()
        blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
        open(os.path.join(BASE, "flows.html"), "w", encoding="utf-8").write(
            html.replace("__PAYLOAD__", blob))
        print("flows.html written")


if __name__ == "__main__":
    main()
