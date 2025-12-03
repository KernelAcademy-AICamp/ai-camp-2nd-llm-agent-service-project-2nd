/**
 * Authentication API Client
 * Handles login, logout, and authentication-related API calls
 */

import { apiRequest, ApiResponse } from './client';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
}

/**
 * Login user with email and password
 */
export async function login(
  email: string,
  password: string
): Promise<ApiResponse<LoginResponse>> {
  return apiRequest<LoginResponse>('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
}

/**
 * Logout current user
 */
export async function logout(): Promise<ApiResponse<void>> {
  return apiRequest<void>('/auth/logout', {
    method: 'POST',
  });
}

export interface SignupRequest {
  name: string;
  email: string;
  password: string;
  law_firm?: string;
  accept_terms: boolean;
}

export interface SignupResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
  };
}

/**
 * Register a new user
 */
export async function signup(
  data: SignupRequest
): Promise<ApiResponse<SignupResponse>> {
  return apiRequest<SignupResponse>('/auth/signup', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
}

/**
 * Request password reset email
 */
export async function forgotPassword(
  email: string
): Promise<ApiResponse<{ message: string }>> {
  return apiRequest<{ message: string }>('/auth/forgot-password', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });
}

/**
 * Reset password with token
 */
export async function resetPassword(
  token: string,
  newPassword: string
): Promise<ApiResponse<{ message: string }>> {
  return apiRequest<{ message: string }>('/auth/reset-password', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export interface UserInfo {
  id: string;
  email: string;
  name: string;
  role: string;
  status: string;
  created_at: string;
}

/**
 * Get current authenticated user info
 * Uses HTTP-only cookie for authentication
 */
export async function getCurrentUser(): Promise<ApiResponse<UserInfo>> {
  return apiRequest<UserInfo>('/auth/me', {
    method: 'GET',
  });
}
