/**
 * Detective Portal Error Boundary
 * Shows error UI when an error occurs in the detective portal
 */

'use client';

import { DetectivePortalError } from '@/components/shared/ErrorBoundary';

export default function DetectiveError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <DetectivePortalError error={error} reset={reset} />;
}
