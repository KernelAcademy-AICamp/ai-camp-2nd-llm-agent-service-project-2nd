/**
 * Admin API Client
 * Handles admin user and role management operations
 */

import { apiRequest, ApiResponse } from './client';

// Backend uses lowercase roles, frontend uses display names
export type ApiUserRole = 'admin' | 'lawyer' | 'staff';
export type ApiUserStatus = 'active' | 'inactive' | 'invited';

export interface ApiAdminUser {
  id: string;
  name: string;
  email: string;
  role: ApiUserRole;
  status: ApiUserStatus;
  created_at?: string;
  last_active?: string;
}

export interface UserListResponse {
  users: ApiAdminUser[];
  total: number;
}

export interface InviteUserRequest {
  email: string;
  role: ApiUserRole;
}

export interface InviteUserResponse {
  invite_token: string;
  invite_url: string;
  expires_at: string;
}

export interface RolePermissions {
  role: ApiUserRole;
  cases: 'full' | 'own' | 'none';
  evidence: 'full' | 'own' | 'none';
  admin: boolean;
  billing: boolean;
}

export interface RolePermissionsResponse {
  roles: RolePermissions[];
}

export interface UpdateRolePermissionsRequest {
  cases?: 'full' | 'own' | 'none';
  evidence?: 'full' | 'own' | 'none';
  admin?: boolean;
  billing?: boolean;
}

/**
 * Get list of admin users
 */
export async function getAdminUsers(params?: {
  email?: string;
  name?: string;
  role?: ApiUserRole;
  status?: ApiUserStatus;
}): Promise<ApiResponse<UserListResponse>> {
  const searchParams = new URLSearchParams();
  if (params?.email) searchParams.append('email', params.email);
  if (params?.name) searchParams.append('name', params.name);
  if (params?.role) searchParams.append('role', params.role);
  if (params?.status) searchParams.append('status', params.status);

  const queryString = searchParams.toString();
  const url = `/admin/users${queryString ? `?${queryString}` : ''}`;

  return apiRequest<UserListResponse>(url, {
    method: 'GET',
  });
}

/**
 * Invite a new user
 */
export async function inviteUser(
  request: InviteUserRequest
): Promise<ApiResponse<InviteUserResponse>> {
  return apiRequest<InviteUserResponse>('/admin/users/invite', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
}

/**
 * Delete (deactivate) a user
 */
export async function deleteUser(
  userId: string
): Promise<ApiResponse<{ message: string; user_id: string }>> {
  return apiRequest<{ message: string; user_id: string }>(`/admin/users/${userId}`, {
    method: 'DELETE',
  });
}

/**
 * Get role permissions matrix
 */
export async function getRoles(): Promise<ApiResponse<RolePermissionsResponse>> {
  return apiRequest<RolePermissionsResponse>('/admin/roles', {
    method: 'GET',
  });
}

/**
 * Update role permissions
 */
export async function updateRolePermissions(
  role: ApiUserRole,
  request: UpdateRolePermissionsRequest
): Promise<ApiResponse<RolePermissions>> {
  return apiRequest<RolePermissions>(`/admin/roles/${role}/permissions`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
}
