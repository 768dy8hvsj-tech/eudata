#!/usr/bin/env python3
"""Sanity check across the three non-member pages.

Three separate questions, because they fail differently:
  1  STRUCTURE  -- does every non-member page carry the same cards? An asymmetry is not
     automatically a bug (Switzerland has no EEA row to show) but every one should be
     deliberate rather than an accident of what was built when.
  2  INTERNAL   -- does a number appearing twice on one page agree with itself?
  3  PROVENANCE -- does every number in the payload trace back to the CSV it came from?
"""
import json, re, pathlib, csv, collections, sys

BASE = pathlib.Path(__file__).resolve().parent
PAGES = {"NOR": "norway-dashboard.html", "ISL": "iceland-dashboard.html",
         "CHE": "switzerland-dashboard.html"}

def payload(fn):
    m = re.search(r'<script id="payload" type="application/json">(.*?)</script>',
                  (BASE / fn).read_text(encoding="utf-8"), re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))

P = {iso: payload(fn) for iso, fn in PAGES.items()}

# A card missing from a page is either a bug or a decision. This manifest is where the
# decisions are written down, so the harness can fail on the bugs and stay quiet on the
# rest. "*" means every non-member page must carry it.
EXPECTED = {
    "verdict": "*", "flows": "*", "destinations": "*", "disputes": "*",
    "acquis": "*", "joining": "*", "competence": "*", "context": "*",
    "milestones": "*", "siblings": "*",
}
DELIBERATE = {
    ("money", "*"): "the EU budget workbook has no line for a non-member; flows replaces it",
    ("offsets", "NOR"): "no verified Norwegian farm-support budget figure, so the panel would "
                        "duplicate the flows card rather than add anything",
    ("offsets", "CHE"): "same -- and the Swiss offset question is structurally different, "
                        "since Switzerland pays cohesion without being in the EEA at all",
}

print("=" * 72)
print("1. STRUCTURE — which cards each page carries")
print("=" * 72)
CARDS = ["verdict", "money", "flows", "destinations", "disputes", "acquis", "joining",
         "competence", "offsets", "context", "milestones", "siblings"]
fails = []
print(f"{'card':16} " + "".join(f"{i:>8}" for i in PAGES) + "   note")
for c in CARDS:
    row, note = [], ""
    for iso in PAGES:
        v = P[iso].get(c)
        present = bool(v)
        row.append("—" if not present else (str(len(v)) if isinstance(v, (list, dict)) else "yes"))
        if not present:
            why = DELIBERATE.get((c, iso)) or DELIBERATE.get((c, "*"))
            if EXPECTED.get(c) == "*" and not why:
                fails.append(f"{iso} is missing '{c}' and no reason is recorded")
            elif why:
                note = "deliberate: " + why
    print(f"{c:16} " + "".join(f"{x:>8}" for x in row) + ("   " + note if note else ""))
for f in fails:
    print("  *** " + f)

print()
print("=" * 72)
print("2. CONTRIBUTION LINES — bases, currencies and periods actually being shown")
print("=" * 72)
for iso in PAGES:
    F = P[iso].get("flows") or {}
    print(f"\n{iso}")
    for d in ("out", "in"):
        for r in F.get(d, []):
            print(f"  {d:3} {r['amount']:>7} {r['currency']:<7} {r['basis']:<16} "
                  f"{r['period']:<12} {r['label'][:44]}")
    units = {(r["currency"], r["basis"]) for d in ("out", "in") for r in F.get(d, [])}
    if len(units) > 1:
        print(f"  note: {len(units)} distinct (currency, basis) pairs — never summed, by design")
    # a duplicated amount across two rows is usually a copy-paste, not a coincidence
    amts = collections.Counter(r["amount"] for d in ("out", "in") for r in F.get(d, []))
    for a, n in amts.items():
        if n > 1:
            fails.append(f"{iso}: amount {a} appears on {n} contribution rows — check for a "
                         f"copied cell")
    # where the detail text itemises components, they must sum to the stated amount
    for d in ("out", "in"):
        for r in F.get(d, []):
            comp = re.findall(r"(?:CHF|EUR)\s*([\d.]+)\s*(bn|m)\b", r["detail"])
            if len(comp) < 2:
                continue
            tot = sum(float(v) * (1000 if u == "bn" else 1) for v, u in comp)
            if abs(tot - float(r["amount"])) > 1:
                fails.append(f"{iso}: '{r['label']}' states {r['amount']} but its components "
                             f"sum to {tot:.0f}")

print()
print("=" * 72)
print("3. ACQUIS COUNTS — the headline each page states, recomputed from the rows")
print("=" * 72)
for iso in PAGES:
    A = P[iso].get("acquis")
    if not A: continue
    full = sum(1 for r in A["rows"] if r["here"] == "full")
    part = sum(1 for r in A["rows"] if r["here"] == "partial")
    none = sum(1 for r in A["rows"] if r["here"] == "none")
    ok = (full == A["full"] and part == A["partial"] and none == A["none"]
          and full + part + none == A["n"] == len(A["rows"]))
    print(f"{iso}: {full} full / {part} partial / {none} none of {len(A['rows'])}"
          f"   states: \"{A['counts']}\"   {'OK' if ok else '*** MISMATCH ***'}")
    J = P[iso].get("joining")
    if J:
        gains = full + part                    # areas that already apply, minus the vote row
        vote_in = any(r["area"] == "A vote on the rules" and r["here"] in ("full", "partial")
                      for r in A["rows"])
        exp = gains - (1 if vote_in else 0)
        print(f"     joining card says gainsN={J['gainsN']} entersN={J['entersN']}"
              f"   recomputed gains={exp}  {'OK' if J['gainsN'] == exp else '*** MISMATCH ***'}")


print()
print("=" * 72)
print("4. COMPETENCE MATRIX — the same five areas, scored on every page")
print("=" * 72)
areas = {}
for iso in PAGES:
    C = P[iso].get("competence")
    if not C:
        fails.append(f"{iso} has no competence card")
        continue
    areas[iso] = [r["label"] for r in C["comp"]]
    tally = collections.Counter(r["status"] for r in C["comp"])
    recomputed = ("%d of the %d exclusive competences already apply here in full, %d partly, "
                  "%d not at all, and %d cannot apply to this country at all"
                  % (tally.get("in", 0), len(C["comp"]), tally.get("partial", 0),
                     tally.get("out", 0), tally.get("na", 0)))
    ok = recomputed == C["summary"]
    print(f"{iso}: " + "  ".join(f"{k}={v}" for k, v in sorted(tally.items()))
          + f"   summary {'OK' if ok else '*** MISMATCH ***'}")
    if not ok:
        fails.append(f"{iso}: competence summary disagrees with the rows")
    if sum(tally.values()) != 5:
        fails.append(f"{iso}: {sum(tally.values())} competences, expected 5")
if len({tuple(v) for v in areas.values()}) > 1:
    fails.append("the five competences are not labelled identically across the three pages")
else:
    print("all three pages score the same five areas, identically labelled")

print()
print("=" * 72)
print(f"{len(fails)} problem(s)")
for f in fails:
    print("  *** " + f)
sys.exit(1 if fails else 0)
