# The EU in the world

Added 4 August 2026. Full detail on the **In the world** tab of `analysis.html`.

## The methodological fact that has to come first

The World Bank's "European Union" aggregate is **EU27 applied retroactively**. Its population
matches the sum of today's twenty-seven members *exactly* in 2000, 2010 and 2016 — years when
the UK was still a member. The aggregate never contained the UK.

Two consequences: no decline in it can be a Brexit artefact, and it is a constant basket of
countries rather than the Union as it stood at the time. Right for a like-for-like trend, wrong
for asking how the Union's weight changed as it grew. Both versions are built.

## Share of world output, 1990 → 2024

| Measure | EU27 | United States | China |
|---|---|---|---|
| **Market exchange rates** | 28.0% → **17.5%** (−10.5pp) | 25.9% → 26.2% (**+0.3pp**) | 1.6% → 16.8% (+15.2pp) |
| **Purchasing power parity** | 20.4% → **14.4%** (−6.0pp) | 20.1% → **14.7%** (−5.4pp) | 3.8% → 19.1% (+15.4pp) |
| **Population** | 7.9% → 5.5% (−2.4pp) | 4.7% → 4.2% | 21.4% → 17.3% |

**The measure changes the answer.** At market rates the EU nearly halved while the US held
steady — a striking gap. In PPP terms the two declined by 6.0 and 5.4 points respectively and
are barely distinguishable. **That is the rise of Asia, not a specifically European decline.**

Market-rate shares also move with the euro–dollar exchange rate, which is why the EU line dips
in 2000 when the euro was weak and peaks in 2005 when it was strong. PPP is the better measure
of real economic weight.

And roughly **a quarter of the EU's PPP decline is demographic** before any economics enters:
Europeans went from 7.9% of humanity to 5.5%.

## The finding that runs against the received view

**GNI per capita at PPP, as a percentage of the United States:**

| | 1995 | 2024 | Change |
|---|---|---|---|
| EU27 (World Bank aggregate) | 62.1% | 74.6% | **+12.5pp** |
| Old 14 (pre-2004 members, ex-UK) | 74.1% | 79.7% | **+5.5pp** |
| New 13 (joined 2004 onward) | 28.9% | 57.8% | **+28.9pp** |

On living standards the EU has been **closing** the gap with the United States, not falling
behind. The obvious suspicion is composition — that the aggregate only rises because poor new
members joined and converged. Checked directly: **that is not the whole story.** The old
fourteen gained 5.5 points too. Both halves closed the gap.

*Caveat:* PPP conversion factors are rebenchmarked periodically by the International Comparison
Program and levels shift when they are. The direction is consistent across three decades and
three separate groupings, which is more robust than any single year's ratio.

## The Union as it actually was

Share of world GDP counting only the countries that were members that year:

| Year | Members | Share |
|---|---|---|
| 1990 | 12 | 29.4% |
| 2000 | 15 | 25.1% |
| 2005 | 25 | 29.9% |
| 2019 | 28 | 21.0% |
| **2020** | **27** | **17.9%** |
| 2024 | 27 | 17.5% |

Two compositional step-changes. Enlargement from fifteen to twenty-five members added roughly
five points of world GDP share. And the drop from 21.0% to 17.9% between 2019 and 2020 **is the
United Kingdom leaving** — the UK was 3.2% of world GDP in 2019 and is 3.3% today.

**This is the one Brexit number this dataset produces cleanly:** not what leaving did to
Britain, which `claude/brexit-findings.md` shows is not identifiable here, but what it did to
the Union's economic weight. About three percentage points of world output, immediately and by
construction.

## What to take from it

The claim that the EU's share of world output nearly halved is true at market exchange rates
and misleading alone. In purchasing-power terms the EU and the US declined together and were
displaced by the same thing. A quarter of the EU's decline is demography. And on the measure
closest to what a person experiences, the direction is the opposite of the story usually told.

None of this is causal about membership. It is the descriptive backdrop the rest of the study
sits inside, and a reader cannot judge the internal comparisons without it.

## Data added

`NY.GDP.MKTP.CD`, `NY.GDP.PCAP.PP.CD`, `NY.GNP.PCAP.PP.CD`, `SP.POP.TOTL` for **WLD, USA, CHN**
— 612 rows, 1960–2025 (PPP series begin 1990). Store now 38,832 rows, 46 entities.
