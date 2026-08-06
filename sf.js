/* Every number flows.html renders, checked against the payload it was built from.
   Walks all 28 country statements, reads both tables out of the DOM, and compares
   each cell to the value the payload carries. Catches formatting bugs that a
   Python-side reconciliation cannot see. */
const {chromium}=require('playwright');
(async()=>{
const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium'});
const p=await b.newPage(); const errs=[];
p.on('pageerror',e=>errs.push(String(e)));
p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
await p.goto('file:///home/claude/eu-project/flows.html');
await p.waitForTimeout(500);
const P=JSON.parse(await p.$eval('#payload',e=>e.textContent));
let checked=0, bad=[];
for(const c of P.countries){
  await p.click(`#panel-country .picker button:text-is("${c.name}")`);
  await p.waitForTimeout(60);
  const tables=await p.$$eval('#panel-country table.t',ts=>ts.map(t=>
    Array.from(t.querySelectorAll('tr')).slice(1).map(r=>
      Array.from(r.querySelectorAll('td')).map(d=>d.textContent.trim()))));
  const fl={}; P.funds.forEach(f=>fl[f.label]=f.id);
  const sl={}; P.sources.forEach(s=>sl[s.label]=s.id);
  for(const [ti,map,cum] of [[0,fl,c.cumReceipts],[1,sl,c.cumPayments]]){
    for(const row of tables[ti]){
      if(!row.length) continue;
      const name=row[0];
      if(name.startsWith('Total')){
        const want=(ti===0?c.cumIn:c.cumOut);
        const got=parseFloat(row[1].replace(/,/g,''));
        if(Math.abs(got-want)>0.06) bad.push(`${c.name} total[${ti}] ${got} vs ${want}`);
        checked++; continue;
      }
      const id=map[name];
      if(id===undefined){bad.push(`${c.name}: unknown row "${name}"`);continue}
      const got=parseFloat(row[1].replace(/,/g,''));
      if(Math.abs(got-cum[id])>0.06) bad.push(`${c.name} ${name}: ${got} vs ${cum[id]}`);
      checked++;
    }
  }
  // headline tiles
  const tiles=await p.$$eval('#panel-country .est .val',e=>e.map(x=>x.textContent));
  const want=[c.cumOut,c.cumIn,Math.abs(c.net)];
  tiles.forEach((t,i)=>{
    const got=parseFloat(t.replace(/[^0-9.]/g,''));
    if(Math.abs(got-want[i])>0.06) bad.push(`${c.name} tile${i}: ${got} vs ${want[i]}`);
    checked++;
  });
}
// fund tab: every fund and source rendered without error
await p.click('[data-tab="fund"]');
for(const side of ['funds','sources']){
  if(side==='sources') await p.click('#panel-fund .toggle button:text-is("What countries pay")');
  const list=side==='funds'?P.funds:P.sources;
  for(const f of list){
    await p.click(`#panel-fund .picker button:text-is("${f.label}")`);
    await p.waitForTimeout(30);
    const n=await p.$$eval('#panel-fund svg rect',e=>e.length);
    if(n<20) bad.push(`fund view ${f.label}: only ${n} bars`);
    checked++;
  }
}
console.log(`checked ${checked} rendered values across ${P.countries.length} countries`);
console.log(bad.length?('FAILURES:\n  '+bad.slice(0,20).join('\n  ')):'0 mismatches');
console.log('JS errors:',errs.length?errs.slice(0,3):'none');
await b.close();
process.exit(bad.length||errs.length?1:0);})();
