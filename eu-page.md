# The Union itself

Written 6 August 2026. Page: `eu.html`. Built by `build_eu.py` from `data/eu_stats.csv`,
`flows_payload.json` and `analysis_payload.json`. Checked by `audit_eu.py`.

Every other page in this study looks at one country. This is the first that looks at the thing
they are members of. It carries six headline figures, the trade picture, the budget, and the
Union's position in the world — each with the dataset and vintage it came from, because three
different provenances meet on this page and mixing their vintages silently would be the easiest
way to get it wrong.

---

## The headline figures

| | | |
|---|---|---|
| Gross domestic product | **€18.8 tn** | Current prices, 2025, flagged by Eurostat as an estimate. `nama_10_gdp` |
| Population | **452.0 m** | 1 January 2026, estimated, up 706,000 on a year earlier. `demo_gind` |
| In the euro area | **21 of 27** | Bulgaria joined 1 January 2026 and is the twenty-first |
| HICP inflation | **2.9%** | June 2026, down from 3.3% in May. Euro area 2.8%. `prc_hicp_manr` |
| Unemployment | **6.0%** | June 2026, seasonally adjusted — 13.317 m people. Euro area 6.3%. `une_rt_m` |
| ECB deposit facility rate | **2.25%** | Raised 25bp on 11 June 2026, the first rise after the 2025 cutting cycle; held 23 July |

---

## The finding worth leading with

**Most EU trade is internal, and this reframes every partner ranking.**

Counting each intra-EU consignment once: intra-EU goods trade is **€4,142.9 bn** against
**€5,156.5 bn** with the rest of the world, so **44.6%** of the Union's goods trade is between
its own members. Eurostat's per-country tables count that trade twice — once as a dispatch,
once as an arrival — which puts the same fact at **61.6%**.

Both conventions are defensible and they are not the same number. Eurostat publishes no
EU-level intra share at all, so any figure quoted is derived. The page therefore shows the
underlying values and names both conventions rather than picking one silently.

The consequence is that the partner league table below — the United States, China, the United
Kingdom — is a ranking of the *smaller half* of EU trade. That is not how it is usually
presented.

---

## The largest trade pools

Goods, 2025, EUR bn. Source: DG TRADE factsheet on Eurostat COMEXT, statistical regime 4,
extracted 20 May 2026.

| Partner | EU exports | EU imports | Total | Balance |
|---|---|---|---|---|
| United States | 554.6 | 356.2 | **910.8** | **+198.4** |
| China | 199.4 | 560.0 | **759.4** | **−360.6** |
| United Kingdom | 345.3 | 158.7 | **504.1** | +186.6 |
| Switzerland | 219.4 | 143.2 | **362.6** | +76.3 |
| Türkiye | 114.2 | 103.3 | **217.5** | +10.8 |
| Norway | 64.0 | 95.7 | **159.7** | −31.7 |
| Japan | 65.8 | 63.3 | **129.1** | +2.4 |
| South Korea | 54.5 | 69.7 | **124.3** | −15.2 |
| India | — | 69.5 | 118.4 | not published |
| Brazil | — | — | 87.1 | not published |

**Three things stand out.**

The two poles are the United States and China, and they point in opposite directions: the
Union runs its largest goods surplus with the country it trades with most, and its largest
deficit with the country it buys most from. Everything else is small beside them.

**The United Kingdom is still the third largest partner six years after leaving**, and the
second largest destination for EU exports. Whatever Brexit changed, it did not change who the
EU sells to.

**Switzerland, a country of nine million, is the fourth largest goods partner** — a larger
relationship than Japan and South Korea combined. This belongs beside the finding on the
non-member pages that Norway sends 67.5% of its exports to the EU. The countries that chose not
to join are among the Union's largest trading partners.

India and Brazil are not drawn in the ranked chart. The factsheet publishes only one flow for
India and neither for Brazil, and a chart that ranks on the sum of two flows cannot honestly
draw a partner with one. Their totals are stated instead.

---

## Where the Union's outside exports go, 2002–2025

Share of extra-EU goods exports by destination region. Over twenty-three years the largest
shifts are **Asia +4.4 points** and **Rest of Europe −6.0 points**. The single structural
movement in the period is toward Asia and away from non-EU Europe.

