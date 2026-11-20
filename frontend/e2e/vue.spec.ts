import { test, expect } from '@playwright/test';

// See here how to get started:
// https://playwright.dev/docs/intro
test('opens the map', async ({ page }) => {
  await page.goto('/');
  await expect(page.locator('.d3-map')).toBeVisible();
  await expect(page.locator('.year-ruler')).toBeVisible();
});
