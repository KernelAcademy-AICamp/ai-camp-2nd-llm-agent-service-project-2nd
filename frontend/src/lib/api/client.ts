/**
 * API Client Configuration
 * Base API client for making HTTP requests to the backend
 *
 * Security: Uses HTTP-only cookies for authentication (XSS protection)
 * - Token is never stored in localStorage
 * - Cookies are automatically included via credentials: 'include'
 *
 * Error Handling (FR-008, FR-009):
 * - 401: Redirect to login with session expired message
 * - 403: Permission denied toast notification
 * - 500: Server error toast notification
 * - Network error: Connection error toast notification
 */

import toast from 'react-hot-toast';

// Empty string = relative URL (CloudFront proxies /api/* to backend)
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

// API prefix for all endpoints (matches backend router prefix)
const API_PREFIX = '/api';

// #311: Token refresh state management
// Prevents multiple simultaneous refresh attempts
let isRefreshing = false;
let refreshSubscribers: ((success: boolean) => void)[] = [];

function subscribeTokenRefresh(cb: (success: boolean) => void) {
  refreshSubscribers.push(cb);
}

function onRefreshComplete(success: boolean) {
  refreshSubscribers.forEach(cb => cb(success));
  refreshSubscribers = [];
}

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
    // Add /api prefix to all endpoints (backend routes are prefixed with /api)
    const url = `${API_BASE_URL}${API_PREFIX}${endpoint}`;

    // Authentication is handled via HTTP-only cookies only
    // No localStorage token - credentials: 'include' sends cookies automatically
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      credentials: 'include', // Include HTTP-only cookies
      headers,
    });

    // Handle empty responses (e.g., 204 No Content)
    let data: T | undefined = undefined;
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const text = await response.text();
      if (text) {
        data = JSON.parse(text) as T;
      }
    }

    if (!response.ok) {
      // Handle both error formats: { error: { message: "..." } } and { detail: "..." }
      const errorData = data as { error?: { message?: string }; detail?: string } | undefined;
      const errorMessage = errorData?.error?.message || errorData?.detail || 'An error occurred';

      // Handle 401 Unauthorized - attempt token refresh first (#311)
      if (response.status === 401 && typeof window !== 'undefined') {
        const isAuthCheck = endpoint.includes('/auth/me');
        const isAuthPage = window.location.pathname.startsWith('/login') ||
                           window.location.pathname.startsWith('/signup');
        const isLandingPage = window.location.pathname === '/';
        const isRefreshEndpoint = endpoint.includes('/auth/refresh');

        // Attempt token refresh for protected endpoints (not auth check, auth pages, landing, or refresh itself)
        if (!isAuthCheck && !isAuthPage && !isLandingPage && !isRefreshEndpoint) {
          // If already refreshing, wait for the result
          if (isRefreshing) {
            return new Promise<ApiResponse<T>>((resolve) => {
              subscribeTokenRefresh(async (success) => {
                if (success) {
                  // Retry original request after successful refresh
                  resolve(apiRequest<T>(endpoint, options));
                } else {
                  resolve({ error: errorMessage, status: 401 });
                }
              });
            });
          }

          // Start refresh process
          isRefreshing = true;

          try {
            // Call /auth/refresh directly to avoid circular import
            const refreshUrl = `${API_BASE_URL}${API_PREFIX}/auth/refresh`;
            const refreshResponse = await fetch(refreshUrl, {
              method: 'POST',
              credentials: 'include',
              headers: { 'Content-Type': 'application/json' },
            });

            if (refreshResponse.ok) {
              isRefreshing = false;
              onRefreshComplete(true);
              // Retry original request with new token
              return apiRequest<T>(endpoint, options);
            }
          } catch {
            // Refresh failed, fall through to logout
          }

          isRefreshing = false;
          onRefreshComplete(false);
        }

        // Redirect to login if not on excluded pages
        if (!isAuthCheck && !isAuthPage && !isLandingPage) {
          window.location.href = '/login?expired=true';
        }
      }
      // Handle 403 Forbidden - Permission denied (FR-009)
      if (response.status === 403 && typeof window !== 'undefined') {
        toast.error('접근 권한이 없습니다. 담당자에게 문의해 주세요.');
      }

      // Handle 500+ Server errors (FR-009)
      if (response.status >= 500 && typeof window !== 'undefined') {
        toast.error('서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.');
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
    // Network error - show toast notification (FR-009)
    if (typeof window !== 'undefined') {
      toast.error('네트워크 연결에 실패했습니다. 인터넷 연결을 확인해 주세요.');
    }
    return {
      error: error instanceof Error ? error.message : 'Network error',
      status: 0,
    };
  }
}

/**
 * Helper fetcher that throws when the API responds with an error.
 * Useful for libraries like SWR that expect a resolved payload or thrown error.
 */
export async function apiFetcher<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await apiRequest<T>(endpoint, options);

  if (response.error) {
    throw new Error(response.error);
  }

  if (typeof response.data === 'undefined') {
    throw new Error('No data returned from API');
  }

  return response.data;
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

  patch: <T>(endpoint: string, body?: unknown, options?: RequestInit) =>
    apiRequest<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(endpoint: string, options?: RequestInit) =>
    apiRequest<T>(endpoint, { ...options, method: 'DELETE' }),
};
