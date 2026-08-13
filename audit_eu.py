#!/usr/bin/env python3
"""Cross-check eu.html against the sources it was built from.

The EU page mixes three provenances -- a hand-entered CSV of published Eurostat and DG TRADE
figures, the reconciled budget payload, and the analysis payload's regional shares. Each is
credible on its own; the risk is that the page states a number none of them contains, or
states arithmetic that does not follow. So every value is checked back to its origin and every
derived figure is recomputed.
"""
import json, re, csv, sys, pathlib

BASE = pathlib.Path(__file__).resolve().parent
P = json.loads(re.search(r'<script id="payload" type="application/json">(.*?)</script>',
               (BASE / "eu.html").read_text(encoding="utf-8"), re.S)
               .group(1).replace("<\\/", "</"))
src = {r["label"]: r for r in csv.DictReader(open(BASE / "data" / "eu_stats.csv",
                                                 encoding="utf-8"))}
bad = []

# 1. every stated figure traces to the CSV, and carries a source
for k in ("kpis", "trade", "world"):
    for r in P[k]:
        s = src.get(r["label"])
        if not s:
            bad.append(f"{k}/{r['label']}: not in eu_stats.csv")
        elif s["value"].strip() and abs(float(s["value"]) - r["value"]) > 1e-9:
            bad.append(f"{k}/{r['label']}: {r['value']} != CSV {s['value']}")
        if not (r.get("source") or "").strip():
            bad.append(f"{k}/{r['label']}: no source recorded")

# 2. the intra/extra split is arithmetic on the trade rows, not a separate claim
S, T = P["split"], P["trade"]
intra = next(r["value"] for r in T if r["label"].startswith("Intra"))
xe = next(r["value"] for r in T if "exports" in r["label"])
xi = next(r["value"] for r in T if "imports" in r["label"])
for name, got, want in (("intra", S["intra"], intra), ("extra", S["extra"], xe + xi),
                        ("total", S["total"], intra + xe + xi),
                        ("balance", S["balance"], xe - xi),
                        ("intraPctOnce", S["intraPctOnce"], intra / (intra + xe + xi) * 100),
                        ("intraPctTwice", S["intraPctTwice"],
                         2 * intra / (2 * intra + xe + xi) * 100)):
    if abs(got - want) > 0.06:
        bad.append(f"split.{name}: {got} but recomputes to {want:.2f}")

# 3. partner totals and balances follow from the two flows
for q in P["partners"]:
    if q["exp"] is None or q["imp"] is None:
        continue
    if abs(q["total"] - (q["exp"] + q["imp"])) > 0.11:
        bad.append(f"{q['label']}: total != exports + imports")
    if abs(q["balance"] - (q["exp"] - q["imp"])) > 0.11:
        bad.append(f"{q['label']}: balance != exports - imports")
# and the ranking is by total, as the card claims
drawn = [q for q in P["partners"] if q["exp"] is not None and q["imp"] is not None]
if drawn != sorted(drawn, key=lambda q: -q["total"]):
    bad.append("partners are not in descending order of total trade")

# 4. the budget shares partition
B = P["budget"]
tot = sum(f["pct"] for f in B["funds"])
if abs(tot - 100) > 0.6:
    bad.append(f"fund shares sum to {tot:.1f}, not 100")
if abs(B["topTwoPct"] - sum(f["pct"] for f in B["funds"][:2])) > 0.05:
    bad.append("topTwoPct does not match the first two funds")
if B["payers"][0]["net"] > 0 or B["receivers"][0]["net"] < 0:
    bad.append("payers/receivers are the wrong way round")

# 5. the regional shares partition to ~100 each year, and the double-counted subset is gone
R = P["regions"]
if any(r["code"].endswith("USMCA") for r in R["rows"]):
    bad.append("North America is drawn beside the Americas -- double counted")
for i, y in enumerate(R["years"]):
    tot = sum(r["path"][i] for r in R["rows"] if r["path"][i] is not None)
    if abs(tot - 100) > 3.0:
        bad.append(f"regional shares for {y} sum to {tot:.1f}")

print(f"{len(P['kpis'])} KPIs · {len(P['partners'])} partners ({len(drawn)} drawn) · "
      f"{len(B['funds'])} funds · {len(R['rows'])} regions x {len(R['years'])} years")
print(f"{len(bad)} problem(s)")
for b in bad:
    print("  *** " + b)
sys.exit(1 if bad else 0)
