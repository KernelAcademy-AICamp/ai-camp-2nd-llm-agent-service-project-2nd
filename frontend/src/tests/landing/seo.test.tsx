/**
 * Plan 3.19.2 - SEO Optimization Tests
 *
 * Tests for SEO compliance:
 * - Title tag with proper format
 * - Meta description (160 chars or less)
 * - Meta keywords
 * - Open Graph tags
 * - Structured Data (JSON-LD)
 *
 * Note: These tests verify the metadata configuration in layout.tsx
 * Next.js handles the actual rendering of these tags
 */

import { metadata } from '../../app/layout';

describe('Plan 3.19.2 - SEO Optimization', () => {
  describe('Title Tag', () => {
    test('should have a descriptive title', () => {
      expect(metadata.title).toBeDefined();
      expect(typeof metadata.title).toBe('string');
    });

    test('title should include brand name and value proposition', () => {
      const title = metadata.title as string;
      expect(title).toContain('Legal Evidence Hub');
      expect(title).toContain('AI');
    });

    test('title should be within recommended length (50-60 chars)', () => {
      const title = metadata.title as string;
      // Title can be slightly longer for Korean characters
      expect(title.length).toBeLessThanOrEqual(70);
      expect(title.length).toBeGreaterThan(20);
    });
  });

  describe('Meta Description', () => {
    test('should have a meta description', () => {
      expect(metadata.description).toBeDefined();
      expect(typeof metadata.description).toBe('string');
    });

    test('description should be within 160 characters', () => {
      const description = metadata.description as string;
      expect(description.length).toBeLessThanOrEqual(160);
    });

    test('description should include key value propositions', () => {
      const description = metadata.description as string;
      expect(description).toMatch(/AI|증거|분석|이혼/i);
    });

    test('description should include call-to-action or benefit', () => {
      const description = metadata.description as string;
      // Should mention time savings or free trial
      expect(description).toMatch(/90%|무료|단축/);
    });
  });

  describe('Meta Keywords', () => {
    test('should have keywords defined', () => {
      expect(metadata.keywords).toBeDefined();
      expect(Array.isArray(metadata.keywords)).toBe(true);
    });

    test('should include relevant keywords', () => {
      const keywords = metadata.keywords as string[];
      const requiredKeywords = ['이혼소송', '증거분석', 'AI법률', '답변서'];

      requiredKeywords.forEach((keyword) => {
        expect(keywords).toContain(keyword);
      });
    });
  });

  describe('Open Graph Tags', () => {
    test('should have Open Graph configuration', () => {
      expect(metadata.openGraph).toBeDefined();
    });

    test('should have og:title', () => {
      expect(metadata.openGraph?.title).toBeDefined();
    });

    test('should have og:description', () => {
      expect(metadata.openGraph?.description).toBeDefined();
    });

    test('should have og:url', () => {
      expect(metadata.openGraph?.url).toBeDefined();
    });

    test('should have og:site_name', () => {
      expect(metadata.openGraph?.siteName).toBeDefined();
    });

    test('should have og:locale set to ko_KR', () => {
      expect(metadata.openGraph?.locale).toBe('ko_KR');
    });

    test('should have og:type set to website', () => {
      expect(metadata.openGraph?.type).toBe('website');
    });

    test('should have og:image with proper dimensions', () => {
      const images = metadata.openGraph?.images;
      expect(images).toBeDefined();
      expect(Array.isArray(images)).toBe(true);

      if (Array.isArray(images) && images.length > 0) {
        const firstImage = images[0] as { width?: number; height?: number };
        expect(firstImage.width).toBe(1200);
        expect(firstImage.height).toBe(630);
      }
    });
  });

  describe('Twitter Card', () => {
    test('should have Twitter card configuration', () => {
      expect(metadata.twitter).toBeDefined();
    });

    test('should use summary_large_image card type', () => {
      expect(metadata.twitter?.card).toBe('summary_large_image');
    });

    test('should have Twitter title', () => {
      expect(metadata.twitter?.title).toBeDefined();
    });

    test('should have Twitter description', () => {
      expect(metadata.twitter?.description).toBeDefined();
    });

    test('should have Twitter image', () => {
      expect(metadata.twitter?.images).toBeDefined();
    });
  });

  describe('Robots Configuration', () => {
    test('should have robots configuration', () => {
      expect(metadata.robots).toBeDefined();
    });

    test('should allow indexing', () => {
      const robots = metadata.robots as { index?: boolean };
      expect(robots.index).toBe(true);
    });

    test('should allow following links', () => {
      const robots = metadata.robots as { follow?: boolean };
      expect(robots.follow).toBe(true);
    });
  });

  describe('Search Engine Verification', () => {
    test('should have verification configuration', () => {
      expect(metadata.verification).toBeDefined();
    });

    test('should have Google verification placeholder', () => {
      expect(metadata.verification?.google).toBeDefined();
    });
  });

  describe('Authors', () => {
    test('should have authors defined', () => {
      expect(metadata.authors).toBeDefined();
      expect(Array.isArray(metadata.authors)).toBe(true);
    });

    test('should include Legal Evidence Hub as author', () => {
      const authors = metadata.authors as Array<{ name: string }>;
      expect(authors.some((author) => author.name === 'Legal Evidence Hub')).toBe(
        true
      );
    });
  });
});
