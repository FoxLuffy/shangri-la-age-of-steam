# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: market.spec.ts >> market trading flow
- Location: e2e\market.spec.ts:3:1

# Error details

```
Test timeout of 60000ms exceeded.
```

```
Error: page.click: Test timeout of 60000ms exceeded.
Call log:
  - waiting for locator('text=Register')

```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test('market trading flow', async ({ page }) => {
  4  |   test.setTimeout(60000); // 60s timeout for this long test
  5  |   
  6  |   await page.goto('/');
> 7  |   await page.click('text=Register');
     |              ^ Error: page.click: Test timeout of 60000ms exceeded.
  8  |   const username = `MarketUser_${Date.now()}`;
  9  |   await page.fill('input[type="text"]', username);
  10 |   await page.fill('input[type="password"]', 'password123');
  11 |   await page.click('button:has-text("Forge Credentials")');
  12 |   
  13 |   await expect(page.locator('text=UPLINK ESTABLISHED: SELECT PROTOCOL')).toBeVisible();
  14 |   await page.click('button:has-text("Commence Solo Journey")');
  15 |   
  16 |   await expect(page.locator('text=Manifest')).toBeVisible();
  17 |   await page.fill('input[placeholder="Enter your name..."]', 'Trader Joe');
  18 |   await page.click('button:has-text("Begin Journey")');
  19 |   
  20 |   // Wait for game UI to load
  21 |   await expect(page.locator('text=Dossier')).toBeVisible({ timeout: 15000 });
  22 |   await page.waitForTimeout(1000);
  23 |   
  24 |   await expect(page).toHaveScreenshot('chat-interface.png', { fullPage: true, maxDiffPixelRatio: 0.1 });
  25 |   
  26 |   // Wait for Market button to appear (needs worldState to load)
  27 |   await expect(page.locator('button:has-text("Market")')).toBeVisible({ timeout: 15000 });
  28 |   await page.click('button:has-text("Market")');
  29 |   
  30 |   await expect(page.locator('text=Global Resource Exchange')).toBeVisible();
  31 |   await page.waitForTimeout(1000); // Give time for market prices to fetch
  32 |   await expect(page).toHaveScreenshot('market-ui.png', { fullPage: true, maxDiffPixelRatio: 0.1 });
  33 | });
  34 | 
```