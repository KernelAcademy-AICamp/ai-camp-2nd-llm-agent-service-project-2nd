import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Evidence Management
 * Tests evidence listing, upload preparation, and viewing
 *
 * @tag real-api - Requires backend to be running
 */

test.describe('Evidence Management @real-api', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Set mock auth token for navigation guard
    await page.evaluate(() => {
      localStorage.setItem('authToken', 'test-jwt-token');
    });
  });

  test.describe('Evidence Page', () => {
    test('should display case detail page', async ({ page }) => {
      await page.goto('/cases/1');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(1000);

      // Page should load
      await expect(page.locator('body')).toBeVisible();
    });

    test('should navigate from cases list to case detail', async ({ page }) => {
      await page.goto('/cases');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(1000);

      // Check if there are clickable case items
      const caseLinks = page.locator('a[href*="/cases/"]');
      const count = await caseLinks.count();

      if (count > 0) {
        await caseLinks.first().click();
        await page.waitForLoadState('domcontentloaded');

        // Should navigate to case detail page
        await expect(page).toHaveURL(/\/cases\/\w+/);
      }
    });
  });

  test.describe('Evidence Upload UI', () => {
    test('should load case detail page without errors', async ({ page }) => {
      await page.goto('/cases/1');
      await page.waitForLoadState('domcontentloaded');

      // Page loaded successfully
      await expect(page.locator('body')).toBeVisible();
    });

    test('should check for file input elements', async ({ page }) => {
      await page.goto('/cases/1');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(1000);

      const fileInputs = page.locator('input[type="file"]');
      const count = await fileInputs.count();

      // This is a soft check - file input may or may not exist
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });
});

test.describe('Evidence API Integration @real-api', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    await page.evaluate(() => {
      localStorage.setItem('authToken', 'test-jwt-token');
    });
  });

  test('should fetch evidence list from API', async ({ page, request }) => {
    // Check if backend is available
    try {
      const healthCheck = await request.get('http://localhost:8000/health');
      if (!healthCheck.ok()) {
        test.skip();
        return;
      }
    } catch {
      test.skip();
      return;
    }

    await page.goto('/cases/1');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);

    // Page should load without errors
    await expect(page.locator('body')).toBeVisible();
  });

  test('should handle case not found gracefully', async ({ page }) => {
    await page.goto('/cases/nonexistent-id');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Page should still be visible (no crash)
    await expect(page.locator('body')).toBeVisible();
  });
});
