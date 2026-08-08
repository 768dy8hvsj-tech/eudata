const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  for (const mode of ['light', 'dark']) {
    const pg = await b.newPage({ viewport: { width: 1000, height: 1400 },
                                 colorScheme: mode, deviceScaleFactor: 2 });
    const errs = [];
    pg.on('pageerror', e => errs.push(String(e)));
    await pg.goto('file://' + process.cwd() + '/iceland-dashboard.html');
    await pg.waitForTimeout(700);
    const card = await pg.locator('.card').filter({ hasText: 'What it already pays' }).first();
    const n = await card.count();
    console.log(mode, '| offsets card found:', n > 0, '| js errors:', errs.length ? errs : 'none');
    if (n) await card.screenshot({ path: `offsets-${mode}.png` });
    // overflow / collision check on the value labels
    const bad = await pg.evaluate(() => {
      const out = [];
      document.querySelectorAll('.ofval').forEach(e => {
        const r = e.getBoundingClientRect(), p = e.parentElement.getBoundingClientRect();
        if (r.right > p.right + 1 || r.left < p.left - 1) out.push(e.textContent);
      });
      return out;
    });
    console.log(mode, '| labels outside their track:', bad.length ? bad : 'none');
    await pg.close();
  }
  await b.close();
})();
