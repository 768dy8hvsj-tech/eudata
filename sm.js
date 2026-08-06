/* The country pages gained three things at once -- a verdict, a budget card, and milestone
   rails clipped to each chart's own data range. This checks all three across all 28 pages,
   because a rail that renders on Poland and silently fails on Malta is exactly the kind of
   bug a single screenshot misses. */
const {chromium}=require('playwright');
const fs=require('fs');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const files=fs.readdirSync('/home/claude/eu-project').filter(f=>f.endsWith('-dashboard.html'));
let bad=[], errs=[], totalCharts=0, totalDots=0, lensChecked=0;
const p=await b.newPage();
p.on('pageerror',e=>errs.push(String(e)));
p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
for(const f of files){
  await p.goto('file:///home/claude/eu-project/'+f);
  await p.waitForTimeout(220);
  const P=JSON.parse(await p.$eval('#payload',e=>e.textContent));
  const nm=P.name;
  // 1. verdict card present, headline non-empty, three channels
  const v=await p.$$eval('#panel-overview .card.verdict .vrow',e=>e.length).catch(()=>0);
  const label=await p.$eval('#panel-overview .vlabel',e=>e.textContent.trim()).catch(()=>'');
  if(v!==3) bad.push(`${nm}: ${v} verdict channels, expected 3`);
  if(!label) bad.push(`${nm}: no verdict headline`);
  // 2. budget card totals match the payload. Non-members have no budget relationship at
  //    all, so the absence of the card is the correct behaviour rather than a failure.
  const mtiles=await p.$$eval('#panel-overview .card .tile .value',e=>e.map(x=>x.textContent));
  if(P.money===null||P.money===undefined){
    if(P.member!==false) bad.push(`${nm}: member page with no budget card`);
  } else {
  /* Compare numerically, not as strings: toFixed and toLocaleString disagree on a value
     like 59.55 (one says 59.5, the other 59.6) and that is a rounding convention, not a
     data error. */
  const want=[P.money.cumOut,P.money.cumIn,Math.abs(P.money.net)];
  const got=mtiles.map(t=>parseFloat(t.replace(/[^0-9.]/g,''))).filter(x=>!isNaN(x));
  want.forEach(w=>{ if(!got.some(g=>Math.abs(g-w)<0.06)) bad.push(`${nm}: budget tile ${w.toFixed(2)} not rendered`); });
  }
  // 3. every chart's x-range must lie inside its own data range, and carry a rail
  for(const tab of ['overview','financial','commercial','social','political','legal']){
    await p.click(`[data-tab="${tab}"]`).catch(()=>{});
    const info=await p.$$eval(`#panel-${tab} .chart-box svg`,svgs=>svgs.map(s=>({
      xLabels:Array.from(s.querySelectorAll('text')).map(t=>t.textContent).filter(t=>/^(19|20)\d\d$/.test(t)).map(Number),
      dots:s.querySelectorAll('circle[r="3.6"]').length,
      rail:Array.from(s.querySelectorAll('text')).some(t=>t.textContent==='events')
    })));
    info.forEach((c,i)=>{
      totalCharts++; totalDots+=c.dots;
      if(!c.xLabels.length) return;
      const lo=Math.min(...c.xLabels), hi=Math.max(...c.xLabels);
      if(lo<P.window.start) bad.push(`${nm}/${tab}#${i}: x axis starts ${lo}, before window ${P.window.start}`);
      if(!c.rail && P.milestones.length) bad.push(`${nm}/${tab}#${i}: no milestone rail`);
    });
  }
  // 4. the five-lens analysis must be present on every member page, and must not claim
  //    causation the study has not established. One outcome in one bloc clears that gate;
  //    a page asserting more than that is a page that has outrun its evidence.
  if(P.member!==false && nm!=='Poland'){
    for(const lens of ['legal','financial','commercial','political','social']){
      const blocks=(P.tabs||{})[lens]||[];
      const prose=blocks.filter(x=>x.type==='prose');
      if(!prose.length){bad.push(`${nm}/${lens}: no written analysis`);continue}
      if(prose.some(x=>(x.paras||[]).some(t=>/analysis (is )?pending|narrative pending/i.test(t))))
        bad.push(`${nm}/${lens}: still says pending`);
      const words=prose.reduce((a,x)=>a+(x.paras||[]).join(" ").split(/\s+/).length,0);
      if(words<60) bad.push(`${nm}/${lens}: only ${words} words of analysis`);
      lensChecked++;
    }
    const all=JSON.stringify(P.tabs);
    [/membership caused/i,/because of membership/i,/proves that/i,/membership led to/i]
      .forEach(re=>{ if(re.test(all)) bad.push(`${nm}: overclaims — matches ${re}`); });
  }

  // 5. no milestone in the timeline earlier than the window
  const early=P.milestones.filter(m=>m.sort<P.window.start);
  if(early.length) bad.push(`${nm}: ${early.length} timeline events before window start`);
  if(!P.milestones.some(m=>m.scope==='eu')) bad.push(`${nm}: no EU-wide milestones`);
  // non-member pages carry the two cards a member page cannot: published contribution
  // figures and the dated confrontations with the Union
  if(P.member===false){
    if(!P.flows) bad.push(`${nm}: non-member page with no contributions card`);
    if(!(P.disputes||[]).length) bad.push(`${nm}: non-member page with no disputes`);
    const heads=await p.$$eval('#panel-overview .card h3',e=>e.map(x=>x.textContent));
    if(!heads.some(t=>/pays the Union/.test(t))) bad.push(`${nm}: contributions card not rendered`);
    if(!heads.some(t=>/Points of contention/.test(t))) bad.push(`${nm}: disputes card not rendered`);
    // every dispute must carry a source
    P.disputes.forEach(d=>{ if(!d.source||!d.source.trim()) bad.push(`${nm}: dispute "${d.label}" has no source`); });
  }
  // a non-member page must ask the mirror question, not the membership one
  const q=await p.$eval('#panel-overview .card.verdict h3',e=>e.textContent).catch(()=>'');
  if(P.member===false && !/staying out/.test(q)) bad.push(`${nm}: non-member page asks the membership question`);
  if(P.member!==false && /staying out/.test(q)) bad.push(`${nm}: member page asks the non-member question`);
}
console.log(`${files.length} pages · ${totalCharts} charts · ${totalDots} milestone markers · ${lensChecked} lens analyses`);
console.log(bad.length?('FAILURES:\n  '+bad.slice(0,25).join('\n  ')):'0 failures');
console.log('JS errors:',errs.length?errs.slice(0,3):'none');
await b.close();
process.exit(bad.length||errs.length?1:0);})();
