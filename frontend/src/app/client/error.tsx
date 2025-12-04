/**
 * Client Portal Error Boundary
 * Shows error UI when an error occurs in the client portal
 */

'use client';

import { ClientPortalError } from '@/components/shared/ErrorBoundary';

export default function ClientError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <ClientPortalError error={error} reset={reset} />;
}
