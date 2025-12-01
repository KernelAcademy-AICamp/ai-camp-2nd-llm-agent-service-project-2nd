/**
 * Robots.txt configuration for SEO
 * Plan 3.19.4 - SEO Optimization
 *
 * Controls search engine crawler behavior
 * https://nextjs.org/docs/app/api-reference/file-conventions/metadata/robots
 */

import { MetadataRoute } from 'next';

const BASE_URL = 'https://legalevidence.hub';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: ['/admin', '/cases', '/api', '/settings'],
    },
    sitemap: `${BASE_URL}/sitemap.xml`,
  };
}
