# Project status — 6 August 2026

## Where it stands

All five lenses carry data. Beyond the original brief, six further questions have been
answered or explicitly closed as unanswerable.

**Data store: 45,096 rows · 46 entities.** Sources: World Bank (WDI + Worldwide Governance
Indicators), Eurostat, ECB, European Commission (budget workbook), plus verified milestone
and metadata tables.

**Pages:** `start-here.html` · `index.html` (7 regions × 14 measures) · `analysis.html`
(10 tabs) · 28 country pages.

## Findings that survive every check

| Outcome | Bloc | Estimate | 95% interval |
|---|---|---|---|
| Trade openness | East | **+20.5 pp of GDP** | +14.3 to +26.7 |
| FDI inflows | East | −3.1 pp of GDP | −5.2 to −1.0 |
| FDI inflows | West | +1.0 pp of GDP | +0.2 to +1.8 |
| Unemployment | East | +1.4 pp (null) | −0.6 to +3.4 |

Four of thirty attempted. Trade persists at **+13.7pp** at t+11–15 — a level shift that
partly erodes.

## The other questions, and their answers

- **Crises** (`crisis-findings.md`) — the 2012 downturn was **European, not global**: 61% of
  members contracted against 23% of non-members, where 2009 and 2020 hit both alike. GFC:
  members fell deeper and recovered slower, but the recovery gap is largely a rich-vs-poor
  effect (income r²=0.28). COVID: **no difference at all**, which disciplines the GFC result.
- **Brexit** (`brexit-findings.md`) — **not identifiable**. The estimate swings from −7 to
  −21pp depending on comparator choice; both routes fail the project's own checks. Needs
  bilateral trade data.
- **The South** (`south-findings.md`) — the "Mediterranean flatline" was **my error**, a median
  artefact. Malta +18.1, Greece −20.0, Italy −28.6. Bond spreads to Germany collapsed to near
  zero by 2007 and every income peak sits inside that window.
- **In the world** (`world-findings.md`) — at market rates the EU nearly halved while the US
  held steady; **in PPP terms both fell by ~6 points**. On income per head the EU has been
  *closing* the gap with the US, old members included.
- **Who gains** (`who-gains.md`) — the four synthesis questions. Measured against a fixed
  external benchmark (US income per head, PPP) over one common window, Eastern members gained
  a median **+29.4 points** against the Western Balkans' **+18.1** — gap **+10.3pp**, interval
  +5.1 to +15.5, placebo **+0.1**. The catch-up objection was tested and fails: starting income
  explains 1% of the variation and members started *richer*. Question 3 (who loses by staying
  out) is **structurally unanswerable** — it needs a counterfactual for countries that never
  entered. Question 4 is **not empirical**.
- **The money** (`money-findings.md`) — accounting, not estimates. **Belgium moves from +€92bn
  to −€70bn** depending on convention. Validated against Poland's independently published
  €161.8bn to within 1.8%. Whether the money bought convergence is **not answerable**:
  receipts and convergence are each 71% explained by starting income.

## Method machinery built

Pre-accession **placebo** on every estimate; **headroom adjustment** for bounded indices;
**convergence adjustment** for income; r²≥0.5 identification gate; coverage rule that adapts
to publication frequency; `audit.js` checking every chart on every page; harnesses verifying
every plotted point against the CSV.

## Known gaps

- **Population decomposition not on the convergence charts.** It lives in the South tab and
  the docs only. A casual reader still gets an incomplete picture: 32% of Latvia's measured
  gain is population decline; Cyprus and Latvia grew total output 169% vs 163% but show +73%
  vs +250% per head.
- WGI `RQ.EST`, `GE.EST`, `PV.EST` not collected — straightforward repeat of the same run.
- OECD wages and Better Life Index — blocked on gzip transport.
- CJEU references, transposition deficit, EP turnout, Eurobarometer — never reached.
- WGI annual renormalisation and the 2025 methodology revision remain unverified. Neither
  affects the causal estimates (common year effects difference out); both affect descriptive
  reading of a single country's line.

## Two specifications on income, and both are reported

The event study says the income effect is not demonstrable. The fixed-window comparison on the
Who gains tab says +10.3 points. Both are in the data. The event study measures the accession
*step* (t+6..t+10 against t−5..t−1, so 2010–2014 against 1999–2003 for the 2004 wave) and stops
a decade short of today; netting its own placebo off leaves +2.5, same sign, not significant.
The calendar comparison measures the twenty-five-year trajectory including the run-up. Neither
was chosen over the other.

## Permanent limit

The six founding members can never be tested causally. They joined in 1958; usable income
data begins in 1960 and WGI in 1996.
