/**
 * Lawyer Portal Error Boundary
 * Shows error UI when an error occurs in the lawyer portal
 */

'use client';

import { LawyerPortalError } from '@/components/shared/ErrorBoundary';

export default function LawyerError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <LawyerPortalError error={error} reset={reset} />;
}
