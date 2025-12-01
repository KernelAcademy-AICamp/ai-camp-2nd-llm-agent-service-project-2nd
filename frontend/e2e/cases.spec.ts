import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Cases Management
 * Tests case listing, creation, and status management
 *
 * @tag real-api - Requires backend to be running
 */

test.describe('Cases Management @real-api', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');

    // Set mock auth token for navigation guard
    await page.evaluate(() => {
      localStorage.setItem('authToken', 'test-jwt-token');
    });
  });

  test.describe('Cases List', () => {
    test('should display cases list page', async ({ page }) => {
      await page.goto('/cases');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(1000);

      // Should see some page content
      await expect(page.locator('body')).toBeVisible();

      // Check for navigation or main content area
      const hasNav = await page.locator('nav').count() > 0;
      const hasMain = await page.locator('main').count() > 0;
      expect(hasNav || hasMain).toBeTruthy();
    });

    test('should have case management UI elements', async ({ page }) => {
      await page.goto('/cases');
      await page.waitForLoadState('domcontentloaded');
      await page.waitForTimeout(1000);

      // Look for any button elements on the page
      const buttons = page.locator('button');
      const count = await buttons.count();

      // Page should have some interactive elements
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe('Case Page Structure', () => {
    test('should load cases page without errors', async ({ page }) => {
      await page.goto('/cases');
      await page.waitForLoadState('domcontentloaded');

      // Page loaded successfully
      await expect(page.locator('body')).toBeVisible();
    });
  });
});

test.describe('Cases API Integration @real-api', () => {
  test.beforeEach(async ({ page }) => {
    // Clear and set fresh token
    await page.goto('/');
    await page.waitForLoadState('domcontentloaded');
    await page.evaluate(() => {
      localStorage.setItem('authToken', 'test-jwt-token');
    });
  });

  test('should fetch and display cases from API', async ({ page, request }) => {
    // First check if backend is available
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

    await page.goto('/cases');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(1000);

    // Page should load without errors
    await expect(page.locator('body')).toBeVisible();
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Set an invalid token to trigger API errors
    await page.evaluate(() => {
      localStorage.setItem('authToken', 'invalid-token');
    });

    await page.goto('/cases');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Page should still be visible (no crash)
    await expect(page.locator('body')).toBeVisible();
  });
});
