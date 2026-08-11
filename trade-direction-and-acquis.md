# Trade direction, the acquis overlap, and what joining would change

Written 6 August 2026. Pages: the **Trade direction** tab in `analysis.html`; the coverage grid
and joining case on the three non-member pages. Data: `data/raw/_trade_partners.csv` (1,470
rows, Eurostat), `data/acquis_coverage.csv` (25 policy areas).

## 1. Membership made them trade more. It did not make them trade differently.

This is a new finding and it sharpens the study's strongest result rather than competing with
it. Every other trade measure here asks *how much* a country trades. This one asks *who with*.

| | Effect of accession |
|---|---|
| Trade **openness** (exports + imports, % of GDP), East | **+20.5pp**, 11 of 11 positive, placebo +0.6 |
| Share of exports going to the **EU**, 2004 wave | **−0.3pp** (median of 10, range −12.2 to +11.8) |
| Same, 2007 wave | +3.1pp (n=2) |
| Same, 2013 (Croatia) | +6.7pp (n=1) |

The reason is that the reorientation had already happened. The Europe Agreements opened free
trade with the Community through the 1990s, so two years before entry **Czechia was sending
80.5% of its exports to the EU, Hungary 80.7%, Slovakia 87.7% and Poland 76.3%.** There was very
little direction left to change. Accession raised the volume of trade; the destination was
already fixed.

**The three non-members are not trading elsewhere either.** Norway sends **67.5%** of its
exports to the European Union — a higher share than Germany (55.9%), France (53.7%) or Italy
(51.3%). Iceland 63.2%. Switzerland reads 40.0%, partly because the Eurostat totals include
non-monetary gold, which flows to the UK, US and Asia; Swiss national figures excluding gold run
substantially higher. Being outside the Union has not made these countries trade with the rest
of the world instead. It has left them trading overwhelmingly with the Union, from outside it.

**Where the Union's own extra-EU exports go**, 2002 → 2025: Rest of Europe 40.0% → 34.0%
(−6.0pp), Asia 22.6% → 27.0% (+4.4pp), the Americas 27.6% → 28.8%, Africa flat at 6.3%. The
single largest shift in twenty-three years is toward Asia and away from non-EU Europe.

Source: Eurostat `ext_lt_intratrd` and `ext_lt_maineu`, EU27 (2020) definition applied to every
year — so the UK counts as outside throughout, which is why Norway reads 59.2% in 2015 rather
than the ~75% often quoted against EU28.

**What could not be obtained:** a per-country breakdown by world region. No accessible dataset
has it — Eurostat's per-member-state tables carry only EU27 / extra-EU / world, and the
continent-partner dataset exists only at EU27 level. The UK is absent entirely from the
Eurostat share series. Direct HTTPS from this container is blocked for every external host;
Eurostat via the fetcher was the only usable route.

## 2. The overlap in legislation, drawn rather than counted

*How much EU law applies to a non-member?* has no honest single number. The quoted figures vary
wildly because they depend entirely on what is being counted — EFTA's own EEA-Lex tracker reads
**9,164 EU acts incorporated into the EEA Agreement and in force**, against 5,421 incorporated
and since lapsed, so roughly 14,600 have been part of the Agreement at some point (retrieved
6 August 2026). So the pages draw the map instead: 25 policy areas, three columns (EU member,
EEA, Swiss bilaterals), each cell full / partial / none, with a note per column.

*Correction, 6 August 2026:* an earlier version of this document reported the tracker the other
way round — "more than 9,500 acts ever part of the Agreement, around 5,000 in force". The
figures above are what EEA-Lex publishes today. The error was caught by the non-member page
audit, `audit_nm.py`.

| | Applies in full | In part | Not at all |
|---|---|---|---|
| **Norway and Iceland** (EEA) | 15 of 25 | 0 | 10 |
| **Switzerland** (bilaterals) | 3 of 25 | 8 | 14 |

Inside the EEA: all four freedoms, competition and state aid, public procurement, consumer
protection, company law, employment and social policy, environment, energy, statistics, research
and education programmes, Schengen. Outside: agriculture, fisheries, the customs union, the
common commercial policy, monetary union, foreign and security policy, wider justice and home
affairs, and both sides of the budget.

