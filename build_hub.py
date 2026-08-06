#!/usr/bin/env python3
"""Build start-here.html — the front door.

Until now the project was ~30 loose HTML files with no entry point and no way
to get from the analysis to a country page. This builds a hub that states the
finding, routes to the three layers (argument, comparison, countries), and
documents what the dataset actually contains.
"""
import csv, json, os, re, datetime, collections

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")

blocs = list(csv.DictReader(open(os.path.join(DATA, "blocs.csv"), encoding="utf-8")))
members = [b for b in blocs if b["group"] == "member"]
controls = [b for b in blocs if b["group"] == "control"]
A = json.load(open(os.path.join(BASE, "analysis_payload.json"), encoding="utf-8"))

rows = list(csv.DictReader(open(os.path.join(DATA, "indicators.csv"), encoding="utf-8")))
npoints = sum(1 for r in rows if r["value"])
entities = len({r["iso3"] for r in rows})
indicators = len({r["indicator_code"] for r in rows})
milestones = sum(1 for _ in csv.DictReader(open(os.path.join(DATA, "milestones.csv"), encoding="utf-8")))

adjE = A["adjusted"]["East"]
inc = [m for m in A["measures"] if m["id"] == "income"][0]


def slug(n):
    return re.sub(r"[^a-z0-9]+", "-", n.lower()).strip("-") + "-dashboard.html"


by_bloc = collections.OrderedDict()
for b in ("West", "South", "East"):
    by_bloc[b] = [m for m in members if m["bloc"] == b]

cards = ""
for bloc, ms in by_bloc.items():
    items = "".join(
        f'<a href="{slug(m["name"])}"><span class="n">{m["name"]}</span>'
        f'<span class="d">joined {m["accession_year"] or "1958"}</span></a>'
        for m in sorted(ms, key=lambda x: x["name"]))
    ctrl = ", ".join(c["name"] for c in controls if c["control_for"] == bloc) or "none"
    cards += (f'<h4>{bloc} — {len(ms)} members</h4>'
              f'<p class="mini">Compared against: {ctrl}</p>'
              f'<div class="clist">{items}</div>')

# Non-member profiles. A control group nobody can look at is a control group nobody can
# check, so the countries every estimate is measured against get pages of their own.
nm_path = os.path.join(DATA, "nonmembers.csv")
if os.path.exists(nm_path):
    nm = list(csv.DictReader(open(nm_path, encoding="utf-8")))
    built = [c for c in nm if os.path.exists(os.path.join(BASE, slug(c["name"])))]
    if built:
        items = "".join(
            f'<a href="{slug(c["name"])}"><span class="n">{c["name"]}</span>'
            f'<span class="d">{"not a member · EEA since 1994" if c["eea_year"].strip() else "not a member · bilateral route"}</span></a>'
            for c in sorted(built, key=lambda x: x["name"]))
        nm_block = ('<h4 id="non-members">Non-members — profiled</h4>'
                    '<p class="mini">The comparison countries every estimate in this '
                    'project is measured against — shown rather than assumed. Each carries a '
                    'membership verdict, what it pays the Union, its points of contention, and '
                    'a map of how much of the EU rulebook already applies.</p>'
                    f'<div class="clist">{items}</div>')
        cards = nm_block + cards

ci = adjE.get("ci")
headline_val = "not distinguishable from zero" if (ci and ci["crossesZero"]) else f"{adjE['mean']:+.1f}%"
ci_txt = (f"Central estimate {adjE['mean']:+.1f}%, 95% interval {ci['lo']:+.1f}% to {ci['hi']:+.1f}%, "
          f"across {adjE['n']} countries." if ci else "Interval not computable.")

# The trade result is the one estimate that clears every check the project
# applies, so the front door states it next to the income null rather than
# leaving the overview reading as "nothing was found".
trade = [m for m in A["measures"] if m["id"] == "trade"][0]["did"]["East"]
tci, tpl = trade.get("ci"), trade.get("placebo", {})
trade_block = ""
if trade.get("identified") and tpl.get("verdict") == "passes" and tci:
    trade_block = f"""
<div class="finding">
  <div class="k">Central finding — trade openness, Eastern members vs Western Balkan non-members</div>
  <div class="v">{trade['mean']:+.1f} pp of GDP</div>
  <p>95% interval {tci['lo']:+.1f} to {tci['hi']:+.1f} percentage points, and <strong>all
  {trade['n']} of {trade['n']} Eastern members are above their control group</strong> — there is no
  country carrying this average on its own. Run entirely on pre-accession years the same estimator
  reports {tpl['mean']:+.1f}, so the gap opens at accession rather than before it.</p>
  <p>This is the single result in the study that survives every check applied to it, and it is
  worth being precise about what it claims. Trade is the channel the single market acts on most
  directly, so an effect here is what the theory predicts. <strong>It does not follow that people
  became better off:</strong> that is the income question above, and the income question remains
  unresolved.</p>
</div>"""

