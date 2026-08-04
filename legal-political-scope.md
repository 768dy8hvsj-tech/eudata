# Scope: quantifying the legal and political lenses

Drafted 2 August 2026. **Updated 3 August: Tier 1 has been collected and analysed.**
Tiers 2 and 3 remain unattempted. The blocker at the end is resolved for the World Bank API
and still stands for every other host.

> **Tier 1 outcome in one line:** rule of law, adjusted for headroom, is **+0.04 —
> indistinguishable from zero**. Voice and accountability and control of corruption carry no
> reportable estimate. The raw comparisons look negative for members and are confounded; see
> `claude/comparative-findings.md` for why.

## The reframe

The legal and political lenses were scoped as written narrative, 27 countries deep. That is
expensive mainly because prose has no mechanical verification: a chart either matches the CSV
or it doesn't, whereas a sentence about judicial independence is either sourced claim by claim
or it is pattern-matching.

Much of both lenses is countable instead. Counted, it goes into the existing store, gets the
same regional treatment, the same difference-in-differences with the same pre-accession placebo
gate, and the same point-by-point verification against the CSV. That is a different order of
cost and a much higher standard of evidence.

The trade-off is real and should be stated plainly: **numbers answer a narrower question than
prose.** "Rule-of-law perception scores fell 0.6 points" is verifiable; "the judiciary was
captured" is an interpretation the numbers support or fail to support but never establish.

---

## Tier 1 — World Bank Worldwide Governance Indicators

**The anchor of the whole proposal, and the only tier that can produce causal estimates.**

| Live API code | Indicator | Lens | Status |
|---|---|---|---|
| `GOV_WGI_RL.EST` | Rule of Law | Legal | **collected**, 41/41 |
| `GOV_WGI_VA.EST` | Voice and Accountability | Political | **collected**, 41/41 |
| `GOV_WGI_CC.EST` | Control of Corruption | Political | **collected**, 41/41 |
| `GOV_WGI_RQ.EST` | Regulatory Quality | Legal | not attempted |
| `GOV_WGI_GE.EST` | Government Effectiveness | Political | not attempted |
| `GOV_WGI_PV.EST` | Political Stability | Political | not attempted |

All require `&source=3`. The bare `RL.EST` / `VA.EST` / `CC.EST` forms are archived stubs that
resolve in the catalogue but return *"The indicator was not found."* on every data call.

Why this tier matters more than the rest combined:

1. **It runs on `api.worldbank.org`**, the endpoint this project has already pulled tens of
   thousands of rows from. No new transport risk of the kind that killed the OECD collection.
   *Confirmed, with one trap: the bare codes below are archived stubs. The live series are
   `GOV_WGI_<X>.EST` and require `&source=3`.*
2. **It covers the 13 non-EU comparators.** Every other candidate below is EU-only, which
   means it cannot answer the project's actual question — *compared to countries that did not
   join*. Without comparators there is no control group, no DiD, no placebo test.
3. It slots into the existing pipeline unchanged: 6 indicators x 41 entities, the same shape as
   the population collection that succeeded earlier today.

**Caveats that must travel with it, and two that need checking before anything is built:**

- These are **perception indices**, aggregated from expert assessments and surveys — not counts
  of legal facts. A falling score is evidence that assessors judged conditions to have worsened.
  That is meaningful and it is not the same thing as a measured event.
- **Still unverified: the rescaling question.** `www.worldbank.org` is not an approved fetch
  host and the API's own `sourceNote` is empty. It matters less than feared: difference-in-
  differences uses the same calendar windows for treated and controls, so any common annual
  renormalisation differences out and the causal estimates stand regardless. It affects only
  the descriptive reading of one country's line over time, which the chart blurbs flag.
- **Original note, retained:** WGI scores are conventionally reported on a scale
  of roughly -2.5 to +2.5 normalised against the world distribution *in each year*. If that
  normalisation is annual, a country can improve absolutely while declining on the index — the
  identical trap to "% of EU average" that already required care on the convergence measure.
  This must be confirmed from the methodology paper before any trend is presented.
