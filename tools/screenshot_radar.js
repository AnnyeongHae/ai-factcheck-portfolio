const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

async function run() {
  const browser = await puppeteer.launch({
    headless: 'new',
    executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });
  await page.goto('http://localhost:3000/#home', { waitUntil: 'networkidle0' });
  await page.waitForSelector('#trendRadarBullets');
  await new Promise(r => setTimeout(r, 1500));

  const radarCard = await page.$('#trendRadarTitle');
  const parentBox = await page.evaluateHandle(el => el ? el.closest('.bg-white.p-5.rounded-2xl') : null, radarCard);

  const outDir = 'C:\\Users\\user\\.gemini\\antigravity\\brain\\9aaa23ae-7653-43c7-8762-06450b3f867e\\.user_uploaded';

  for (let s = 1; s <= 4; s++) {
    await page.click(`#radarBtn${s}`);
    await new Promise(r => setTimeout(r, 400));
    const outPath = path.join(outDir, `radar_screenshot_s${s}.png`);
    if (parentBox && parentBox.asElement()) {
      await parentBox.asElement().screenshot({ path: outPath });
      console.log(`Saved session ${s} screenshot to`, outPath);
    }
  }

  await browser.close();
}
run().catch(err => {
  console.error(err);
  process.exit(1);
});