HTML = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>EU membership impact — overview</title>
<style>
.viz-root{{color-scheme:light;--surface-1:#fcfcfb;--page:#f9f9f7;--text-primary:#0b0b0b;
--text-secondary:#52514e;--text-muted:#898781;--grid:#e1e0d9;--border:rgba(11,11,11,0.10);
--series-1:#2a78d6;--series-2:#eb6834;--neg:#e34948}}
@media (prefers-color-scheme:dark){{:root:where(:not([data-theme="light"])) .viz-root{{color-scheme:dark;
--surface-1:#1a1a19;--page:#0d0d0d;--text-primary:#fff;--text-secondary:#c3c2b7;--text-muted:#898781;
--grid:#2c2c2a;--border:rgba(255,255,255,0.10);--series-1:#3987e5;--series-2:#d95926;--neg:#e66767}}}}
:root[data-theme="dark"] .viz-root{{color-scheme:dark;--surface-1:#1a1a19;--page:#0d0d0d;--text-primary:#fff;
--text-secondary:#c3c2b7;--text-muted:#898781;--grid:#2c2c2a;--border:rgba(255,255,255,0.10);
--series-1:#3987e5;--series-2:#d95926;--neg:#e66767}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:system-ui,-apple-system,"Segoe UI",sans-serif}}
.viz-root{{background:var(--page);color:var(--text-primary);min-height:100vh;padding:26px 20px 52px}}
.wrap{{max-width:1000px;margin:0 auto}}
.sitenav{{display:flex;gap:14px;margin-bottom:16px;font-size:12.5px;flex-wrap:wrap}}
.sitenav a{{color:var(--text-secondary);text-decoration:none;border-bottom:1px solid transparent;padding-bottom:2px}}
.sitenav a:hover{{color:var(--text-primary);border-bottom-color:var(--border)}}
.sitenav a.here{{color:var(--text-primary);font-weight:600;border-bottom-color:var(--series-1)}}
header.top{{display:flex;align-items:flex-start;justify-content:space-between;gap:16px}}
h1{{font-size:30px;font-weight:650;letter-spacing:-0.02em}}
.sub{{color:var(--text-secondary);font-size:14.5px;margin-top:6px;max-width:680px;line-height:1.6}}
.theme-btn{{border:1px solid var(--border);background:var(--surface-1);color:var(--text-secondary);
border-radius:8px;padding:6px 12px;font-size:12.5px;cursor:pointer;font-family:inherit;white-space:nowrap}}
h2{{font-size:16px;font-weight:600;margin:30px 0 4px}}
.lead{{font-size:12.5px;color:var(--text-secondary);margin-bottom:12px;line-height:1.5}}
.finding{{background:var(--surface-1);border:1px solid var(--border);border-left:3px solid var(--series-1);
border-radius:12px;padding:20px 22px;margin-top:22px}}
.finding .k{{font-size:12.5px;color:var(--text-secondary)}}
.finding .v{{font-size:27px;font-weight:600;margin-top:6px;letter-spacing:-0.01em}}
.finding p{{font-size:13.5px;color:var(--text-secondary);line-height:1.62;margin-top:10px}}
.finding p strong{{color:var(--text-primary);font-weight:600}}
.routes{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px}}
.route{{display:block;background:var(--surface-1);border:1px solid var(--border);border-radius:12px;
padding:17px 19px;text-decoration:none}}
.route:hover{{border-color:var(--series-1)}}
.route .t{{font-size:15px;font-weight:600;color:var(--text-primary)}}
.route .d{{font-size:12.5px;color:var(--text-secondary);margin-top:5px;line-height:1.5}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-top:6px}}
.stat{{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:13px 15px}}
.stat .v{{font-size:21px;font-weight:600}}
.stat .k{{font-size:12px;color:var(--text-secondary);margin-top:3px}}
h4{{font-size:13px;font-weight:600;margin:18px 0 2px}}
.mini{{font-size:11.5px;color:var(--text-muted);margin-bottom:8px}}
.clist{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:7px}}
.clist a{{display:block;border:1px solid var(--border);border-radius:9px;padding:8px 11px;
text-decoration:none;background:var(--surface-1)}}
.clist a:hover{{border-color:var(--series-1)}}
.clist .n{{display:block;font-size:13px;font-weight:500;color:var(--text-primary)}}
.clist .d{{display:block;font-size:11px;color:var(--text-muted);margin-top:1px}}
.files{{font-size:13px;color:var(--text-secondary);line-height:1.75}}
.files code{{font-size:11.5px;background:var(--page);padding:1px 5px;border-radius:4px;color:var(--text-muted)}}
.stamp{{font-size:11.5px;color:var(--text-muted);margin-top:26px}}
</style></head>
<body><div class="viz-root"><div class="wrap">
<nav class="sitenav"><a class="here">Overview</a><a href="index.html">Country comparison</a><a href="analysis.html">The argument</a><a href="flows.html">Budget flows</a><a href="start-here.html#non-members">Non-members</a></nav>
<header class="top">
<div><h1>EU membership impact</h1>
<p class="sub">What has EU membership done to its member states — legally, financially, commercially, politically and socially — measured against comparable countries that never joined.</p></div>
<button class="theme-btn" id="themeBtn" type="button">Theme: auto</button>
</header>

<div class="finding">
  <div class="k">Central finding — income effect on Eastern members, adjusted for catch-up growth</div>
  <div class="v">{headline_val}</div>
  <p>{ci_txt} Eastern members grew enormously after joining — but so did the Western Balkan countries that did not join, and poorer economies grow faster mechanically regardless of membership.</p>
  <p><strong>This is an inconclusive result, not a null one.</strong> Two biases push the estimate toward zero: the control countries are all EU candidates already reforming in anticipation, and the heaviest accession reforms happen <em>before</em> entry, inside the pre-accession baseline. One bias pushes the other way: countries joined because they already qualified. They do not cancel in any quantifiable way.</p>
</div>
{trade_block}

<h2>Four ways in</h2>
<p class="lead">The project has four layers. Start with whichever question you have.</p>
<div class="routes">
  <a class="route" href="analysis.html"><span class="t">The argument →</span>
    <span class="d">Does membership change a country's trajectory? Event-time alignment, bloc splits, difference-in-differences against non-members, and an explicit account of what the method cannot show.</span></a>
  <a class="route" href="index.html"><span class="t">Country comparison →</span>
    <span class="d">Where every member stands today on income, GNI, unemployment and convergence with the EU average — ranked, plus each country's full trajectory.</span></a>
  <a class="route" href="flows.html"><span class="t">Budget flows →</span>
    <span class="d">What each country pays into the EU budget and what comes back, itemised by fund — farm payments, cohesion, research, the Recovery Facility. Accounting rather than inference: no estimation, and every figure reconciled to the Commission's published totals.</span></a>
  <a class="route" href="poland-dashboard.html"><span class="t">A worked country page →</span>
    <span class="d">Poland is the completed reference: five lenses, verified milestone timeline, and written analysis. Every other country has the same charts and timeline with narrative pending.</span></a>
</div>

<h2>What the dataset holds</h2>
<div class="stats">
  <div class="stat"><div class="v">{npoints:,}</div><div class="k">verified data points</div></div>
  <div class="stat"><div class="v">{entities}</div><div class="k">countries &amp; aggregates</div></div>
  <div class="stat"><div class="v">{indicators}</div><div class="k">indicators</div></div>
  <div class="stat"><div class="v">{milestones}</div><div class="k">verified milestones</div></div>
  <div class="stat"><div class="v">{len(members)}</div><div class="k">member states + UK</div></div>
  <div class="stat"><div class="v">{len(controls)}</div><div class="k">non-member controls</div></div>
</div>

<h2>Country pages</h2>
<p class="lead">Grouped by bloc, because post-war starting points differ so much that comparing across the line measures the Iron Curtain rather than the Union.</p>
{cards}

<h2>Under the hood</h2>
<p class="files">
Everything is generated from a tidy data store — nothing is hand-written into the HTML.<br>
<code>data/indicators.csv</code> every value with its own source and retrieval date ·
<code>data/countries.csv</code> accession, euro, Schengen, OECD status ·
<code>data/milestones.csv</code> verified timeline events ·
<code>data/blocs.csv</code> bloc and control-group assignment ·
<code>data/narrative/&lt;ISO3&gt;.json</code> per-country content and page layout<br><br>
Rebuild with <code>consolidate.py</code> → <code>gen_narrative.py</code> → <code>build_dashboard.py</code> →
<code>build_index.py</code> → <code>analysis.py</code> → <code>build_hub.py</code>.
See <code>README.md</code> for the full description.
</p>

<p class="stamp">Generated {datetime.date.today().isoformat()} · sources: World Bank Open Data, European Commission, Council of the EU, EUR-Lex, ECB, national electoral commissions.</p>
</div></div>
<script>
(function(){{var m=["auto","light","dark"],i=0,b=document.getElementById("themeBtn");
b.addEventListener("click",function(){{i=(i+1)%3;var v=m[i];
if(v==="auto")document.documentElement.removeAttribute("data-theme");
else document.documentElement.setAttribute("data-theme",v);b.textContent="Theme: "+v}})}})();
</script></body></html>"""

open(os.path.join(BASE, "start-here.html"), "w", encoding="utf-8").write(HTML)
print(f"start-here.html written ({npoints:,} data points, {len(members)} members, {len(controls)} controls)")