- **Unverified: a 2025 methodology revision exists** (World Bank published "The Worldwide
  Governance Indicators 2025 Methodology Revision"). Whether it creates a break in series, and
  whether earlier years were restated, has to be established. Treat as a suspected break until
  checked — the same discipline applied to the Eurostat 2024 earnings break.
- **Coverage starts 1996**, so pre-accession windows exist only for the 2004, 2007 and 2013
  waves. The 1973, 1981, 1986 and 1995 accessions are untestable here, and the founding six
  remain permanently untestable as they are everywhere else in this project.

**Actual yield:** 123 series, 3,221 rows, 41/41 entities on each of the three collected
indicators — two new lens groups on the region page and charts on all 28 country pages.
RQ, GE and PV were not attempted: the API was degraded badly enough that three indicators
consumed most of a day, and the three chosen cover one legal and two political dimensions,
which was the priority. The remaining three are a straightforward repeat of the same run.

---

## Tier 2 — legal integration, EU members only

These measure something Tier 1 cannot: not *perceived* governance quality but *actual
engagement with the EU legal order*. They are the better legal indicators on the merits.

They are also **structurally EU-only** and no collection effort changes that. A non-member has
no Article 267 route to the Court of Justice and no directives to transpose. So they can be
charted, compared across members and across regions, and read against accession dates — but
they cannot be run through difference-in-differences, because no control group can exist.

- **Preliminary references to the CJEU, by member state, by year.** How often a country's own
  courts refer questions of EU law to Luxembourg — a direct measure of how deeply EU law has
  penetrated national adjudication. Confirmed to exist as annual "Statistics concerning the
  judicial activity of the Court of Justice" pages on curia.europa.eu, back to at least 2006.
  Unverified whether the per-country tables are HTML or PDF-only; PDF-only would make this
  materially more expensive.
- **Transposition deficit** — share of single-market directives not transposed on time, per
  member state. European Commission Single Market Scoreboard. Unverified whether a time
  series is published or only a current snapshot. Snapshot-only would reduce this to a single
  cross-section.
- **Open infringement proceedings** per member state per year. Same source, same uncertainty.

---

## Tier 3 — political engagement, EU members (mostly)

- **European Parliament election turnout by country**, 1979-2024. Nine elections rather than an
  annual series, but a direct measure of democratic engagement with the Union, and the falling
  EU-wide trend reversing in 2019 and 2024 is a genuinely interesting political fact. The
  Parliament publishes downloadable datasheets, which is promising. Unverified whether the
  historical elections are in the same download or only the most recent.
- **Eurobarometer: trust in the EU, and "membership is a good thing"**, per country, twice
  yearly. The single best attitudinal series available. GESIS maintains trend files on trust in
  institutions. Unverified whether a machine-readable per-country series can be retrieved
  without an academic data-service account — this is the most likely of all the candidates to
  fail on access rather than on content.
  Worth noting: enlargement-country Eurobarometer waves survey Turkey, Serbia, Albania, North
  Macedonia, Bosnia and Montenegro, so this is the **one Tier 2/3 candidate with any prospect
  of comparator coverage**, and therefore of a real causal estimate.

---

## What this buys, honestly

**It buys:** two lenses moved from "no data" to "measured", six new causal estimates subject to
the same gate everything else passed, and legal/political series on all 28 country pages and
all seven region tabs.

**It does not buy:** resolution of the contested cases. If Hungary's rule-of-law score falls
0.8 points after 2010, that is a finding about an index built from expert assessments. Whether
it constitutes democratic backsliding is an argument, and the honest presentation says so
rather than letting the number imply a verdict it cannot deliver.

**It does not replace the narrative.** Poland shows what the written version looks like and it
carries texture no index does. The proposal is to do the cheap, verifiable thing first and let
what it shows decide where prose is actually worth writing.

---

## Cost

Tier 1 is the population collection again, six times over: agents fetching one country-indicator
at a time from a flaky API, writing CSVs directly. Hours, not days, and no new failure modes.

Tiers 2 and 3 are genuinely uncertain until the sources are reachable. If the CJEU tables are
PDF-only and Eurobarometer needs an account, most of the value collapses back to Tier 1 — which
is still worth doing on its own.

**Recommendation: build Tier 1 first, then re-probe Tiers 2 and 3 with what is learned.**

---

## BLOCKER

Every fetch attempted for this scope — 15 requests across 6 hosts, including
`api.worldbank.org`, which worked earlier in this same session — returned
`PROVENANCE_REQUIRED`: *"The permission request for this URL was not answered in time."*

This is a permission gate, not a source problem. Nothing above was shown to be missing,
rate-limited, or slow; none of it was reached at all. Subagents do not inherit provenance, so
delegating does not route around it. WebSearch still works, which is where the catalogue
evidence in this document came from — no values were taken from search results.

**To unblock:** approve the fetch prompts when they appear, or paste the URLs into a message.
The Tier 1 URLs are all of the form
`https://api.worldbank.org/v2/country/<ISO3>/indicator/<CODE>?format=json&per_page=200&date=1996:2025`
with `<CODE>` in `RL.EST`, `RQ.EST`, `CC.EST`, `GE.EST`, `VA.EST`, `PV.EST`.

---

## Catalogue sources consulted (WebSearch only; no data taken from these)

- Worldwide Governance Indicators — World Bank Data Catalog:
  https://datacatalog.worldbank.org/search/dataset/0038026/worldwide-governance-indicators
- WGI 2025 Methodology Revision:
  https://www.worldbank.org/content/dam/sites/govindicators/doc/The%20Worldwide%20Governance%20Indicators%202025%20Methodology%20Revision.pdf
- Statistics concerning the judicial activity of the Court of Justice 2023:
  https://curia.europa.eu/site/jcms/p1_1000051300/en/statistics-concerning-the-judicial-activity-of-the-court-of-justice-2023
- European Parliament, download datasheets:
  https://results.elections.europa.eu/en/tools/download-datasheets/
- GESIS Eurobarometer trend file, trust in institutions:
  https://www.gesis.org/en/eurobarometer-data-service/overview/eb-trends-trend-files/list-of-trends/trust-in-institutions
