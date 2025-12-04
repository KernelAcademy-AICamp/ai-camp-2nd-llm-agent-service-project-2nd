/**
 * Custom 404 Page for SPA-style routing with Static Export
 *
 * When S3 returns 404, CloudFront serves this page.
 * This page then checks if the URL should be handled by client-side routing
 * and redirects appropriately.
 */

import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';

export default function Custom404() {
  const router = useRouter();

  useEffect(() => {
    // Get the current path from the URL
    const path = window.location.pathname;

    // List of known client-side routes that should be handled by the app
    const dynamicRoutes = [
      /^\/cases\/[^/]+\/?$/,  // /cases/[id]
    ];

    // Check if current path matches a dynamic route
    const isDynamicRoute = dynamicRoutes.some(pattern => pattern.test(path));

    if (isDynamicRoute) {
      // For dynamic routes, push to router to handle client-side
      // This preserves the URL and lets Next.js handle the routing
      router.replace(path);
    }
    // For truly unknown routes, just show the 404 page
  }, [router]);

  return (
    <>
      <Head>
        <title>페이지를 찾을 수 없습니다 | Legal Evidence Hub</title>
      </Head>
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <div className="text-center">
          <h1 className="text-6xl font-bold text-gray-300 mb-4">404</h1>
          <p className="text-xl text-gray-600 mb-8">페이지를 찾을 수 없습니다</p>
          <button
            onClick={() => router.push('/cases')}
            className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            사건 목록으로 돌아가기
          </button>
        </div>
      </div>
    </>
  );
}
