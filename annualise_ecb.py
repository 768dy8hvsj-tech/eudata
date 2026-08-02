#!/usr/bin/env python3
"""Turn the ECB's dated rate-change list into an annual series.

The ECB publishes changes to the main refinancing rate as dated steps, not as an
annual series, so any annual figure is a derived quantity and the derivation has
to be stated. This computes the TIME-WEIGHTED AVERAGE rate in force during each
calendar year: each rate is weighted by the number of days it applied.

Two caveats travel with the output and are written into the source field:

1. The MRO series has genuine definitional breaks. It is a fixed-rate tender
   through 9 June 2000, a variable-rate tender MINIMUM BID rate from 28 June 2000
   to 9 July 2008, and a fixed rate again from 15 October 2008. Those are not the
   same instrument, so a continuous line across 2000 and 2008 overstates
   comparability.

2. The rate applies to the euro area as a whole, so it does not vary across euro
   members and cannot discriminate between them. It is context, not a comparison
   variable — which is exactly why the long-term bond yield was collected too.
"""
import csv, os, datetime, collections

BASE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(BASE, "data", "raw", "_ecb_policy_rate.csv")
OUT = os.path.join(BASE, "data", "raw", "_ecb_policy_rate_annual.csv")

steps = []
for r in csv.DictReader(open(SRC, encoding="utf-8")):
    v = (r.get("value") or "").strip()
    d = (r.get("year") or "").strip()
    if not v or len(d) != 10:
        continue
    try:
        steps.append((datetime.date.fromisoformat(d), float(v)))
    except ValueError:
        continue
steps.sort()
if not steps:
    raise SystemExit("no dated ECB steps parsed")

first_year = steps[0][0].year
last_year = min(2025, datetime.date.today().year)

# day-by-day is simplest and exactly right; the span is ~27 years
rate_on = {}
idx = 0
cur = None
day = steps[0][0]
end = datetime.date(last_year, 12, 31)
while day <= end:
    while idx < len(steps) and steps[idx][0] <= day:
        cur = steps[idx][1]
        idx += 1
    rate_on[day] = cur
    day += datetime.timedelta(days=1)

acc = collections.defaultdict(list)
for d, v in rate_on.items():
    if v is not None:
        acc[d.year].append(v)

rows = []
for y in sorted(acc):
    days = acc[y]
    # only report a year that is fully covered, so a partial year cannot be
    # mistaken for a complete one
    expected = 366 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 365
    if y == first_year or len(days) < expected:
        continue
    rows.append(["EMU", "Euro area", "ECB.MRO.ANNUAL",
                 "ECB main refinancing rate, time-weighted annual average", "%",
                 y, round(sum(days) / len(days), 3),
                 "Derived from European Central Bank dated rate changes; "
                 "definitional breaks 2000-06 and 2008-10", "2026-08-02"])

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["iso3", "country", "indicator_code", "indicator_name", "unit",
                "year", "value", "source", "retrieved"])
    w.writerows(rows)

print(f"{len(rows)} complete years written ({rows[0][5]}–{rows[-1][5]})")
for r in rows:
    if r[5] in (2000, 2008, 2015, 2022, 2023, 2024):
        print(f"   {r[5]}: {r[6]}%")
