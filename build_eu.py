#!/usr/bin/env python3
"""Build the Union-level overview page.

Every other page in this study looks at one country. This one looks at the thing they are
members of: what the Union is worth, what it spends, and — the part that surprises people —
where its trade actually goes.

Reads:
    data/eu_stats.csv        headline financials, trade totals, top partners, world shares
    flows_payload.json       the budget, already reconciled to 0.0000% by build_flows.py
    analysis_payload.json    the extra-EU regional export shares, 2002-2025
    data/indicators.csv      the EUU series the rest of the study already uses
    eu_template.html         presentation layer, no data in it

Writes:
    eu.html

DESIGN NOTE — why the trade section leads with one number. The headline fact about EU trade
is not who the biggest partner is; it is that the Union's members trade far more with each
other than with anyone outside. Every partner ranking is a ranking of the smaller half. The
page says that first, in a single comparison, and only then ranks the outside partners.

A NOTE ON THE INTRA-EU SHARE. Eurostat publishes intra-EU trade as one value on the
dispatches basis, and publishes no EU-level intra share at all. Counting intra-EU trade once
gives 44.6% of all goods trade; counting it the way the per-country tables do -- once as a
dispatch and once as an arrival -- gives 61.6%. Both are defensible and they are not the same
number, so this page states the underlying values, shows the once-counted split, and names the
other convention rather than picking one silently.
"""
import csv, json, pathlib, datetime, collections

BASE = pathlib.Path(__file__).resolve().parent
DATA = BASE / "data"


def stats():
    """-> {panel: [row, ...]} from data/eu_stats.csv, provenance intact on every row."""
    out = collections.defaultdict(list)
    for r in csv.DictReader(open(DATA / "eu_stats.csv", encoding="utf-8")):
        out[r["panel"]].append({
            "label": r["label"],
            "value": float(r["value"]) if r["value"].strip() else None,
            "value2": float(r["value2"]) if r["value2"].strip() else None,
            "unit": r["unit"], "note": r["note"], "source": r["source"],
        })
    return dict(out)


def budget():
    """The Union's own spending, from the reconciled flows payload.

    Not re-derived here. build_flows.py already parses 233 budget lines into 15 funds and
    checks them against the Commission's own totals to 0.0000%; this reads that result.
    """
    p = BASE / "flows_payload.json"
    if not p.exists():
        return None
    F = json.loads(p.read_text(encoding="utf-8"))
    funds = {f["id"]: f["label"] for f in F["funds"]}
    tot = collections.Counter()
    for c in F["countries"]:
        for k, v in c["cumReceipts"].items():
            tot[k] += v
    grand = sum(tot.values())
    rows = sorted(({"label": funds[k], "v": round(v, 1),
                    "pct": round(v / grand * 100, 1)} for k, v in tot.items() if v > 0),
                  key=lambda r: -r["v"])
    net = sorted(({"iso3": c["iso3"], "name": c["name"], "net": round(c["net"], 1)}
                  for c in F["countries"]), key=lambda r: r["net"])
    return {
        "years": [F["years"][0], F["years"][-1]],
        "grand": round(grand, 1),
        "funds": rows,
        # the two ends of the distribution, which is the whole story of the budget
        "payers": net[:5],
        "receivers": list(reversed(net[-5:])),
        # agriculture and cohesion against everything else
        "topTwoPct": round(sum(r["pct"] for r in rows[:2]), 1),
        "topTwo": [rows[0]["label"], rows[1]["label"]],
    }


