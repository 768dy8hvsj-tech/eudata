# Project status — 3 August 2026

## Against the original goal

The brief was to understand EU membership's effect across five lenses — legal, financial,
commercial, political, social — at ≥95% confidence, credited sources only.

**All five lenses now carry data.** Two of them carry it only as a measured null, which is a
real answer rather than a gap.

| Lens | State |
|---|---|
| Financial | Answered. An income effect is **not demonstrable** at 95% confidence, and that is now firmer: the pre-accession placebo shows the gap was already opening before anyone joined. |
| Commercial | Answered. **Trade openness is the study's strongest result**: Eastern members +20.5pp of GDP vs Western Balkan non-members, 11 of 11 above their control, placebo clean. FDI clears in both East (−3.1pp) and West (+1.0pp). Tourism estimated then **rejected**. |
| Social | Answered, largely in the negative. Unemployment shows no detectable effect. Net migration and Gini are defeated by pre-trends or missing surveys. |
| Legal | **Measured, result is a null.** Rule of law, adjusted for headroom: +0.04, indistinguishable from zero across 8 members. The raw −0.16 is a confounded number and must not be quoted. |
| Political | **Measured, no reportable estimate.** Voice and accountability fails the placebo; control of corruption has no identifiable catch-up line. Both are charted descriptively on all 28 country pages. |

## Data

**38,022 rows · 43 entities · 25 indicators.**

Added 3 August — World Bank Worldwide Governance Indicators, 41 entities each, 1996–2024,
26 points per country (1997, 1999 and 2001 genuinely absent; WGI was biennial before 2002):

- `WGI.RL.EST` Rule of law — 1,065 rows
- `WGI.VA.EST` Voice and accountability — 1,091 rows
- `WGI.CC.EST` Control of corruption — 1,065 rows

**Collection trap worth remembering:** the familiar codes `RL.EST`, `VA.EST`, `CC.EST` are
**archived stubs**. They resolve in the catalogue with `source id 57, "WDI Database Archives"`
but every data call returns *"The indicator was not found. It may have been deleted or
archived."* The live series are namespaced `GOV_WGI_<X>.EST` and **require `&source=3`**:

```
https://api.worldbank.org/v2/country/POL/indicator/GOV_WGI_RL.EST?format=json&per_page=300&source=3&page=1
```

Also learned: WebFetch caches errors for 15 minutes keyed on the full URL string, so a failing
call must be given a genuinely novel URL to retry — appending a throwaway parameter works where
reordering existing ones does not.

## Two method changes this session

**1. Coverage requirement now adapts to publication frequency.** The old rule demanded 3 of 5
years in every window. WGI is biennial before 2002, so a 1994–1998 window holds only two
published years and complete coverage was being rejected on a technicality. The requirement is
now three, *or all of them where the source publishes fewer than three in that span*. Verified
as a no-op for every annual series — no pre-existing result changed except tourism East, which
gained one country and remains gated.

**2. Headroom adjustment for bounded indices.** The placebo tests whether groups shared a
*trend*; it does not test whether they shared a *starting level*, and on a bounded −2.5…+2.5
scale those are different things. Eastern members began rule of law at +0.57 and gained +0.14;
the Balkan controls began at −0.58 and gained +0.35. Both improved. Subtracting one from the
other charges members for their head start — the beta-convergence problem the income estimates
already had, in a new outcome. The fix reuses `convergence_adjusted`'s logic with the same
r² ≥ 0.5 gate. **Where a headroom adjustment exists, the raw DiD is never reported as a
finding.**

## Findings that survive every check

| Outcome | Bloc | Estimate | 95% interval | Unanimity |
|---|---|---|---|---|
| Trade openness | East | **+20.5 pp of GDP** | +14.3 to +26.7 | 11 of 11 |
| FDI inflows | East | **−3.1 pp of GDP** | −5.2 to −1.0 | 1 of 11 positive |
| FDI inflows | West | **+1.0 pp of GDP** | +0.2 to +1.8 | 5 of 6 |
| Unemployment | East | +1.4 pp (null) | −0.6 to +3.4 | not distinguishable from zero |

Four of thirty estimates attempted. That strike rate is the point, not a defect.

## Unresolved

- **WGI renormalisation.** Whether the scores are renormalised against the world distribution
  each year is unconfirmed — `www.worldbank.org` is not an approved fetch host and the API's own
  `sourceNote` field is empty. **This does not affect the causal estimates**: DiD uses the same
  calendar windows for treated and controls, so any common year effect differences out. It
  affects only the descriptive reading of a single country's line over time, which is flagged in
  the chart blurbs.
- **The 2025 WGI methodology revision** — whether it restated earlier years is unchecked. Treat
  as a suspected break, as with the Eurostat 2024 earnings break.
- **OECD wages and Better Life Index** remain blocked on gzip transport.
- Tier 2/3 legal-political sources (CJEU preliminary references, transposition deficit, EP
  turnout, Eurobarometer) never reached — see `claude/legal-political-scope.md`.

## Not yet on the user's Mac

The device bridge disconnected during the final commit. All 31 rebuilt pages were delivered
into the conversation but **not written to `~/Downloads/EU Analysis/`**, and the git commit for
this session's work has not been made. Both need redoing when the desktop reconnects.

## Permanent limit

The six founding members can never be tested causally. They joined in 1958; usable income data
begins in 1960 and WGI in 1996. No pre-membership baseline exists and no collection creates one.