**The decisive row is the last one.** EEA states adopt single-market law with no seat in the
Council and no members of the European Parliament. There is consultation at the drafting stage
and a formal right of reservation that has never been used to block an act outright.

Switzerland's shape is different rather than smaller: free movement of persons and Schengen in
full, but no consumer, company, employment or energy law at all, and market access in services
and capital resting on equivalence decisions the EU can withdraw — as it did in 2019.

Sources: European Parliament research service briefing on EU–Norway relations (2025), the EEA
Agreement's own structure, EFTA, and the Swiss Federal Department of Foreign Affairs.

## 2a. The five exclusive competences — a second, sharper cut

The 25-area map answers "how much of the rulebook applies". It does not distinguish between the
areas a non-member could in principle reach by agreement and the ones it could not. That
distinction is in the Treaties: **Article 3(1) TFEU** lists five areas where only the Union may
act. Everything else is shared or supporting, and can be approximated by treaty — which is
exactly what the EEA and the Swiss bilaterals do.

| | Norway | Iceland | Switzerland |
|---|---|---|---|
| Customs union | outside | outside | outside |
| Competition and state aid | **applies in full** | **applies in full** | in part (air transport only) |
| Monetary policy | cannot apply | cannot apply | cannot apply |
| Conservation of marine resources | outside | outside | cannot apply |
| Common commercial policy | outside | outside | outside |

Four values rather than three, deliberately: *cannot apply* is not *outside*. Switzerland has no
marine fisheries competence to be outside of, and monetary policy is an exclusive competence
only for states whose currency is the euro, so it is structurally unavailable to a non-member
rather than declined. Collapsing those into "outside" overstates the distance.

Full treatment, with the depth measures and the live 2026 argument for each country, is in
`competence.md` and on the competence card on all three non-member pages.

## 3. Where membership would change something, and where it would cost

Derived from that map rather than asserted: an area already applying in full would not change on
joining; one applying partly or not at all would.

**Would gain.** A vote on rules it already follows — the largest single change, and not a matter
of degree: 15 of 25 areas already apply in Norway in full, adopted, enforced and litigated,
with no franchise over any of them. Joining would not extend the rulebook much; it would extend
the vote over it. Second, the areas currently held by renewable concession rather than treaty
right — Switzerland lost stock-exchange equivalence in 2019 and medical-device recognition in
2021, and spent four years outside Horizon Europe. Third, the customs union: no non-member is in
it, so every consignment carries rules-of-origin paperwork even at a zero tariff.

**Would give up.** A net contribution, and a large one: the budget key is GNI-based and these
are the richest countries in the comparison — Norway at 120.4% of US income per head against
Germany's 87.3%, and Germany pays 0.47% of national income a year net. *No published estimate of
what Norway would pay exists and this project does not manufacture one*, but the direction is not
in doubt, and the cohesion and farm funds it would pay into are closed to it now. Then fisheries
— the single reason membership has never been settled in Norway or Iceland, since quota-setting
would move to Brussels — and agricultural protection higher than the CAP allows in all three.
Then real trade-policy autonomy, and for Switzerland a neutrality that sits outside the common
foreign and security policy by constitutional choice.

**None of this is a recommendation and none of it is measured.** It is a list of what would
change. Whether the trade is worth taking depends on how a country weighs a vote against a
fishing quota, and no dataset settles that.

## Two chart defects fixed in passing

The signed-formatter bug returned — a share of 40% rendering as "+40%" — on the region chart's
axis, end labels and table. And the 30-country direction chart was drawn entirely in the
de-emphasis grey, legible only under the cursor: the same ghost-chart pattern this project
fixed once before on the regional comparison page. Members now read light blue and non-members
dashed orange at rest, with hover emphasis on top.

## Verification

31 pages, 606 charts, 9,108 milestone and dispute markers, 135 lens analyses, every plotted
point checked against `data/indicators.csv`, 0 failures, no JS errors. `xref.py` 0
cross-reference issues; `audit_nm.py` 0 problems across the three non-member pages.
