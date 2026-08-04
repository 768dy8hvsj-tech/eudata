# Brexit: the one country that left

Added 4 August 2026. Full detail on the **Brexit** tab of `analysis.html`.

## The result

**This study cannot measure the trade effect of Brexit.** That is a finding, not a failure to
try, and it is worth more than the number I nearly reported.

## What happened

Every other result in the project runs one direction — countries joining. The UK is the single
observation pointing the other way, so if membership does what the trade finding says, leaving
should show up in the same place.

Two dates matter. The June 2016 referendum moved expectations; departure from the single market
was 1 January 2021. COVID sits between them, one quarter before the transition ended, so no
before-and-after comparison of the UK against itself can separate the two. Comparing against
countries living through the same calendar years can, because the pandemic hit them too.

Two control sets were used deliberately: **tight** (Denmark, Sweden — rich, western, EU members
that kept their own currency, which is what the UK was) and **broad** (adding France, Germany,
Italy, Spain, Netherlands, Belgium).

## Why it does not produce a number

Trade openness, difference-in-differences, pre-window 2011–2015:

| Post-window | Tight controls | Broad controls |
|---|---|---|
| 2016–2019 | −0.8 | −1.3 |
| 2021–2025 | **−18.1** | **−9.0** |
| 2023–2025 | **−21.3** | **−7.3** |
| 2011–2015 *(placebo)* | +3.1 | −2.5 |
| 2013–2015 *(placebo)* | +2.1 | −4.2 |

The estimate is **stable against the choice of years** — dropping the 2022 energy spike barely
moves it, which killed my first hypothesis that the spike was doing the work. It is **not stable
against the choice of comparators**: 21 points of GDP against Denmark and Sweden, 7 against the
eight-country set. A result that swings threefold on which handful of countries you nominate is
not measuring Brexit.

Both routes then fail the checks this study applies everywhere else. The tight set has two
countries, below the three-control minimum. The broad set has a placebo of −4.2 against an
effect of −7.3 — more than half the estimate is present in years before the referendum.

## The plainest look

Trade openness in 2025 against the same country's own 2019 level, percentage points of GDP:

| Denmark | Sweden | Italy | Spain | France | Germany | **UK** | Netherlands | Belgium |
|---|---|---|---|---|---|---|---|---|
| +17.3 | +11.6 | +3.8 | +3.1 | +0.8 | −0.6 | **−2.5** | −10.6 | −12.5 |

**The UK is not the outlier.** It sits between Germany and the Netherlands. Denmark and Sweden —
the tight control set — are the two countries behaving unusually, and building a counterfactual
out of them is what generated the large negative estimate.

## What the referendum window does show

2016–2019 is the clean window: no COVID, no energy shock, UK still a full member. Across all six
measures the differences are small, around a percentage point either way, and inconsistent in
sign. The four years after the referendum are not distinguishable from an ordinary period for a
large European economy. That says nothing about what departure itself did.

## What would settle it

**Bilateral trade data.** Total trade openness mixes EU and non-EU trade together, so it cannot
see the thing Brexit changed: trade *with the EU specifically* against trade with everyone else.
Not in this dataset. Collecting UK–EU and UK–rest-of-world trade separately is the single change
that would turn this from unanswerable into answerable.

Also worth checking before any future attempt: whether the UK's post-2021 trade statistics have
a methodology break from the switch in how EU imports are recorded. Exports and imports move
together in the series here, which is mild evidence against a one-sided recording change, but it
has not been verified against a source.
