const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  for (const mode of ['light','dark']) {
    const pg = await b.newPage({ viewport:{width:1100,height:1400}, colorScheme:mode, deviceScaleFactor:2 });
    const errs=[]; pg.on('pageerror',e=>errs.push(String(e)));
    await pg.goto('file://' + process.cwd() + '/germany-dashboard.html');
    await pg.waitForTimeout(500);
    await pg.locator('nav.tabs button',{hasText:'Financial'}).first().click();
    await pg.waitForTimeout(500);
    // hover the first chip so the tooltip is in the shot
    await pg.locator('.rankchip').first().hover();
    await pg.waitForTimeout(250);
    const wrap = await pg.evaluate(() => {
      const out=[];
      document.querySelectorAll('.h3row').forEach(r=>{
        const h3=r.querySelector('h3'), c=r.querySelector('.rankchip');
        if (h3&&c && c.getBoundingClientRect().top > h3.getBoundingClientRect().bottom-2)
          out.push('chip wrapped below title: '+h3.textContent);
      });
      return out;
    });
    console.log(mode,'errors:',errs.length?errs:'none','| layout:',wrap.length?wrap:'ok');
    if (mode==='light') await pg.screenshot({path:'rank-light.png', clip:{x:0,y:0,width:1100,height:900}});
    await pg.close();
  }
  await b.close();
})();
