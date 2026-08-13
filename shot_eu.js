const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  for (const mode of ['light','dark']) {
    const pg = await b.newPage({ viewport:{width:1160,height:1400}, colorScheme:mode, deviceScaleFactor:2 });
    const errs = []; pg.on('pageerror', e=>errs.push(String(e)));
    await pg.goto('file://' + process.cwd() + '/eu.html');
    await pg.waitForTimeout(700);
    console.log(mode, 'js errors:', errs.length?errs:'none');
    const bad = await pg.evaluate(() => {
      const out = [];
      document.querySelectorAll('.val').forEach(e => {
        const r = e.getBoundingClientRect(), p = e.parentElement.getBoundingClientRect();
        if (r.right > p.right + 1 || r.left < p.left - 1) out.push(e.textContent);
      });
      // anything spilling out of the page
      document.querySelectorAll('.card, svg, .kpi').forEach(e => {
        if (e.getBoundingClientRect().right > window.innerWidth) out.push('overflow: ' + e.tagName);
      });
      return out;
    });
    console.log(mode, 'layout problems:', bad.length?bad:'none');
    await pg.screenshot({ path:`eu-${mode}.png`, fullPage:true });
    await pg.close();
  }
  await b.close();
})();
