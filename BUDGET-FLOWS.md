# What each country pays in, and what comes back — by fund

Written 6 August 2026. Page: `flows.html`. Builders: `extract_detail.py` → `tree.py` →
`build_flows.py`. Verifiers: `verify_flows.py` and `sf.js`.

Source: European Commission, *EU spending and revenue 2000–2024* (workbook published
25 September 2025). 63,709 extracted rows, 233 distinct budget lines, mapped onto 15 funds
and 5 revenue sources for 28 member states across 25 years.

**Nothing here is estimated.** This is the accounting layer of the project. The only work
done to the Commission's figures is arithmetic, and the arithmetic is checked to zero.

## Two problems had to be solved first

**The hierarchy is implied, not declared.** The sheets are flat lists in which some rows are
totals of other rows, so adding them up counts the same euro two or three times. Where the
workbook carries programme codes they *nearly* identify depth — but not quite: in the 2010
sheet `1.1.1` is the Seventh Research Framework Programme and `1.1.10` is Nuclear
decommissioning, a sibling rather than a child, despite one code being a string prefix of the
other. So parentage is proposed from the codes and then **tested**: a row keeps its children
only if their values sum to it. Where the test fails the children are promoted one level and
it runs again, strictly deepest-first — repairing several levels at once collapses the tree
into a flat list that triple-counts.

Before 2007 there are no codes below the eight headings, and the sheet prints the structural
funds **twice**, once split by Objective and once split by fund. No arithmetic can choose
between two correct decompositions of the same money, so that era uses an explicit list.

**The names change every seven years.** "Structural funds - Total ERDF" (2000–06),
"Convergence objective" (2007–13), "Less developed regions" (2014–20) and "European Regional
Development Fund" (2021–24) are four labels for money doing one job. The crosswalk is an
ordered list of matchers in `build_flows.py`, readable and arguable.

## Verification

| Check | Result |
|---|---|
| Recovered leaves sum to published TOTAL EXPENDITURE, every country, every year | **0.0000%** worst error |
| Mapped funds sum to published TOTAL EXPENDITURE, same test | **0.0000%** |
| Revenue sources sum to published TOTAL NATIONAL CONTRIBUTION | **0.0000%** |
| Payload re-checked against the workbook by independent code (`verify_flows.py`) | 28 countries, **0 mismatches** |
| Rendered DOM values checked against the payload (`sf.js`) | 717 values, **0 mismatches** |
| Spending matching no fund, landing in "Other programmes" | 1.4% |

The first reconciliation was initially reported as a perfect 0.000% and was **vacuous** — the
TOTAL row had been classified into the revenue block, so the check found nothing to compare
and silently passed everything. Worth recording: a check that cannot fail is worse than no
check.

## Where the money goes, Union-wide, 2000–2024

| Fund | Cumulative |
|---|---|
| Farm payments and market support | €1,037.6bn |
| Regional and social funds | €795.4bn |
| Rural development | €277.5bn |
| Administration | €179.7bn |
| Cohesion Fund | €175.9bn |
| Research and innovation | €169.2bn |
| Infrastructure, digital and space | €58.0bn |
| Education, youth and culture | €43.9bn |

Agriculture and cohesion together are **80% of everything the Union spends**. Research, the
policy area that gets the most rhetorical attention, is 6%.

## Net positions, 2000–2024

On this page's convention — receipts are all allocated expenditure, payments include customs
duties. This is the broader of the two conventions in the study and differs from the
Commission's own headline figure, which excludes customs.

| | Net €bn | % GNI/yr | € per person/yr |
|---|---|---|---|
| Poland | +168.3 | +1.87 | +212 |
| Greece | +105.8 | +2.20 | +390 |
| Hungary | +67.9 | +2.77 | +328 |
| Spain | +67.5 | +0.25 | +59 |
| Portugal | +65.4 | +1.45 | +250 |
| Romania | +59.5 | +1.77 | +167 |
| Belgium | +48.9 | +0.49 | +177 |
| Czechia | +44.5 | +1.21 | +201 |
| Luxembourg | +33.3 | +4.02 | **+2,457** |
| Slovakia | +26.5 | +1.64 | +233 |
| Lithuania | +25.0 | +3.04 | +397 |
| Bulgaria | +24.3 | +2.56 | +194 |
| Latvia | +14.7 | +2.76 | +345 |
| Croatia | +12.0 | +1.83 | +251 |
| Estonia | +10.8 | +2.43 | +385 |
| Slovenia | +6.5 | +0.75 | +151 |
| Ireland | +6.0 | +0.12 | +52 |
| Malta | +1.6 | +0.83 | +168 |
| Cyprus | +0.9 | +0.23 | +37 |
| Finland | −11.6 | −0.23 | −86 |
| Denmark | −22.8 | −0.34 | −162 |
| Austria | −22.8 | −0.28 | −107 |
| Sweden | −42.6 | −0.41 | −177 |
| Italy | −107.3 | −0.26 | −73 |
| Netherlands | −108.3 | −0.63 | −257 |
| United Kingdom | −145.9 | −0.29 | −92 |
| France | −154.9 | −0.29 | −95 |
| Germany | −345.3 | −0.47 | −168 |

**Luxembourg's +€2,457 per person per year is an artefact of hosting institutions** — 76% of
its allocated expenditure in 2023 is administrative. Belgium's +€48.9bn is the same effect at
larger scale. Neither is a transfer to residents in the sense a reader would assume.

**The asymmetry of scale is the structural fact.** Recipients take 2–3% of national income a
year; contributors pay well under 1% of theirs. The budget is roughly 1% of EU income but
concentrated enough to matter enormously at the receiving end.

## Who does well out of which fund (% of national income a year)

- **Farm payments:** Greece 1.22, Bulgaria 1.12, Lithuania 0.92, Hungary 0.90, Romania 0.73
- **Regional and social funds:** Hungary 1.55, Latvia 1.35, Lithuania 1.32, Portugal 1.30, Poland 1.21
- **Cohesion Fund:** Hungary 0.76, Latvia 0.71, Lithuania 0.69, Estonia 0.69, Poland 0.58
- **Research and innovation:** Belgium 0.19, Luxembourg 0.18, Cyprus 0.13, Estonia 0.11, Greece 0.09

Research is the one fund whose ranking inverts: it is competitive rather than allocated, and
the winners are rich small countries with dense university and institutional sectors, not the
cohesion recipients.

## Four caveats that travel with every figure

1. **"Received" means allocated expenditure, not a cheque to the government.** A Horizon grant
   to a university, a farm payment to a landowner and a co-financed road all count, and all
   reach different hands.
2. **"Paid in" includes customs duties.** The Commission treats duties collected at the
   external border as the Union's own revenue and excludes them from its headline figure.
   They are included here, which is why these net figures differ from the Commission's.
3. **ERDF and ESF cannot be separated between 2007 and 2020.** The workbook reports them
   together under objective headings in those years and separately before and after. One
   combined line is carried across all 25 years rather than a split that silently changes
   meaning twice.
4. **Every figure is nominal.** Rankings and shares are unaffected; a per-person figure
   spanning the whole period is not comparable to a price today.

A net position is also not a verdict. Money paid into a shared budget buys things that never
come back as budget lines — a market to sell into, the removal of border checks, a common
regulatory regime. Whether that trade is worth it is the question `who-gains.md` addresses,
and the answer there is that the accounts cannot settle it.
