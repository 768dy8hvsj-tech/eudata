# Comparative analysis & regional structure

Updated 4 August 2026. Pages: `start-here.html` (front door), `index.html` (regional
comparison, 14 measures), `analysis.html` (the causal argument, 12 tabs), 31 country pages.

## Two groupings, two jobs — this is deliberate, not an inconsistency

**Seven regions** (`data/regions.csv`) structure the *descriptive* comparison page.
Continental core (7: founding six + Austria), Nordic (3), British Isles (2),
Mediterranean (5), Visegrád (4), Baltic (3), South-East (4).

**Three blocs** (`data/blocs.csv`: West / South / East) structure the *causal* analysis,
because each bloc is matched to a real non-member control group. Regions of 2–4 countries
cannot carry difference-in-differences estimates with useful precision.

## What survives the checks — the short version

Every estimate is run twice: once over the real accession windows, and once entirely over
pre-accession years as a **placebo**. If the placebo already reports an effect, the groups
were drifting apart before anyone joined and the headline figure is not attributable to
membership. Of 30 estimates attempted, **four clear every check.**

| Outcome | Bloc | Estimate | 95% interval | Placebo | Unanimity |
|---|---|---|---|---|---|
| Trade openness | East | **+20.5 pp of GDP** | +14.3 to +26.7 | +0.6 | 11 of 11 |
| FDI inflows | East | **−3.1 pp of GDP** | −5.2 to −1.0 | −0.2 | 1 of 11 positive |
| FDI inflows | West | **+1.0 pp of GDP** | +0.2 to +1.8 | +0.4 | 5 of 6 |
| Unemployment | East | +1.4 pp (null) | −0.6 to +3.4 | −0.0 | not distinguishable from zero |

**Trade openness is the strongest result in the study.** All eleven Eastern members are
above their Western Balkan control group — no single country carries the average — and the
pre-accession placebo reports essentially nothing. It does **not** follow that people became
better off; that is the income question, and the income question remains unresolved.

Persistence check at t+11 to t+15: trade East falls to **+13.7pp** — persists, roughly a
third weaker. The shape of a level shift that partly erodes. FDI East holds at −2.7pp.

The **Eastern FDI result is negative and counter-intuitive**: post-communist members
received *less* FDI relative to GDP than Balkan non-members over the same windows. Treat it
as real but narrow — the Balkan comparators were privatising state assets from very low
bases during exactly these years.

## What the placebo killed

- **Tourist arrivals (East), raw −90%.** The Western Balkan controls roughly quadrupled
  arrivals while recovering from war. Placebo −34.7, interval excluding zero. Never quote it.
- **Income per head, all three blocs.** The placebo is as large as the headline — the
  beta-convergence confound.
- **Net migration, East and West.** Groups were already diverging pre-accession.
- **Everything in the South bloc.** Turkey is the only available control.
- **Rule of law, voice and accountability, control of corruption.** See
  `claude/legal-political-scope.md` — the raw comparisons look negative for members and are
  confounded by headroom on a bounded scale. Rule of law adjusted: **+0.04, indistinguishable
  from zero.**

## A demotion worth recording

The project's previous headline — Eastern members closed **+5.5pp** on the EU average
versus non-members — is marked *indicative* rather than a finding. Its placebo is +1.4 with a
95% lower bound of **+0.008**, clearing the threshold by a hair. Netting the pre-trend off
leaves **+4.1pp**, essentially the median anyway. Only the label changed.

## The regional table — GNI convergence, median per region, 1996 → 2025

| Region | 1996 | 2025 | Change |
|---|---|---|---|
| Baltic | 35.0% | 78.8% | **+43.8pp** |
| South-East | 36.3% | 76.7% | **+40.4pp** |
| Visegrád | 50.6% | 77.5% | **+26.9pp** |
| British Isles | 109.8% | 130.9% | +21.1pp |
| Mediterranean | 88.0% | 88.1% | +0.1pp |
| Nordic | 127.2% | 116.8% | −10.4pp |
| Continental core | 132.2% | 118.2% | −14.0pp |

