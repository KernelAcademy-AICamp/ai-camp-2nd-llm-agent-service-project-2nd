/**
 * RoleGuard Component
 * 003-role-based-ui Feature
 *
 * Protects routes based on user role.
 * Renders children only if user has required role/permission.
 */

'use client';

import { ReactNode, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useRole } from '@/hooks/useRole';
import { UserRole } from '@/types/user';

interface RoleGuardProps {
  /** Children to render if access is granted */
  children: ReactNode;
  /** Required roles (user must have one of these) */
  allowedRoles?: UserRole[];
  /** Required feature access */
  requiredFeature?: string;
  /** Where to redirect if access denied (default: /login) */
  redirectTo?: string;
  /** Show loading state while checking auth */
  showLoading?: boolean;
  /** Custom fallback component when access denied */
  fallback?: ReactNode;
}

/**
 * RoleGuard - Protects routes based on user role
 *
 * Usage:
 * ```tsx
 * // Allow only lawyers
 * <RoleGuard allowedRoles={['lawyer', 'admin']}>
 *   <LawyerDashboard />
 * </RoleGuard>
 *
 * // Check feature access
 * <RoleGuard requiredFeature="billing">
 *   <BillingPage />
 * </RoleGuard>
 * ```
 */
export function RoleGuard({
  children,
  allowedRoles,
  requiredFeature,
  redirectTo = '/login',
  showLoading = true,
  fallback,
}: RoleGuardProps) {
  const router = useRouter();
  const { user, role, isAuthenticated, hasAccess } = useRole();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    // Client-side auth check
    const checkAccess = () => {
      // Not authenticated
      if (!isAuthenticated) {
        if (fallback) {
          setIsChecking(false);
          return;
        }
        router.push(redirectTo);
        return;
      }

      // Check role requirement
      if (allowedRoles && role && !allowedRoles.includes(role)) {
        if (fallback) {
          setIsChecking(false);
          return;
        }
        router.push(redirectTo);
        return;
      }

      // Check feature requirement
      if (requiredFeature && !hasAccess(requiredFeature)) {
        if (fallback) {
          setIsChecking(false);
          return;
        }
        router.push(redirectTo);
        return;
      }

      setIsChecking(false);
    };

    // Small delay to allow localStorage to be read
    const timer = setTimeout(checkAccess, 50);
    return () => clearTimeout(timer);
  }, [isAuthenticated, role, allowedRoles, requiredFeature, hasAccess, redirectTo, router, fallback]);

  // Show loading state
  if (isChecking && showLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
      </div>
    );
  }

  // Check access for fallback rendering
  if (!isAuthenticated) {
    return fallback ? <>{fallback}</> : null;
  }

  if (allowedRoles && role && !allowedRoles.includes(role)) {
    return fallback ? <>{fallback}</> : null;
  }

  if (requiredFeature && !hasAccess(requiredFeature)) {
    return fallback ? <>{fallback}</> : null;
  }

  return <>{children}</>;
}

/**
 * AccessDenied - Default fallback component
 */
export function AccessDenied({ message }: { message?: string }) {
  const router = useRouter();
  const { dashboardPath, roleDisplayName } = useRole();

  return (
    <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-8">
      <div className="w-16 h-16 mb-4 rounded-full bg-[var(--color-error-light)] flex items-center justify-center">
        <svg
          className="w-8 h-8 text-[var(--color-error)]"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>
      <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
        접근 권한이 없습니다
      </h2>
      <p className="text-[var(--color-text-secondary)] mb-6 max-w-md">
        {message || `현재 ${roleDisplayName || '사용자'} 역할로는 이 페이지에 접근할 수 없습니다.`}
      </p>
      <button
        onClick={() => router.push(dashboardPath)}
        className="px-6 py-2 rounded-lg bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] transition-colors"
      >
        대시보드로 이동
      </button>
    </div>
  );
}

export default RoleGuard;
