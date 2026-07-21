const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => {
    if (msg.type() === 'error') {
      console.log('BROWSER ERROR:', msg.text());
    }
  });
  
  page.on('pageerror', err => {
    console.log('PAGE ERROR:', err.toString());
  });

  // Try multiple times to wait for the server
  for (let i = 0; i < 10; i++) {
    try {
      await page.goto('http://localhost:5173', { waitUntil: 'networkidle0', timeout: 5000 });
      console.log('Page loaded successfully');
      
      const errorText = await page.evaluate(() => {
        return document.body.innerText;
      });
      console.log('Body Text:', errorText.substring(0, 500));
      break;
    } catch (e) {
      console.log(`Attempt ${i} failed, retrying in 2s...`);
      await new Promise(r => setTimeout(r, 2000));
    }
  }

  await browser.close();
  process.exit(0);
})();
