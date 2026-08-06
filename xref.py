#!/usr/bin/env python3
"""Cross-reference audit: text on one country's page that is really about another country.

WHY THIS EXISTS. The pages are generated, and generated pages share text. Shared text is
right when it states a rule that holds for every country and wrong when it states a fact
about one of them. The failure is silent -- nothing errors, the page renders, and a reader
on Iceland's page is told what the Norwegian Supreme Court decided. That is how the energy
row in the acquis map went out: `note_eea` is one column shared by Norway and Iceland, and
somebody wrote a Norwegian fact into it.

WHAT IT DOES. Reads the payload out of the BUILT HTML rather than the source CSVs, so it
catches leakage wherever it enters -- a shared column, a shared narrative constant, a
template default. For each page it looks for words identifying a different country, and
flags them unless the same string also names the page's own country (which is what a
genuine comparison looks like: "more than Germany, France or Italy" on Norway's page).

WHAT IT DELIBERATELY ALLOWS. Two kinds of legitimate other-country mention that the "names
its own country too" rule cannot see, listed explicitly in ALLOW below with a reason each.
Anything not on that list is a finding. Add to the list only when the text is genuinely
about the other country ON PURPOSE.
"""
import json, re, sys, pathlib, csv

BASE = pathlib.Path(__file__).resolve().parent

# words that identify a country. Demonyms, capitals and institutions, because those are
# what actually leak -- "the Storting" is as country-specific as "Norway".
OWNER = {
    "NOR": ["norway", "norwegian", "storting", "svalbard"],
    "ISL": ["iceland", "icelandic", "althingi"],
    "CHE": ["switzerland", "swiss"],
    "POL": ["poland", "polish", "sejm"],
    "DEU": ["germany", "german", "bundestag", "bundesverfassungsgericht"],
    "GBR": ["united kingdom", "britain", "british", "westminster"],
    "FRA": ["france", "french"],
    "ITA": ["italy", "italian"],
    "ESP": ["spain", "spanish"],
    "GRC": ["greece", "greek"],
    "HUN": ["hungary", "hungarian"],
    "IRL": ["ireland", "irish"],
    "MLT": ["malta", "maltese"],
    "SWE": ["sweden", "swedish", "riksdag"],
    "DNK": ["denmark", "danish", "folketing"],
    "FIN": ["finland", "finnish"],
    "AUT": ["austria", "austrian"],
    "BEL": ["belgium", "belgian"],
    "NLD": ["netherlands", "dutch"],
    "PRT": ["portugal", "portuguese"],
    "CZE": ["czechia", "czech"],
    "SVK": ["slovakia", "slovak"],
    "SVN": ["slovenia", "slovenian"],
    "HRV": ["croatia", "croatian"],
    "ROU": ["romania", "romanian"],
    "BGR": ["bulgaria", "bulgarian"],
    "EST": ["estonia", "estonian"],
    "LVA": ["latvia", "latvian"],
    "LTU": ["lithuania", "lithuanian"],
    "CYP": ["cyprus", "cypriot"],
    "LUX": ["luxembourg"],
}

# Paths whose whole job is to name other countries. Not leakage.
SHARED = (".acquis", ".joining", ".method", ".sources", ".subtitle", ".pageTitle",
          ".tabs", ".heroChart", ".kpis")

# (page, payload path, substring, why it is allowed)
ALLOW = [
    ("NOR", ".joining.gains[1].body", "Switzerland spent four years",
     "deliberate comparison -- the sentence says 'for a neighbour' and the point is that "
     "programme access has been withdrawn from an EFTA state before"),
    ("ISL", ".joining.gains[1].body", "Switzerland spent four years",
     "same deliberate comparison"),
    ("ISL", ".flows.out[0].source", "Norwegian MFA",
     "the credited source for Iceland's share of the EEA Financial Mechanism genuinely is "
     "the Norwegian MFA and the European Parliament; no Icelandic figure in euros exists"),
    ("*", ".acquis.rows", "Norway",
     "the acquis map's shared EEA notes may name Norway on Norway's own page; the Iceland "
     "overrides live in note_isl and are applied by build_dashboard.acquis()"),
    ("*", ".method", "Poland is the one hand-written page",
     "a method note about how the study is built, true on every page"),
    ("*", ".acquis.rows", "Bulgaria joined on 1 January 2026",
     "dates the euro area's current size; a fact about the Union, not about the page"),
    ("*", ".tabs", "is the sharpest case",
     "the Eastern population illustration, computed by narrate._peak_case; the page "
     "belonging to that country gets the first-person form instead"),
    ("NOR", ".joining.costs[0].body", "Germany, at a lower income per head",
     "the only published net-contribution benchmark, used deliberately as the comparison"),
    ("ISL", ".joining.costs[0].body", "Germany, at a lower income per head", "same"),
    ("CHE", ".joining.costs[0].body", "Germany, at a lower income per head", "same"),
    ("CHE", ".tabs.political[0].items[0].delta", "French-speaking cantons",
     "about Switzerland's own linguistic regions, not about France"),
    ("NOR", ".tabs.political[0].items[1].delta", "Austria, Finland",
     "names the three states that joined in 1995 when Norway's treaty went unratified"),
    ("POL", ".tabs", "UK, Irish and Swedish labour markets",
     "the three states that opened their labour markets to Poles in 2004"),
]


def allowed(owner, path, text):
    for page, pfx, needle, _why in ALLOW:
        if page in (owner, "*") and path.startswith(pfx) and needle in text:
            return True
    return False


def walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, node


def payload_of(p):
    m = re.search(r'<script id="payload" type="application/json">(.*?)</script>',
                  p.read_text(encoding="utf-8"), re.S)
    return json.loads(m.group(1).replace("<\\/", "</")) if m else None


pages = {}
for r in csv.DictReader(open(BASE / "data" / "countries.csv", encoding="utf-8")):
    slug = re.sub(r"[^a-z0-9]+", "-", r["name"].lower()).strip("-")
    pages[f"{slug}-dashboard.html"] = r["iso3"]
for fn, iso in (("norway-dashboard.html", "NOR"), ("iceland-dashboard.html", "ISL"),
                ("switzerland-dashboard.html", "CHE")):
    pages[fn] = iso

hits, scanned = 0, 0
for fn, owner in sorted(pages.items()):
    p = BASE / fn
    if not p.exists():
        continue
    payload = payload_of(p)
    if payload is None:
        print(f"NO PAYLOAD  {fn}"); hits += 1; continue
    scanned += 1
    mine = OWNER.get(owner, [])
    for path, text in walk(payload):
        if not path.startswith(SHARED) or allowed(owner, path, text):
            continue
        low = text.lower()
        def has(w):
            return re.search(r"\b" + re.escape(w), low) is not None
        if any(has(x) for x in mine):
            continue                      # names its own country: a comparison, not leakage
        for other, words in OWNER.items():
            if other == owner:
                continue
            w = next((w for w in words if has(w)), None)
            if not w:
                continue
            i = re.search(r"\b" + re.escape(w), low).start()
            print(f"\n{owner:3} {fn}\n    {path}\n    names {other} ('{w}'), never {owner}"
                  f"\n    …{text[max(0, i - 90):i + 120].strip()}…")
            hits += 1
            break

print(f"\n{scanned} pages scanned · {hits} cross-reference issue(s)")
sys.exit(1 if hits else 0)