> **⚠ CORRECTED 4 August 2026.** This section previously called the Mediterranean's +0.1pp
> "the striking result" of the whole project. That interpretation was **wrong** — see
> `claude/south-findings.md`. The number is a **median artefact**. Underneath it Malta gained
> 18.1pp, Spain +0.4, Portugal −1.9, Cyprus −2.0, **Greece lost 20.0pp**, and Italy —
> classified Continental core, so invisible in this table — **lost 28.6pp**, the largest
> single reversal in the dataset. Four of the five southern members converged and then
> reversed, peaking between 1999 and 2009. Averaging that produces a flat line describing no
> country in the group.

The negative figures for Continental core and Nordic are largely mechanical: the EU average
itself rises as poorer members catch up, so a rich region can decline while still growing.
The same caution now applies to **every** median in this table — they compress real
divergence, and the Mediterranean row is where that mattered most.

## The demographic caveat that applies to every convergence number

Income per head is total output divided by population, so it moves when either half moves.
Across 1996–2025 the direction differs systematically by region:

- **East, shrinking:** Latvia −24.8% population, Bulgaria −23.1%, Lithuania −19.8%. Between
  17% and 29% of their measured gain in output per head is the denominator falling.
- **South, growing:** Cyprus +55.7%, Malta +52.6%, Spain +23.7%. Population growth *held down*
  their per-head figures.

**Cyprus and Latvia grew their total real economies by 169% and 163% respectively over the
same twenty-nine years — within six points of each other. Per head, Cyprus shows +73% and
Latvia +250%.** The entire difference is demography. Income per head remains the right measure
for most questions, but no chart in this project currently says this, which is a live gap.

## The fourteen measures, grouped by lens

**Financial** — GNI convergence (default), GNI per capita PPP, long-term bond yield, net
annual earnings, GDP convergence. **Commercial** — trade openness, FDI, tourist arrivals.
**Social** — unemployment, net migration per 1,000, Gini. **Legal** — rule of law.
**Political** — voice and accountability, control of corruption.

Caveats that travel with them:

- **Trade openness** exceeds 100% routinely and that is not an error — a component crossing
  a border three times is counted three times. Good measure of integration, poor measure of
  size. Luxembourg exceeds 375%.
- **FDI** in Luxembourg, Malta, Ireland, Cyprus and the Netherlands is dominated by
  special-purpose entities routing capital onward. Cyprus alone scores +173pp on the raw DiD,
  which is why the South FDI *mean* (+41.3) is worthless and the *median* (+0.5) is honest.
- **Tourism** ends 2020 everywhere. Croatia counts border crossings, not overnight stays.
- **Net migration** is per 1,000 residents; these are modelled estimates, not counts.
- **Gini** is survey data at irregular intervals. A missing year means no survey.
- **Governance indices** are expert perceptions on a bounded −2.5…+2.5 scale, so a country
  near the top has less room to rise. Compare levels rather than small movements.

## Why GNI, not GDP

**Luxembourg and Ireland both show GDP exceeding GNI by ~47%** — profit-shifting and IP
relocation, not income reaching residents. On GDP both sit near 238% of the EU average, which
broke their own regional aggregates: within-region spread was 143pp (Continental core) and
138pp (British Isles). Switching to GNI roughly halved those to 67pp and 65pp.

Region aggregates additionally use the **median**, robust to a single extreme member — with
the caveat recorded above about what medians hide.

## Chart form

The all-regions tab draws all seven legibly and lights the line nearest the cursor; each
*region tab* compares the countries inside that region — EU members solid blue, non-EU
neighbours dashed orange — with the same hover emphasis. Crisis episodes are shaded on every
chart, with the European-only 2011–13 episode tinted differently from the two global ones.

Three chart bugs found and fixed: an explicitly-coloured first series made the second default
to the same hue; change tiles reported "−0.2" above "0.70 → 0.60" because the change was
computed unrounded while endpoints were rounded; and on the all-regions tab every line was
drawn in the de-emphasis grey, since the emphasis pattern had nothing to emphasise.

## Verification

`audit.js` walks every chart on every page checking for illegible states. Current state:
0 ghost charts, 0 country dashboards flagged, no JS errors.

- 16,465 plotted points on `index.html` checked against `data/indicators.csv`, including
  region medians recomputed members-only and display scaling — 0 mismatches.
- 15,931 plotted points across all 28 country dashboards — 0 mismatches.
- 8 tabs × 14 measures exercised; all 30 internal links resolve.