def regions():
    """Extra-EU export shares by world region, 2002-2025, from the analysis payload."""
    p = BASE / "analysis_payload.json"
    if not p.exists():
        return None
    A = json.loads(p.read_text(encoding="utf-8"))
    D = A.get("direction") or {}
    R = D.get("regions")
    if not R:
        return None
    yrs = D.get("years") or list(range(2002, 2002 + len(R[0]["path"])))
    # Three of the seven series are subsets, not peers. North America and Latin America both
    # sit inside the Americas -- and they overlap each other as well, since 24.8 + 5.7 exceeds
    # the Americas' own 28.8 in the latest year. Drawing them beside their parent inflated the
    # chart to 104%; the page audit caught it. Only the five top-level regions partition.
    TOP = ["TRADE.REG.EXP.EUR", "TRADE.REG.EXP.AMER", "TRADE.REG.EXP.ASIA",
           "TRADE.REG.EXP.AFR", "TRADE.REG.EXP.OCE"]
    keep = [r for r in R if r["code"] in TOP]
    keep.sort(key=lambda r: TOP.index(r["code"]))
    # the five named regions reach about 98%. The remainder is ships' and aircraft stores and
    # unallocated trade, and it is shown rather than quietly absorbed -- the same treatment the
    # per-country destination charts give it.
    resid = []
    for i in range(len(yrs)):
        tot = sum(r["path"][i] for r in keep if r["path"][i] is not None)
        resid.append(round(100 - tot, 1))
    keep.append({"code": "TRADE.REG.EXP.OTHER", "label": "Unallocated", "path": resid})
    subsets = {r["label"]: r["path"][-1] for r in R if r["code"] not in TOP}
    return {"years": yrs, "rows": keep, "subsets": subsets}


def eu_series():
    """The EUU series the rest of the study already carries, for the trajectory charts."""
    want = {"NY.GNP.PCAP.PP.CD": "GNI per capita, PPP",
            "NY.GDP.PCAP.KD": "GDP per capita, constant 2015 US$",
            "SP.POP.TOTL": "Population"}
    out = collections.defaultdict(dict)
    for r in csv.DictReader(open(DATA / "indicators.csv", encoding="utf-8")):
        if r["iso3"] == "EUU" and r["indicator_code"] in want and r["value"].strip():
            out[r["indicator_code"]][int(r["year"])] = float(r["value"])
    return [{"code": k, "label": want[k],
             "years": sorted(v), "values": [v[y] for y in sorted(v)]}
            for k, v in out.items() if v]


def main():
    S = stats()
    P = {
        "kpis": S.get("kpi", []),
        "trade": S.get("trade", []),
        "partners": S.get("partner", []),
        "world": S.get("world", []),
        "budget": budget(),
        "regions": regions(),
        "series": eu_series(),
        "generated": datetime.date.today().isoformat(),
    }

    T = S.get("trade", [])
    intra = next((r["value"] for r in T if r["label"].startswith("Intra")), 0)
    xexp = next((r["value"] for r in T if "exports" in r["label"]), 0)
    ximp = next((r["value"] for r in T if "imports" in r["label"]), 0)
    extra = xexp + ximp
    P["split"] = {
        "intra": intra, "extra": round(extra, 1),
        "total": round(intra + extra, 1),
        "intraPctOnce": round(intra / (intra + extra) * 100, 1),
        # the per-country convention counts each intra-EU consignment twice
        "intraPctTwice": round(2 * intra / (2 * intra + extra) * 100, 1),
        "balance": round(xexp - ximp, 1),
    }

    for p in P["partners"]:
        e, i = p["value"], p["value2"]
        p["total"] = round(((e or 0) + (i or 0)) / 1000, 1) if (e or i) else None
        p["balance"] = round(((e or 0) - (i or 0)) / 1000, 1) if (e and i) else None
        p["exp"] = round(e / 1000, 1) if e else None
        p["imp"] = round(i / 1000, 1) if i else None

    html = (BASE / "eu_template.html").read_text(encoding="utf-8")
    blob = json.dumps(P, ensure_ascii=False).replace("</", "<\\/")
    (BASE / "eu.html").write_text(html.replace("__PAYLOAD__", blob), encoding="utf-8")
    print(f"built eu.html  ({len(P['kpis'])} KPIs, {len(P['partners'])} partners, "
          f"{len(P['budget']['funds'])} funds, "
          f"{len(P['regions']['rows'])} regions x {len(P['regions']['years'])} years)")


if __name__ == "__main__":
    main()
