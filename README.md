# EU Membership Impact — project structure

Research question: how has EU membership affected member nations, across five lenses —
legal, financial, commercial, political, social — tracked annually from two years before
accession negotiations opened, through intake, to today.

Standing rule: only credited data sources, and only findings held at **≥95% confidence**.
Anything weaker is either omitted or explicitly flagged `(≈)`.

## Status

| | |
|---|---|
| Country pages built | 17 (Austria, Belgium, Cyprus, Czechia, Estonia, Finland, France, Germany, Greece, Ireland, Italy, Luxembourg, Netherlands, Poland, Portugal, Spain, Sweden) |
| Written five-lens analysis | Poland only — the rest are data-first |
| Data points | ~9,900 rows in `data/indicators.csv` |
| Milestones verified | 206 rows across all 28 countries, including the UK's Brexit sequence |
| Still to collect | Bulgaria, Croatia, Denmark, Hungary, Latvia, Lithuania, Malta, Romania, Slovakia, Slovenia, United Kingdom |
| Also outstanding | Policy rate + long-term bond yield, OECD + Eurostat wages, OECD Better Life Index topic scores |

Metadata (accession, negotiation, euro, Schengen and OECD status) and full milestone
timelines are already verified and stored for **all 28 countries** — including the eleven
whose World Bank series are still missing. Only the numeric series are outstanding for those.

## Layout

```
EU Analysis/
├── data/
│   ├── indicators.csv          all quantitative series, tidy long format
│   ├── countries.csv           accession / euro / Schengen / OECD metadata, 28 countries
│   ├── milestones.csv          verified timeline events, 28 countries
│   ├── narrative/<ISO3>.json   per-country content + page layout
│   └── raw/<ISO3>.csv          as-collected per-country files (audit trail)
├── template.html               country-page presentation layer — no data in it
├── index_template.html         index-page presentation layer — no data in it
├── build_dashboard.py          data + narrative → one country dashboard
├── build_index.py              data → cross-country index page
├── gen_narrative.py            generates data-first narrative files
├── consolidate.py              merges data/raw/*.csv into indicators.csv
├── index.html                  generated cross-country comparison
├── <country>-dashboard.html    generated country pages (do not hand-edit)
└── README.md
```

## data/indicators.csv

One row per country × indicator × year: `iso3`, `country`, `indicator_code`,
`indicator_name`, `unit`, `year`, `value`, `source`, `retrieved`. `EUU` is the EU
aggregate used as the comparison denominator. Per-row provenance keeps a mixed-source
table auditable. Derived series are stored explicitly rather than computed in the page —
`DERIVED.PPP.PCT.EU` is GDP per capita PPP as a share of the EU average, with its
derivation written into the `source` column.

Counts (`ST.INT.ARVL`, `SM.POP.NETM`) are stored **raw**; charts apply their own display
scaling through the `scale` option, so the stored value always matches the source.

Indicators collected, all World Bank Open Data retrieved 2026-07-27: `NY.GDP.MKTP.KD.ZG`,
`NY.GDP.MKTP.CD`, `NY.GDP.PCAP.PP.CD`, `NY.GNP.PCAP.PP.CD`, `FP.CPI.TOTL.ZG`,
`SL.UEM.TOTL.ZS`, `NE.EXP.GNFS.ZS`, `NE.IMP.GNFS.ZS`, `BX.KLT.DINV.WD.GD.ZS`,
`ST.INT.ARVL`, `SI.POV.GINI`, `SM.POP.NETM`, plus the derived convergence series.

## Rebuilding

```
python3 consolidate.py                  # data/raw/*.csv  → data/indicators.csv
python3 gen_narrative.py                # → data/narrative/<ISO3>.json for new countries
python3 build_dashboard.py DEU FRA ITA  # → one HTML page per country
python3 build_index.py                  # → index.html
```

`gen_narrative.py` never overwrites a file marked `"handwritten": true` — that is how
Poland's written analysis survives regeneration. Promote any country to hand-written by
editing its narrative JSON and setting that flag.

## Adding a country

1. Append its rows to `data/raw/<ISO3>.csv` in the standard nine-column shape.
2. Its `countries.csv` and `milestones.csv` entries already exist for all 28.
3. `python3 consolidate.py && python3 gen_narrative.py && python3 build_dashboard.py <ISO3> && python3 build_index.py`

## Method notes

- **Window rule.** Each country's window starts two years before *its* negotiations opened
  (`window_start` in `countries.csv`). The six founding members have no accession
  negotiation, so their window opens in 1960 and their whole series is post-accession —
  there is no pre-membership baseline for them, and their pages say so.
- **Convergence floor.** The EU aggregate denominator is only available from 1996, so
  convergence charts start there even where a country's window opens earlier.
- **Attribution.** The charts show what happened around membership, not what membership
  alone caused. Causal claims appear only where the literature supports them.
- **Better Life Index.** Deliberately absent rather than approximated. The OECD publishes
  no official composite score, the index is not an annual series, and it excludes five EU
  members. The agreed approach is to store all eleven topic scores and compare them as a
  heatmap, showing the non-OECD members explicitly as no-data.
