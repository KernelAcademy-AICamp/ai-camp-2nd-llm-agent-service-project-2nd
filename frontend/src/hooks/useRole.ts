/**
 * useRole Hook
 * 003-role-based-ui Feature
 *
 * Provides role-based access control utilities for components.
 */

'use client';

import { useMemo, useCallback } from 'react';
import {
  UserRole,
  User,
  hasFeatureAccess,
  getDashboardPath,
  getPortalPath,
  isInternalUser,
  isExternalUser,
  ROLE_DISPLAY_NAMES,
} from '@/types/user';

interface UseRoleReturn {
  // User data
  user: User | null;
  role: UserRole | null;
  isAuthenticated: boolean;

  // Role checks
  isAdmin: boolean;
  isLawyer: boolean;
  isStaff: boolean;
  isClient: boolean;
  isDetective: boolean;
  isInternal: boolean;
  isExternal: boolean;

  // Display
  roleDisplayName: string;

  // Navigation
  dashboardPath: string;
  portalPath: string;

  // Utilities
  hasAccess: (feature: string) => boolean;
  canAccessPortal: (portal: 'lawyer' | 'client' | 'detective' | 'admin') => boolean;
}

/**
 * Get user data from localStorage (client-side only)
 */
function getUserFromStorage(): User | null {
  if (typeof window === 'undefined') return null;

  try {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      return JSON.parse(userStr) as User;
    }
  } catch {
    // Invalid JSON in storage
  }
  return null;
}

/**
 * Hook for role-based access control
 *
 * Usage:
 * ```tsx
 * const { role, isLawyer, hasAccess, dashboardPath } = useRole();
 *
 * if (!hasAccess('billing')) {
 *   return <AccessDenied />;
 * }
 * ```
 */
export function useRole(): UseRoleReturn {
  const user = useMemo(() => getUserFromStorage(), []);
  const role = user?.role || null;

  const isAuthenticated = user !== null;
  const isAdmin = role === 'admin';
  const isLawyer = role === 'lawyer';
  const isStaff = role === 'staff';
  const isClient = role === 'client';
  const isDetective = role === 'detective';
  const isInternal = role ? isInternalUser(role) : false;
  const isExternal = role ? isExternalUser(role) : false;

  const roleDisplayName = role ? ROLE_DISPLAY_NAMES[role] : '';
  const dashboardPath = role ? getDashboardPath(role) : '/login';
  const portalPath = role ? getPortalPath(role) : '/';

  const hasAccess = useCallback(
    (feature: string): boolean => {
      if (!role) return false;
      return hasFeatureAccess(role, feature);
    },
    [role]
  );

  const canAccessPortal = useCallback(
    (portal: 'lawyer' | 'client' | 'detective' | 'admin'): boolean => {
      if (!role) return false;

      switch (portal) {
        case 'admin':
          return isAdmin;
        case 'lawyer':
          return isAdmin || isLawyer || isStaff;
        case 'client':
          return isAdmin || isClient;
        case 'detective':
          return isAdmin || isDetective;
        default:
          return false;
      }
    },
    [role, isAdmin, isLawyer, isStaff, isClient, isDetective]
  );

  return {
    user,
    role,
    isAuthenticated,
    isAdmin,
    isLawyer,
    isStaff,
    isClient,
    isDetective,
    isInternal,
    isExternal,
    roleDisplayName,
    dashboardPath,
    portalPath,
    hasAccess,
    canAccessPortal,
  };
}

export default useRole;
