import { test, expect } from '@playwright/test';

test('market trading flow', async ({ page }) => {
  test.setTimeout(60000); // 60s timeout for this long test
  
  await page.goto('/');
  await page.click('text=Register');
  const username = `MarketUser_${Date.now()}`;
  await page.fill('input[type="text"]', username);
  await page.fill('input[type="password"]', 'password123');
  await page.click('button:has-text("Forge Credentials")');
  
  await expect(page.locator('text=UPLINK ESTABLISHED: SELECT PROTOCOL')).toBeVisible();
  await page.click('button:has-text("Commence Solo Journey")');
  
  await expect(page.locator('text=Manifest')).toBeVisible();
  await page.fill('input[placeholder="Enter your name..."]', 'Trader Joe');
  await page.click('button:has-text("Begin Journey")');
  
  // Wait for game UI to load
  await expect(page.locator('text=Dossier')).toBeVisible({ timeout: 15000 });
  await page.waitForTimeout(1000);
  
  await expect(page).toHaveScreenshot('chat-interface.png', { fullPage: true, maxDiffPixelRatio: 0.1 });
  
  // Wait for Market button to appear (needs worldState to load)
  await expect(page.locator('button:has-text("Market")')).toBeVisible({ timeout: 15000 });
  await page.click('button:has-text("Market")');
  
  await expect(page.locator('text=Global Resource Exchange')).toBeVisible();
  await page.waitForTimeout(1000); // Give time for market prices to fetch
  await expect(page).toHaveScreenshot('market-ui.png', { fullPage: true, maxDiffPixelRatio: 0.1 });
});
