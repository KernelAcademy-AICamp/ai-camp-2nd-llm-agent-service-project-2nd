import { test, expect } from '@playwright/test';

/**
 * Production/Staging E2E Tests
 * 외부 배포 사이트 접속 테스트
 *
 * 사용법:
 *   BASE_URL=https://your-site.vercel.app npx playwright test e2e/production.spec.ts
 */

// 환경변수에서 URL 가져오기 (기본값: localhost)
const BASE_URL = process.env.BASE_URL || 'http://localhost:3000';

test.describe(`Production Site Test (${BASE_URL})`, () => {

  test('메인 페이지 접속', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('domcontentloaded');

    // 페이지 로드 확인
    await expect(page.locator('body')).toBeVisible();

    // 페이지 타이틀 출력
    const title = await page.title();
    console.log(`✅ 메인 페이지 로드 성공`);
    console.log(`   Title: ${title}`);
    console.log(`   URL: ${page.url()}`);

    await page.screenshot({ path: 'test-results/prod-homepage.png', fullPage: true });
  });

  test('로그인 페이지 접속', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState('domcontentloaded');

    // 로그인 폼 확인
    const emailInput = page.locator('input[type="email"]');
    await expect(emailInput).toBeVisible({ timeout: 15000 });

    console.log(`✅ 로그인 페이지 로드 성공`);
    console.log(`   URL: ${page.url()}`);

    await page.screenshot({ path: 'test-results/prod-login.png', fullPage: true });
  });

  test('회원가입 페이지 접속', async ({ page }) => {
    await page.goto(`${BASE_URL}/signup`);
    await page.waitForLoadState('domcontentloaded');

    // 회원가입 폼 확인
    const nameInput = page.locator('input[name="name"]');
    await expect(nameInput).toBeVisible({ timeout: 15000 });

    console.log(`✅ 회원가입 페이지 로드 성공`);
    console.log(`   URL: ${page.url()}`);

    await page.screenshot({ path: 'test-results/prod-signup.png', fullPage: true });
  });

  test('관계도 페이지 접속', async ({ page }) => {
    await page.goto(`${BASE_URL}/cases/1/relationship`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    console.log(`✅ 관계도 페이지 접속`);
    console.log(`   URL: ${page.url()}`);

    await page.screenshot({ path: 'test-results/prod-relationship.png', fullPage: true });

    await expect(page.locator('body')).toBeVisible();
  });

  test('404 페이지 처리 확인', async ({ page }) => {
    await page.goto(`${BASE_URL}/nonexistent-page-12345`);
    await page.waitForLoadState('domcontentloaded');

    console.log(`ℹ️  404 페이지 테스트`);
    console.log(`   URL: ${page.url()}`);

    await page.screenshot({ path: 'test-results/prod-404.png', fullPage: true });
  });

  test('페이지 로드 성능 측정', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    console.log(`⏱️  페이지 로드 시간: ${loadTime}ms`);

    // 5초 이내 로드 확인
    expect(loadTime).toBeLessThan(5000);
  });

  test('모바일 뷰 테스트', async ({ page }) => {
    // 모바일 뷰포트 설정
    await page.setViewportSize({ width: 375, height: 812 }); // iPhone X

    await page.goto(BASE_URL);
    await page.waitForLoadState('domcontentloaded');

    console.log(`📱 모바일 뷰 테스트`);

    await page.screenshot({ path: 'test-results/prod-mobile.png', fullPage: true });

    await expect(page.locator('body')).toBeVisible();
  });

  test('다크모드 확인 (시스템 설정)', async ({ page }) => {
    // 다크모드 에뮬레이션
    await page.emulateMedia({ colorScheme: 'dark' });

    await page.goto(BASE_URL);
    await page.waitForLoadState('domcontentloaded');

    console.log(`🌙 다크모드 테스트`);

    await page.screenshot({ path: 'test-results/prod-darkmode.png', fullPage: true });
  });
});
