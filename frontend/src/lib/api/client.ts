/**
 * API Client Configuration
 * Base API client for making HTTP requests to the backend
 *
 * Security: Uses HTTP-only cookies for authentication (XSS protection)
 * - Token is never stored in localStorage
 * - Cookies are automatically included via credentials: 'include'
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

/**
 * Generic API request function
 *
 * Authentication is handled via HTTP-only cookies:
 * - credentials: 'include' ensures cookies are sent with requests
 * - No token is stored in localStorage (XSS protection)
 * - Backend sets/clears cookies on login/logout
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      credentials: 'include', // Include HTTP-only cookies
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    // Handle empty responses (e.g., 204 No Content)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let data: any = null;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const text = await response.text();
      if (text) {
        data = JSON.parse(text);
      }
    }

    if (!response.ok) {
      // Handle both error formats: { error: { message: "..." } } and { detail: "..." }
      const errorMessage = data?.error?.message || data?.detail || 'An error occurred';

      // Handle 401 Unauthorized - redirect to login (but not from /auth/me or if already on login)
      // Note: Cookie cleanup is handled by the logout endpoint
      if (response.status === 401 && typeof window !== 'undefined') {
        // Clear any legacy localStorage tokens (migration)
        localStorage.removeItem('authToken');
        localStorage.removeItem('user');
        // Don't redirect if:
        // 1. We're checking auth status (/auth/me) - 401 is expected for unauthenticated users
        // 2. We're already on the login/signup page
        const isAuthCheck = endpoint === '/auth/me';
        const isAuthPage = window.location.pathname.startsWith('/login') ||
                           window.location.pathname.startsWith('/signup');
        if (!isAuthCheck && !isAuthPage) {
          window.location.href = '/login';
        }
      }

      return {
        error: errorMessage,
        status: response.status,
      };
    }

    return {
      data,
      status: response.status,
    };
  } catch (error) {
    return {
      error: error instanceof Error ? error.message : 'Network error',
      status: 0,
    };
  }
}

/**
 * API Client object with HTTP methods
 */
export const apiClient = {
  get: <T>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
};
