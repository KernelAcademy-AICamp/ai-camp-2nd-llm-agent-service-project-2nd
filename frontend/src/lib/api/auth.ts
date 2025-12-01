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
  // Create form data for OAuth2 password flow
  const formData = new URLSearchParams();
  formData.append('username', email); // OAuth2 uses 'username' field
  formData.append('password', password);

  return apiRequest<LoginResponse>('/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
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