Latest year: Rest of Europe 34.0%, the Americas 28.8%, Asia 27.0%, Africa 6.3%, Oceania and
polar 1.9%, unallocated 2.0%.

**A trap worth recording.** The regional series contains three subsets masquerading as peers.
North America *and* Latin America both sit inside the Americas — and they overlap each other,
since 24.8% + 5.7% exceeds the Americas' own 28.8%. Drawing all seven inflated the chart to
**104%**. Only the five top-level regions partition. The ~2% remainder is ships' and aircraft
stores and unallocated trade, and it is drawn rather than absorbed, which is the same treatment
the per-country destination charts already give it.

---

## The budget

Every euro of EU spending allocated to a member state, 2000–2024, parsed from the Commission's
own budget workbook into 15 funds. The parse reconciles to the Commission's totals to 0.0000%.

Farm payments and market support **€1,038 bn (36.2%)**; regional and social funds **€795 bn
(27.8%)**; rural development €278 bn (9.7%); administration €180 bn (6.3%); the Cohesion Fund
€176 bn (6.1%); research and innovation €169 bn (5.9%).

**Agriculture and cohesion together are 64.0% of all EU spending.** Adding rural development
and the Cohesion Fund — which are the same two policies under different headings — takes it to
just under 80%. Research, the thing the Union most often talks about, is 5.9%.

The two ends of the distribution are Germany at roughly −€345 bn net over the period and Poland
at roughly +€168 bn. The full per-country picture is on `flows.html`.

---

## The Union in the world

| | | |
|---|---|---|
| Share of world exports | **17.0%** | 2024, goods and services, current prices. China 14.4%, up from 12.5% in 2014 |
| Share of world imports | **15.1%** | 2024. United States 16.1%, up from 15.0% in 2014; China 12.7% |
| Trade as a share of EU GDP | **21.4%** | 2024 |
| Share of world GDP | **15.2%** | 2021, purchasing power standards, World Bank ICP round. China 18.9%, United States 15.5% |

---

## What is not on this page, and why

**Services trade.** Extra-EU services trade is large enough that a goods-only page understates
the Union's trade substantially. A 2024 figure was located but could not be confirmed to this
study's confidence bar as extra-EU rather than total, so no number appears. **Everything on the
trade sections is goods only**, and that is a real limitation rather than a rounding one.

**A recent share of world GDP at current prices.** The only credited figure obtainable is the
15.2% PPS figure above, for 2021. No current-price equivalent and no comparable figure for 2000
could be sourced, so the trajectory is shown through trade shares instead. **The widely
circulated claim that the EU's share of world GDP fell from about 30% to about 17.5% appears
only on non-credited sites and is deliberately absent from this page.**

**Ranks 11 and 12 among partners.** The DG TRADE factsheet table stops at ten. Canada does not
appear in any top-ten column; Mexico and Vietnam appear in single-flow columns only.

**One consistent trade vintage.** Three credited figures exist for the 2025 extra-EU balance —
€133.5 bn from the 13 February 2026 release, €128 bn from a 26 March news item, €126.1 bn from
the 20 May COMEXT extract. The totals here use the February release and the partner detail uses
the May extract. The difference is revision, not error, and both vintages are stated on the
page.

**Euro area GDP in euros.** No credited source giving an EA20/EA21 nominal level was found.

**A note on aggregate codes.** Eurostat's June 2026 unemployment and trade releases still use
EA20 for some series while the July HICP flash uses EA21. Any future pull should check which
vintage a series key returns.

---

## Verification

`audit_eu.py` checks that every stated figure traces back to `data/eu_stats.csv` and carries a
source; that the intra/extra split, both share conventions and the balance recompute from the
trade rows; that every partner total and balance follows from its two flows and the ranking is
by total; that the fund shares partition to 100 and the payers and receivers are the right way
round; and that the regional shares partition to 100 each year with no subset drawn beside its
parent. It found the 104% chart on its first run.

Site-wide at the time of writing: 31 country pages, 606 charts, 135 lens analyses, 9,108
milestone markers, 0 failures; `xref.py` 0 cross-reference issues; `audit_nm.py` 0 problems;
`audit_eu.py` 0 problems.
