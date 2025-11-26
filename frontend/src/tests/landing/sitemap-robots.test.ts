/**
 * Plan 3.19.4 - SEO Tests for Sitemap and Robots.txt
 *
 * Tests for:
 * - sitemap.xml generation
 * - robots.txt configuration
 */

import sitemap from '../../app/sitemap';
import robots from '../../app/robots';

describe('Plan 3.19.4 - Sitemap.xml', () => {
  test('should return a MetadataRoute.Sitemap array', () => {
    const result = sitemap();
    expect(Array.isArray(result)).toBe(true);
    expect(result.length).toBeGreaterThan(0);
  });

  test('should include homepage with highest priority', () => {
    const result = sitemap();
    const homepage = result.find((item) => item.url.endsWith('/'));

    expect(homepage).toBeDefined();
    expect(homepage?.priority).toBe(1);
    expect(homepage?.changeFrequency).toBe('weekly');
  });

  test('should include login page', () => {
    const result = sitemap();
    const loginPage = result.find((item) => item.url.includes('/login'));

    expect(loginPage).toBeDefined();
    expect(loginPage?.priority).toBeGreaterThanOrEqual(0.5);
  });

  test('should include signup page', () => {
    const result = sitemap();
    const signupPage = result.find((item) => item.url.includes('/signup'));

    expect(signupPage).toBeDefined();
    expect(signupPage?.priority).toBeGreaterThanOrEqual(0.7);
  });

  test('should have valid URL format for all entries', () => {
    const result = sitemap();
    const baseUrl = 'https://legalevidence.hub';

    result.forEach((item) => {
      expect(item.url).toMatch(/^https:\/\//);
      expect(item.url).toContain(baseUrl);
    });
  });

  test('should have lastModified date for all entries', () => {
    const result = sitemap();

    result.forEach((item) => {
      expect(item.lastModified).toBeDefined();
    });
  });

  test('should have valid changeFrequency values', () => {
    const result = sitemap();
    const validFrequencies = ['always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never'];

    result.forEach((item) => {
      if (item.changeFrequency) {
        expect(validFrequencies).toContain(item.changeFrequency);
      }
    });
  });

  test('should have priority values between 0 and 1', () => {
    const result = sitemap();

    result.forEach((item) => {
      if (item.priority !== undefined) {
        expect(item.priority).toBeGreaterThanOrEqual(0);
        expect(item.priority).toBeLessThanOrEqual(1);
      }
    });
  });
});

describe('Plan 3.19.4 - Robots.txt', () => {
  test('should return a MetadataRoute.Robots object', () => {
    const result = robots();
    expect(result).toBeDefined();
    expect(typeof result).toBe('object');
  });

  test('should have rules array', () => {
    const result = robots();
    expect(result.rules).toBeDefined();
  });

  test('should allow all user agents to crawl public pages', () => {
    const result = robots();
    const rules = Array.isArray(result.rules) ? result.rules : [result.rules];

    const allBotRule = rules.find((rule) => rule.userAgent === '*');
    expect(allBotRule).toBeDefined();
    expect(allBotRule?.allow).toBeDefined();
  });

  test('should disallow crawling of private/admin pages', () => {
    const result = robots();
    const rules = Array.isArray(result.rules) ? result.rules : [result.rules];

    const allBotRule = rules.find((rule) => rule.userAgent === '*');
    const disallowedPaths = allBotRule?.disallow;

    expect(disallowedPaths).toBeDefined();

    const disallowArray = Array.isArray(disallowedPaths) ? disallowedPaths : [disallowedPaths];
    expect(disallowArray).toContain('/admin');
    expect(disallowArray).toContain('/cases');
    expect(disallowArray).toContain('/api');
  });

  test('should include sitemap URL', () => {
    const result = robots();
    expect(result.sitemap).toBeDefined();
    expect(result.sitemap).toContain('sitemap.xml');
  });

  test('should have valid sitemap URL format', () => {
    const result = robots();
    expect(result.sitemap).toMatch(/^https:\/\/.+\/sitemap\.xml$/);
  });

  test('should disallow settings page', () => {
    const result = robots();
    const rules = Array.isArray(result.rules) ? result.rules : [result.rules];

    const allBotRule = rules.find((rule) => rule.userAgent === '*');
    const disallowedPaths = allBotRule?.disallow;
    const disallowArray = Array.isArray(disallowedPaths) ? disallowedPaths : [disallowedPaths];

    expect(disallowArray).toContain('/settings');
  });
});
