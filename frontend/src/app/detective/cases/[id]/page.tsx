/**
 * Detective Investigation Detail Page - Server Component
 * 003-role-based-ui Feature - US5 (T103)
 *
 * Server component wrapper for static export compatibility.
 */

import DetectiveCaseDetailClient from './DetectiveCaseDetailClient';

// Required for static export with dynamic routes
// Pre-render sample case pages; additional routes are handled at request time
export function generateStaticParams() {
  return [
    { id: '1' },
    { id: '2' },
    { id: '3' },
  ];
}

// Allow dynamic routes not listed in generateStaticParams
export const dynamicParams = true;

interface PageProps {
  params: { id: string };
}

export default function DetectiveCaseDetailPage({ params }: PageProps) {
  return <DetectiveCaseDetailClient caseId={params.id} />;
}
