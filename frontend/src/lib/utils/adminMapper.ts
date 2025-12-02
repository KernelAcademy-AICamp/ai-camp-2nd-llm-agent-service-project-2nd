/**
 * Admin Mapper
 * Converts API Admin types to UI types
 */

import { ApiAdminUser, ApiUserRole, ApiUserStatus } from '@/lib/api/admin';

// UI types for display
export type AdminRole = 'Admin' | 'Attorney' | 'Staff';
export type AdminUserStatus = 'active' | 'invited' | 'inactive';

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: AdminRole;
  status: AdminUserStatus;
  createdAt?: string;
  lastActive?: string;
}

/**
 * Map API role to display role
 */
export function mapApiRoleToRole(apiRole: ApiUserRole): AdminRole {
  const roleMap: Record<ApiUserRole, AdminRole> = {
    admin: 'Admin',
    lawyer: 'Attorney',
    staff: 'Staff',
  };
  return roleMap[apiRole] || 'Staff';
}

/**
 * Map display role to API role
 */
export function mapRoleToApiRole(role: AdminRole): ApiUserRole {
  const roleMap: Record<AdminRole, ApiUserRole> = {
    Admin: 'admin',
    Attorney: 'lawyer',
    Staff: 'staff',
  };
  return roleMap[role] || 'staff';
}

/**
 * Map API status to UI status
 */
export function mapApiStatusToStatus(apiStatus: ApiUserStatus): AdminUserStatus {
  // API and UI use the same values for status
  return apiStatus;
}

/**
 * Convert API Admin User to UI Admin User
 */
export function mapApiAdminUserToAdminUser(apiUser: ApiAdminUser): AdminUser {
  return {
    id: apiUser.id,
    name: apiUser.name,
    email: apiUser.email,
    role: mapApiRoleToRole(apiUser.role),
    status: mapApiStatusToStatus(apiUser.status),
    createdAt: apiUser.created_at,
    lastActive: apiUser.last_active,
  };
}

/**
 * Convert array of API Admin Users to UI Admin Users
 */
export function mapApiAdminUsersToAdminUsers(apiUsers: ApiAdminUser[]): AdminUser[] {
  return apiUsers.map(mapApiAdminUserToAdminUser);
}

// Role Permission types
export type PermissionKey = 'viewCases' | 'editCases' | 'accessAdmin' | 'manageBilling';

export interface RolePermission {
  id: string;
  role: AdminRole;
  label: string;
  permissions: Record<PermissionKey, boolean>;
}

export const PERMISSION_LABELS: Record<PermissionKey, string> = {
  viewCases: '사건 보기',
  editCases: '사건 편집',
  accessAdmin: 'Admin 메뉴 접근',
  manageBilling: 'Billing 관리',
};

/**
 * Map API RolePermissions to UI RolePermission
 * Backend uses: cases ('full'|'own'|'none'), evidence, admin (boolean), billing (boolean)
 * Frontend uses: viewCases, editCases, accessAdmin, manageBilling (all booleans)
 */
export function mapApiRolePermissionToRolePermission(
  apiRole: { role: string; cases: string; evidence: string; admin: boolean; billing: boolean }
): RolePermission {
  const roleMap: Record<string, AdminRole> = {
    admin: 'Admin',
    lawyer: 'Attorney',
    staff: 'Staff',
  };

  return {
    id: `role-${apiRole.role}`,
    role: roleMap[apiRole.role] || 'Staff',
    label: roleMap[apiRole.role] || 'Staff',
    permissions: {
      viewCases: apiRole.cases !== 'none',
      editCases: apiRole.cases === 'full',
      accessAdmin: apiRole.admin,
      manageBilling: apiRole.billing,
    },
  };
}

/**
 * Map UI permissions back to API format
 */
export function mapPermissionsToApiFormat(
  permissions: Record<PermissionKey, boolean>
): { cases: 'full' | 'own' | 'none'; evidence: 'full' | 'own' | 'none'; admin: boolean; billing: boolean } {
  let cases: 'full' | 'own' | 'none' = 'none';
  if (permissions.editCases) {
    cases = 'full';
  } else if (permissions.viewCases) {
    cases = 'own';
  }

  return {
    cases,
    evidence: cases, // Same as cases for simplicity
    admin: permissions.accessAdmin,
    billing: permissions.manageBilling,
  };
}
