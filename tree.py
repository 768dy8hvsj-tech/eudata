#!/usr/bin/env python3
"""Recover the budget hierarchy the workbook implies but never declares.

The sheets are flat lists of rows. Getting from that to "what did Poland actually receive
from the Cohesion Fund" needs to know which rows are totals of other rows, because summing
a parent and its children counts the same euro twice.

Two regimes, because the workbook has two.

FROM 2007 the rows carry dotted codes, and the code is *almost* a depth signal. Almost:
in 2010 "1.1.1" is the Seventh Research Framework Programme and "1.1.10" is Nuclear
decommissioning -- a sibling, despite being a string prefix. So parentage is proposed from
the codes and then tested arithmetically: a node keeps its children only if their values
sum to its own. Where the test fails, the children are re-parented one level up and the
test runs again, until nothing moves. That single check is what separates 1.1.7 (a real
parent of the three CIP lines) from 1.1.1 (not a parent of anything).

THROUGH 2006 there are no codes below the eight top-level headings, and worse, the sheet
prints the structural funds twice -- once split by Objective and once split by fund. No
arithmetic can choose between two correct decompositions of the same money, so that era
uses an explicit list, written out below and verified the same way as everything else.

Verification is the point: whatever this returns must sum to the Commission's own published
TOTAL EXPENDITURE, for every member state, in every one of the twenty-five years.
"""
import csv, collections

DETAIL = "data/raw/_eu_budget_detail.csv"

# 2000-2006. One line per entry the Commission itself treats as a component of its heading.
# The fund-level split is preferred over the Objective-level split: "of which ERDF" appears
# four times under four objectives, while "Structural funds - Total ERDF" appears once and
# is what a reader means by "the ERDF".
EARLY = {
    "AGRICULTURE": ["Direct Aid", "Export refunds", "Storage", "Rural development", "Other"],
    "STRUCTURAL ACTIONS": ["Structural funds - Total EAGGF", "Structural funds - Total FIFG",
                           "Structural funds - Total ERDF", "Structural funds - Total ESF",
                           "Other specific structural operations", "Cohesion Fund"],
    "INTERNAL POLICIES": [
        "Training, youth, culture, audiovisual, media, information & social actions",
        "Energy, Euratom nuclear safeguards and environment",
        "Consumer protection, internal market, industry and trans-European networks",
        "Research and technological development", "Other internal policies"],
}
# headings taken whole, with no split
WHOLE = {"EXTERNAL ACTIONS", "ADMINISTRATION", "RESERVES", "PRE-ACCESSION STRATEGY",
         "COMPENSATIONS", "NEGATIVE RESERVE", "SPECIAL INSTRUMENTS"}


def load(path=DETAIL):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    sheet = collections.defaultdict(dict)     # year -> {row: {code,label,heading}}
    agg = collections.defaultdict(float)      # (year,row) -> sum across member states
    pc = collections.defaultdict(dict)        # (year,row) -> {iso: value}
    for r in rows:
        if r["block"] != "expenditure":
            continue
        y, i = int(r["year"]), int(r["row"])
        sheet[y][i] = {"code": r["code"], "label": r["label"], "heading": r["heading"]}
        agg[(y, i)] += float(r["value"])
        pc[(y, i)][r["iso3"]] = float(r["value"])
    return sheet, agg, pc


def leaves(year, rowsmeta, agg, tol_rel=0.001):
    """Row indices that partition TOTAL EXPENDITURE exactly once."""
    idx = sorted(rowsmeta)
    meta = rowsmeta
    total_rows = {i for i in idx if meta[i]["label"].upper().startswith("TOTAL ")}
    live = [i for i in idx if i not in total_rows]

    if year <= 2006:
        out = []
        for i in live:
            h, lab = meta[i]["heading"], meta[i]["label"]
            if lab in WHOLE and lab == h:
                out.append(i)
            elif h in EARLY and lab in EARLY[h] and lab != h:
                out.append(i)
        return out

    # ---- 2007 onward: propose parentage from codes, then test it arithmetically ----
    code = {i: meta[i]["code"] for i in live}
    coded = [i for i in live if code[i]]
    bycode = {}
    for i in coded:
        bycode.setdefault(code[i], i)

    def proposed_parent(i):
        c = code[i]
        best = None
        for p in bycode:
            if p != c and c.startswith(p) and (best is None or len(p) > len(best)):
                best = p
        return bycode[best] if best else None

    parent = {i: proposed_parent(i) for i in coded}

    # uncoded rows belong to the nearest coded row above them
    for i in live:
        if not code[i]:
            prev = [j for j in coded if j < i]
            parent[i] = max(prev) if prev else None

    # Re-parent until every claimed parent's children actually add up to it. A node that
    # fails the test is not a parent at all, and its "children" are its siblings.
    #
    # Strictly deepest-first, one level per pass. Fixing several levels at once cascades:
    # 1.1.1 wrongly claims 1.1.10-12 as children and fails, but so does its own parent 1.1,
    # because the money sitting under 1.1.1 has not been released yet. Repairing 1.1 in the
    # same pass would push every research programme up to the top level and the whole tree
    # would collapse into a flat list that triple-counts.
    for _ in range(24):
        kids = collections.defaultdict(list)
        for i, p in parent.items():
            if p is not None:
                kids[p].append(i)
        failing = [p for p, ks in kids.items()
                   if abs(sum(agg[(year, k)] for k in ks) - agg[(year, p)])
                   > max(abs(agg[(year, p)]) * tol_rel, 1.0)]
        if not failing:
            break
        deepest = max(len(code.get(p, "")) for p in failing)
        for p in [p for p in failing if len(code.get(p, "")) == deepest]:
            for k in kids[p]:
                parent[k] = parent.get(p)

    kids = collections.defaultdict(list)
    for i, p in parent.items():
        if p is not None:
            kids[p].append(i)
    return [i for i in live if not kids.get(i)]


def build():
    sheet, agg, pc = load()
    out = {}
    for y in sorted(sheet):
        out[y] = leaves(y, sheet[y], agg)
    return sheet, agg, pc, out


if __name__ == "__main__":
    sheet, agg, pc, lv = build()
    print(f"{'year':>5}{'rows':>6}{'leaves':>8}{'worst':>10}  witness")
    worstall = 0.0
    for y in sorted(lv):
        tot = next((i for i in sheet[y]
                    if sheet[y][i]["label"].upper().startswith("TOTAL EXPENDITURE")), None)
        isos = sorted(pc[(y, tot)]) if tot else []
        w, wit = 0.0, ""
        for iso in isos:
            t = pc[(y, tot)][iso]
            if abs(t) < 1:
                continue
            s = sum(pc[(y, i)].get(iso, 0.0) for i in lv[y])
            d = abs(s - t) / abs(t) * 100
            if d > w:
                w, wit = d, iso
        worstall = max(worstall, w)
        flag = "" if w < 0.1 else "   <-- CHECK"
        print(f"{y:>5}{len(sheet[y]):>6}{len(lv[y]):>8}{w:>9.4f}%  {wit}{flag}")
    print(f"\nworst reconciliation error across all years and countries: {worstall:.4f}%")
