# The money: who pays, who receives

Added 4 August 2026. Full detail on **The money** tab of `analysis.html`.

Source: European Commission, *EU spending and revenue 2000–2024* workbook, published
25 September 2025. Supplied by the user as a file — the Commission distributes it only as a
binary .xlsx, which the available fetch tooling cannot decode.

## Why this section is different

Everything else in this study is inference with intervals and gates. **Budget flows are
accounting.** The Commission publishes what each member state paid in and what was spent in
it, every year since 2000. There is no identification problem.

What is contested is not the numbers but the arithmetic done on them.

## Two conventions, and they are not close

- **Commission** = allocated expenditure − national contributions. National contributions
  exclude customs duties, which the Commission treats as the Union's own revenue.
- **Broad** = (expenditure − administration) − (contributions + customs duties). Strips
  administrative spending, which is booked to whoever hosts the institutions.

Cumulative net position, € billion, the eight countries the choice moves most:

| Country | Commission | Broad | Difference |
|---|---|---|---|
| **Belgium** | **+91.8** | **−69.5** | 161.3 |
| Germany | −259.4 | −366.9 | 107.5 |
| United Kingdom | −89.3 | −160.3 | 71.0 |
| Netherlands | −55.0 | −119.4 | 64.4 |
| Italy | −65.8 | −120.8 | 55.0 |

**Belgium flips from the third-largest net recipient in the Union to a net contributor.** The
whole €161bn swing is administration booked to Brussels — 54% of Belgium's allocated
expenditure in 2023, and 76% of Luxembourg's. Luxembourg moves from +€34bn to roughly zero.

Neither convention is wrong. Salaries paid to officials in Brussels are genuinely spent in
Belgium and just as genuinely not a transfer to Belgians. **Any net-contributor league table
that does not state its convention is quoting a number that could be off by nine figures.**

## Cross-check against an independent source

Poland's country page already carried a figure from SGH Warsaw School of Economics, collected
independently of this workbook: €245.5bn received, €83.7bn contributed, **€161.8bn net for
2004–2023**.

Parsing the workbook over the same years gives €178.2bn on the Commission convention and
**€164.7bn on the broad one — within 1.8%** of the published figure, the residual being data
vintage. The gap between conventions for Poland is €13.5bn, almost exactly its customs duties
over the period. The parse reproduces an independent figure once the convention is matched.

## Who pays and who receives

Average annual net position as a share of national income, broad convention, since accession:

**Receiving:** Lithuania +3.11%, Hungary +2.76%, Latvia +2.66%, Bulgaria +2.62%, Estonia
+2.38%, Greece +2.20%, Poland +1.89%, Romania +1.76%.
**Paying:** Belgium −0.72%, Netherlands −0.71%, Germany −0.49%, Sweden −0.44%, Denmark −0.37%.

Note the asymmetry of scale. The largest recipients receive **several percent** of national
income a year; the largest contributors pay **well under one percent** of theirs. The EU budget
is about 1% of EU income — small centrally, concentrated at the receiving end.

Cumulative, broad convention: Poland **+€166bn**, Germany **−€367bn**.

## Did the money buy the convergence? — not answerable here

| Relationship | r² |
|---|---|
| Net receipts vs convergence gain | 0.48 |
| **Starting income vs net receipts** | **0.71** |
| **Starting income vs convergence gain** | **0.71** |

Receipts and convergence do move together. But cohesion money is *allocated by* how poor a
country is, and convergence is *driven by* how poor it starts. Starting income explains 71% of
each, separately. **The two are downstream of the same variable and this dataset cannot
separate them.**

Two countries make the point without statistics: **Greece received 2.2% of national income a
year — sixth-highest in the Union — and lost 20 points of convergence. Ireland received 0.25%
and gained 47.**

This is not evidence that cohesion spending fails. It is the statement that a design where
treatment is assigned by the same variable that drives the outcome cannot recover an effect —
a fact about the design, not the policy. Answering it properly needs variation in funding
unrelated to income; regional eligibility thresholds are the standard route and sit below the
resolution of this country-level dataset.

## Data added

`BUDGET.EXPEND`, `BUDGET.CONTRIB`, `BUDGET.ADMIN`, `BUDGET.CUSTOMS`, `BUDGET.GNI` for 28
countries, 2000–2024 (3,480 rows), plus four derived net-position series on both conventions
including shares of the Commission's own GNI. Store now **45,096 rows**.

Parser note: the workbook's layout drifts across its 25 sheets — the header row moves, the
label column moves, and total labels gain and lose asterisks. `parse_budget.py` addresses
nothing by fixed index; it finds the header by looking for a row carrying ten or more country
codes and finds totals by matching label text. One trap: the 2022 header cell reads `LU*`
because the Commission revised Luxembourg's Horizon figure, so a strict two-letter match drops
Luxembourg from that year silently.
