import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Authentication Flow
 * Tests login, signup, and navigation guard functionality
 */

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.evaluate(() => localStorage.clear());
  });

  test.describe('Login Page', () => {
    test('should display login form', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      // Use locator by id which matches the htmlFor attribute
      await expect(page.locator('#email')).toBeVisible();
      await expect(page.locator('#password')).toBeVisible();
      await expect(page.getByRole('button', { name: /로그인/i })).toBeVisible();
    });

    test('should login and redirect to /cases', async ({ page }) => {
      await page.goto('/login');
      await page.waitForLoadState('networkidle');

      // Fill login form using id selectors
      await page.locator('#email').fill('test@example.com');
      await page.locator('#password').fill('password123');

      // Click login button
      await page.getByRole('button', { name: /로그인/i }).click();

      // Wait for redirect to /cases
      await expect(page).toHaveURL(/\/cases/, { timeout: 10000 });

      // Verify authToken is set
      const token = await page.evaluate(() => localStorage.getItem('authToken'));
      expect(token).toBeTruthy();
    });
  });

  test.describe('Signup Page', () => {
    test('should display signup form', async ({ page }) => {
      await page.goto('/signup');
      await page.waitForLoadState('networkidle');

      await expect(page.locator('#name')).toBeVisible();
      await expect(page.locator('#email')).toBeVisible();
      await expect(page.locator('#password')).toBeVisible();
      await expect(page.getByRole('button', { name: /무료 체험 시작/i })).toBeVisible();
    });

    test('should show error for short password', async ({ page }) => {
      await page.goto('/signup');
      await page.waitForLoadState('networkidle');

      await page.locator('#name').fill('홍길동');
      await page.locator('#email').fill('test@example.com');
      await page.locator('#password').fill('short');

      await page.getByRole('button', { name: /무료 체험 시작/i }).click();

      // Wait for error message
      await expect(page.getByText(/비밀번호는 8자 이상/i)).toBeVisible({ timeout: 5000 });
    });

    test('should signup and redirect to /cases', async ({ page }) => {
      await page.goto('/signup');
      await page.waitForLoadState('networkidle');

      await page.locator('#name').fill('홍길동');
      await page.locator('#email').fill('test@example.com');
      await page.locator('#password').fill('password123');

      await page.getByRole('button', { name: /무료 체험 시작/i }).click();

      // Wait for redirect to /cases
      await expect(page).toHaveURL(/\/cases/, { timeout: 10000 });

      // Verify authToken is set
      const token = await page.evaluate(() => localStorage.getItem('authToken'));
      expect(token).toBeTruthy();
    });
  });

  test.describe('Navigation Guard', () => {
    test('should redirect unauthenticated user from /cases to /login', async ({ page }) => {
      // Ensure no auth token
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await page.evaluate(() => localStorage.clear());

      // Try to access /cases directly
      await page.goto('/cases');
      await page.waitForLoadState('networkidle');

      // Should redirect to /login (wait longer for client-side redirect)
      await expect(page).toHaveURL(/\/login/, { timeout: 10000 });
    });

    test('should allow authenticated user to access /cases', async ({ page }) => {
      // Set auth token first via /login page
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      await page.evaluate(() => {
        localStorage.setItem('authToken', 'mock-jwt-token-e2e-test');
      });

      // Navigate to /cases
      await page.goto('/cases');
      await page.waitForLoadState('networkidle');

      // Should stay on /cases (check URL contains /cases)
      await expect(page).toHaveURL(/\/cases/);

      // Should see cases page content (check for the nav or main content)
      await expect(page.locator('nav')).toBeVisible();
    });
  });

  test.describe('Landing Page', () => {
    test('should display landing page for unauthenticated user', async ({ page }) => {
      await page.goto('/');
      await page.waitForLoadState('networkidle');

      // Should see landing page - check for navigation or main content
      await expect(page.locator('main')).toBeVisible();
    });

    test('should redirect authenticated user from landing to /cases', async ({ page }) => {
      // Set auth token
      await page.goto('/login');
      await page.waitForLoadState('networkidle');
      await page.evaluate(() => {
        localStorage.setItem('authToken', 'mock-jwt-token-e2e-test');
      });

      // Navigate to landing page
      await page.goto('/');

      // Should redirect to /cases
      await expect(page).toHaveURL(/\/cases/, { timeout: 10000 });
    });
  });
});
