const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  for (const [iso, f] of [['NOR','norway'],['ISL','iceland'],['CHE','switzerland']]) {
    const pg = await b.newPage({ viewport:{width:1000,height:1400}, deviceScaleFactor:2 });
    const errs = []; pg.on('pageerror', e => errs.push(String(e)));
    await pg.goto('file://' + process.cwd() + `/${f}-dashboard.html`);
    await pg.waitForTimeout(600);
    const card = pg.locator('.card').filter({ hasText: 'The five exclusive competences' }).first();
    const n = await card.count();
    console.log(`${iso} card:${n>0} errors:${errs.length?errs:'none'}`);
    if (n && iso === 'CHE') await card.screenshot({ path: 'competence-che.png' });
    if (n && iso === 'NOR') await card.screenshot({ path: 'competence-nor.png' });
    await pg.close();
  }
  await b.close();
})();
