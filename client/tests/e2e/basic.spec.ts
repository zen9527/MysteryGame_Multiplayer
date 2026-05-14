import { test, expect } from '@playwright/test';

test.describe('Basic Navigation', () => {
  test('should load home page', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/剧本杀/);
  });

  test('should navigate to scripts page', async ({ page }) => {
    await page.goto('/scripts');
    await expect(page).toHaveURL('/scripts');
  });

  test('should navigate to settings page', async ({ page }) => {
    await page.goto('/settings');
    await expect(page).toHaveURL('/settings');
  });
});
