import { test, expect } from '@playwright/test';

test('character creation flow', async ({ page }) => {
  await page.goto('/');
  await page.click('text=Register');
  const username = `TestUser_${Date.now()}`;
  await page.fill('input[type="text"]', username);
  await page.fill('input[type="password"]', 'password123');
  await page.click('button:has-text("Forge Credentials")');
  await expect(page.locator('text=UPLINK ESTABLISHED: SELECT PROTOCOL')).toBeVisible();
  await page.click('button:has-text("Commence Solo Journey")');
  
  await expect(page.locator('text=Manifest')).toBeVisible();
  await page.fill('input[placeholder="Enter your name..."]', 'John E2E');
  
  // Wait for the UI to be fully rendered before taking a screenshot
  await page.waitForTimeout(500); 
  await expect(page).toHaveScreenshot('character-creation.png', { fullPage: true, maxDiffPixelRatio: 0.1 });
  
  await page.click('button:has-text("Begin Journey")');
  
  // Wait for the character to be created and chat to show up
  await expect(page.locator('text=Dossier')).toBeVisible({ timeout: 15000 });
});
