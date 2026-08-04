/* Audit every chart on every page for illegible states:
   (a) all data strokes drawn in the de-emphasis colour (nothing emphasised)
   (b) several series sharing one colour, where only direct labels tell them apart  */
const { chromium } = require('playwright');
const fs = require('fs');

const DEEMPH = '--deemph';
async function svgStats(p, scope){
  return p.evaluate(sc => {
    const out=[];
    document.querySelectorAll(sc+' svg').forEach((s,i)=>{
      const counts={}; let n=0;
      s.querySelectorAll('path[style*="stroke:"],polyline[style*="stroke:"]').forEach(x=>{
        const st=x.getAttribute('style');
        if(/stroke-dasharray/.test(st) && /--grid|--baseline/.test(st)) return;
        const m=(st.match(/stroke:var\((--[a-z0-9-]+)\)/)||[])[1];
        if(!m||m==='--grid'||m==='--baseline') return;
        counts[m]=(counts[m]||0)+1; n++;
      });
      if(n) out.push({i,counts,n});
    });
    return out;
  }, scope);
}
(async()=>{
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
  const p=await b.newPage({viewport:{width:1180,height:1000}});
  const errs=[]; p.on('pageerror',e=>errs.push(e.message));
  const ghost=[], shared=[];
  const note=(arr,where,st)=>arr.push(`${where}  svg#${st.i} ${JSON.stringify(st.counts)}`);

  // ---- index.html : every tab x every measure
  await p.goto('file:///home/claude/eu-project/index.html');
  const tabs=await p.$$eval('nav.tabs button',bs=>bs.map(x=>x.dataset.tab));
  const ms=await p.$$eval('.mrow button',bs=>bs.map(x=>x.dataset.m));
  for(const t of tabs){ await p.click(`button[data-tab="${t}"]`);
    for(const m of ms){ await p.click(`button[data-m="${m}"]`); await p.waitForTimeout(25);
      for(const st of await svgStats(p,'#panel')){
        const ks=Object.keys(st.counts);
        if(ks.length===1 && ks[0]===DEEMPH && st.n>1) note(ghost,`index ${t}/${m}`,st);
        for(const [c,k] of Object.entries(st.counts))
          if(k>2 && c!==DEEMPH) note(shared,`index ${t}/${m}`,st);
      } } }

  // ---- analysis.html : every tab
  await p.goto('file:///home/claude/eu-project/analysis.html');
  for(const t of ['findings','paths','adjust','method','coverage']){
    await p.click(`button[data-tab="${t}"]`).catch(()=>{}); await p.waitForTimeout(60);
    for(const st of await svgStats(p,'.panel.active')){
      const ks=Object.keys(st.counts);
      if(ks.length===1 && ks[0]===DEEMPH && st.n>1) note(ghost,`analysis ${t}`,st);
      for(const [c,k] of Object.entries(st.counts))
        if(k>2 && c!==DEEMPH) note(shared,`analysis ${t}`,st);
    } }

  // ---- every country dashboard, every lens
  for(const f of fs.readdirSync('.').filter(x=>x.endsWith('-dashboard.html')).sort()){
    await p.goto('file:///home/claude/eu-project/'+f);
    for(const t of ['legal','financial','commercial','political','social']){
      await p.click(`button[data-tab="${t}"]`).catch(()=>{}); await p.waitForTimeout(25);
      for(const st of await svgStats(p,'.panel.active')){
        const ks=Object.keys(st.counts);
        if(ks.length===1 && ks[0]===DEEMPH && st.n>1) note(ghost,`${f} ${t}`,st);
        for(const [c,k] of Object.entries(st.counts))
          if(k>2 && c!==DEEMPH) note(shared,`${f} ${t}`,st);
      } } }
  await b.close();
  console.log('=== ghost charts (every line de-emphasised) ===');
  console.log(ghost.length?ghost.join('\n'):'none');
  console.log('\n=== charts with >2 series sharing one colour, by page ===');
  const byPage={};
  [...new Set(shared)].forEach(x=>{const k=x.split(' ')[0]==='index'?('index '+x.split(' ')[1].split('/')[0]):x.split(' ')[0];byPage[k]=(byPage[k]||0)+1});
  Object.entries(byPage).sort((a,b)=>b[1]-a[1]).forEach(([k,v])=>console.log(`  ${k.padEnd(34)} ${v}`));
  console.log('  country dashboards flagged:',[...new Set(shared)].filter(x=>/dashboard/.test(x)).length);
  console.log('\nJS errors:',errs.length?errs.slice(0,3).join(' | '):'none');
})();
