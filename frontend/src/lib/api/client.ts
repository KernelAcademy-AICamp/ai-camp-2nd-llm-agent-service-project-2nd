/**
 * API Client Configuration
 * Base API client for making HTTP requests to the backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

/**
 * Generic API request function
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;

    // Get auth token from localStorage
    const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
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

      // Handle 401 Unauthorized - clear token and redirect to login
      if (response.status === 401 && typeof window !== 'undefined') {
        localStorage.removeItem('authToken');
        // Redirect to login page
        window.location.href = '/login';
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
