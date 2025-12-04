/**
 * User and Role Types
 * 003-role-based-ui Feature
 */

// User roles matching backend UserRole enum
export type UserRole = 'admin' | 'lawyer' | 'staff' | 'client' | 'detective';

export type UserStatus = 'active' | 'inactive';

export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
}

// Role-based portal paths
export const ROLE_PORTAL_PATHS: Record<UserRole, string> = {
  admin: '/admin',
  lawyer: '/lawyer',
  staff: '/lawyer', // Staff uses lawyer portal
  client: '/client',
  detective: '/detective',
};

// Role-based dashboard paths
export const ROLE_DASHBOARD_PATHS: Record<UserRole, string> = {
  admin: '/admin/dashboard',
  lawyer: '/lawyer/dashboard',
  staff: '/lawyer/dashboard',
  client: '/client/dashboard',
  detective: '/detective/dashboard',
};

// Features allowed per role
export const ROLE_FEATURES: Record<UserRole, string[]> = {
  admin: ['*'], // All access
  lawyer: [
    'dashboard',
    'cases',
    'evidence',
    'timeline',
    'draft',
    'clients',
    'investigators',
    'calendar',
    'billing',
    'messages',
  ],
  staff: ['dashboard', 'cases', 'evidence', 'timeline', 'calendar', 'messages'],
  client: ['dashboard', 'cases', 'evidence', 'timeline', 'messages', 'billing'],
  detective: [
    'dashboard',
    'cases',
    'field',
    'evidence',
    'report',
    'messages',
    'calendar',
    'earnings',
  ],
};

// Check if a role has access to a feature
export function hasFeatureAccess(role: UserRole, feature: string): boolean {
  const features = ROLE_FEATURES[role];
  if (features.includes('*')) return true;
  return features.includes(feature);
}

// Get the portal path for a role
export function getPortalPath(role: UserRole): string {
  return ROLE_PORTAL_PATHS[role] || '/';
}

// Get the dashboard path for a role
export function getDashboardPath(role: UserRole): string {
  return ROLE_DASHBOARD_PATHS[role] || '/dashboard';
}

// Role display names (Korean)
export const ROLE_DISPLAY_NAMES: Record<UserRole, string> = {
  admin: '관리자',
  lawyer: '변호사',
  staff: '직원',
  client: '의뢰인',
  detective: '탐정',
};

// Check if user is internal (not client/detective)
export function isInternalUser(role: UserRole): boolean {
  return ['admin', 'lawyer', 'staff'].includes(role);
}

// Check if user is external (client/detective)
export function isExternalUser(role: UserRole): boolean {
  return ['client', 'detective'].includes(role);
}
