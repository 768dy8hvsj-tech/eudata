#!/usr/bin/env python3
"""One-off: emit the tidy indicator CSV from values retrieved via the
World Bank Open Data API on 2026-07-27. Re-run only to regenerate the
seed file; ongoing updates should append rows for new countries/years.
"""
import csv, os

RETRIEVED = "2026-07-27"
SRC_WB = "World Bank Open Data"
YEARS = list(range(1996, 2026))

# indicator_code -> (name, unit, values 1996..2025)
POL = {
    "NY.GDP.MKTP.KD.ZG": ("GDP growth (annual %)", "%", [6.09,6.36,4.62,4.70,4.66,1.23,1.90,3.52,5.09,3.26,6.20,6.76,4.38,2.62,3.17,5.26,1.51,0.68,3.92,4.43,3.03,5.15,6.25,4.58,-2.04,6.93,5.26,0.25,3.03,3.57]),
    "FP.CPI.TOTL.ZG": ("Inflation, consumer prices (annual %)", "%", [19.79,14.91,11.60,7.15,9.90,5.41,1.91,0.68,3.38,2.18,1.28,2.46,4.16,3.80,2.58,4.24,3.56,0.99,0.05,-0.87,-0.66,2.08,1.81,2.23,3.37,5.06,14.43,11.53,3.79,3.81]),
    "SL.UEM.TOTL.ZS": ("Unemployment, total (% of labour force, modelled ILO)", "%", [12.684,10.964,9.935,12.29,14.928,18.435,20.211,19.899,18.822,17.592,13.794,9.551,7.069,8.131,9.578,9.576,10.031,10.293,8.971,7.475,6.141,4.867,3.835,3.267,3.155,3.268,2.811,2.743,2.807,2.976]),
    "NE.EXP.GNFS.ZS": ("Exports of goods and services (% of GDP)", "%", [21.98,23.26,25.86,24.00,27.07,27.06,28.62,33.24,34.06,34.53,37.66,38.47,37.67,37.00,39.89,42.32,44.02,45.77,46.22,47.16,49.91,51.69,52.23,52.61,52.43,57.04,62.35,57.88,52.18,49.95]),
    "NE.IMP.GNFS.ZS": ("Imports of goods and services (% of GDP)", "%", [23.39,27.12,30.69,29.90,33.54,30.82,32.17,35.97,36.92,35.79,40.04,42.27,42.91,37.96,42.33,44.61,44.81,44.65,45.81,45.09,46.96,48.87,50.21,48.97,46.83,53.84,60.67,52.14,48.18,47.08]),
    "BX.KLT.DINV.WD.GD.ZS": ("Foreign direct investment, net inflows (% of GDP)", "%", [2.80,3.07,3.64,4.34,5.40,2.96,2.05,2.46,5.41,3.60,6.21,5.83,2.72,3.18,3.94,3.57,1.53,0.26,3.85,3.30,3.82,2.38,3.35,3.15,3.31,5.44,6.01,4.39,2.25,1.93]),
    "NY.GDP.PCAP.PP.CD": ("GDP per capita, PPP (current international $)", "$", [8310.30,8967.12,9520.71,10080.69,10721.20,11175.29,11841.27,12328.90,13413.05,13935.56,15204.88,16833.23,18372.38,19300.17,20990.91,22808.51,23728.15,24433.89,25459.74,26988.11,28359.69,30170.28,32345.11,35882.37,37089.30,41059.58,46777.55,48473.09,51262.51,54262.40]),
    "ST.INT.ARVL": ("International tourism, number of arrivals (millions)", "millions", [87.439,87.817,88.592,89.118,84.515,61.431,50.735,52.130,61.918,64.606,65.115,66.208,59.935,53.840,58.340,60.745,67.390,72.310,73.750,77.743,80.476,83.804,85.946,88.515,None,None,None,None,None,None]),
    "SI.POV.GINI": ("Gini index", "index", [32.6,None,32.3,32.3,33.0,32.8,34.1,34.9,38.0,35.8,34.7,34.0,33.5,33.4,33.2,33.2,33.0,33.1,32.8,31.8,31.2,29.7,30.2,28.8,28.5,28.5,28.9,28.5,None,None]),
    "SM.POP.NETM": ("Net migration (thousands of people)", "thousands", [-45.349,-44.230,-39.509,-53.035,-15.921,-16.648,-16.462,-19.039,-38.216,-41.942,-68.882,-51.235,-42.288,-8.283,119.623,45.951,4.635,12.402,5.525,3.887,-5.675,-21.535,-0.223,7.696,3.920,2.251,967.744,-7.824,-238.062,-330.820]),
}

EUU = {
    "NY.GDP.PCAP.PP.CD": ("GDP per capita, PPP (current international $)", "$", [18358.26,19075.90,19970.41,20769.05,22111.55,23208.69,24225.43,24749.10,25910.57,26886.78,29209.47,31125.35,32579.99,31950.76,32995.33,34666.61,35110.66,36288.95,37363.36,38551.99,40893.58,43031.12,45055.20,48588.12,47566.44,51968.44,58573.21,61545.82,63808.07,65503.07]),
}

rows = []


def emit(iso3, country, table, source):
    for code, (name, unit, vals) in table.items():
        assert len(vals) == len(YEARS), (code, len(vals))
        for yr, v in zip(YEARS, vals):
            rows.append({
                "iso3": iso3, "country": country, "indicator_code": code,
                "indicator_name": name, "unit": unit, "year": yr,
                "value": "" if v is None else v,
                "source": source, "retrieved": RETRIEVED,
            })


emit("POL", "Poland", POL, SRC_WB)
emit("EUU", "European Union (aggregate)", EUU, SRC_WB)

# derived: Poland GDP per capita PPP as % of the EU average
pl = POL["NY.GDP.PCAP.PP.CD"][2]
eu = EUU["NY.GDP.PCAP.PP.CD"][2]
for yr, a, b in zip(YEARS, pl, eu):
    rows.append({
        "iso3": "POL", "country": "Poland",
        "indicator_code": "DERIVED.PPP.PCT.EU",
        "indicator_name": "GDP per capita PPP as % of EU average",
        "unit": "%", "year": yr, "value": round(a / b * 100, 2),
        "source": "Derived from World Bank NY.GDP.PCAP.PP.CD (POL / EUU)",
        "retrieved": RETRIEVED,
    })

os.makedirs("data", exist_ok=True)
fields = ["iso3", "country", "indicator_code", "indicator_name", "unit",
          "year", "value", "source", "retrieved"]
with open("data/indicators.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    rows.sort(key=lambda r: (r["iso3"], r["indicator_code"], r["year"]))
    w.writerows(rows)

print("wrote data/indicators.csv:", len(rows), "rows")
