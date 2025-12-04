/**
 * Authentication Hook
 * Handles login state, logout, and user info
 *
 * Security: Uses HTTP-only cookie for authentication (XSS protection)
 * - Token is NEVER stored in localStorage
 * - Auth status is verified by calling /auth/me endpoint
 * - Only user display info is cached in localStorage (not sensitive)
 */

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { getCurrentUser, logout as apiLogout } from '@/lib/api/auth';

// App version - update this when deploying new versions
const APP_VERSION = '0.2.0';
const APP_VERSION_KEY = 'appVersion';
const USER_CACHE_KEY = 'userCache'; // Only for display, not auth

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export function useAuth() {
  const router = useRouter();
  // Initialize with null to distinguish "not checked yet" from "checked and false"
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);

  // Check authentication by calling /auth/me
  const checkAuth = useCallback(async () => {
    setIsLoading(true);

    // Check app version and clear cache if changed
    const storedVersion = localStorage.getItem(APP_VERSION_KEY);
    if (storedVersion && storedVersion !== APP_VERSION) {
      console.log(`App version changed: ${storedVersion} -> ${APP_VERSION}. Clearing cache.`);
      localStorage.removeItem(USER_CACHE_KEY);
      // Clear legacy tokens if any (migration)
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
    }
    localStorage.setItem(APP_VERSION_KEY, APP_VERSION);

    try {
      // Call /auth/me to verify authentication via HTTP-only cookie
      const response = await getCurrentUser();

      if (response.data) {
        const userData: User = {
          id: response.data.id,
          email: response.data.email,
          name: response.data.name,
          role: response.data.role,
        };
        setUser(userData);
        setIsAuthenticated(true);
        // Cache user info for display purposes only
        localStorage.setItem(USER_CACHE_KEY, JSON.stringify(userData));
      } else {
        // Not authenticated
        setUser(null);
        setIsAuthenticated(false);
        localStorage.removeItem(USER_CACHE_KEY);
      }
    } catch {
      // Error checking auth - treat as not authenticated
      setUser(null);
      setIsAuthenticated(false);
      localStorage.removeItem(USER_CACHE_KEY);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initialize auth state
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Logout handler
  const logout = useCallback(async () => {
    try {
      // Call logout API to clear HTTP-only cookies
      await apiLogout();
    } catch {
      // Continue even if API call fails
    }

    // Clear local state and cache
    localStorage.removeItem(USER_CACHE_KEY);
    // Clear legacy tokens if any (migration)
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');

    setIsAuthenticated(false);
    setUser(null);
    router.push('/login');
  }, [router]);

  // Get cached user info (for display only, not for auth decisions)
  const getUser = useCallback((): User | null => {
    // Return state user first, fallback to cache
    if (user) return user;

    const cachedUser = localStorage.getItem(USER_CACHE_KEY);
    if (cachedUser) {
      try {
        return JSON.parse(cachedUser);
      } catch {
        return null;
      }
    }
    return null;
  }, [user]);

  // Refresh auth state
  const refreshAuth = useCallback(async () => {
    await checkAuth();
  }, [checkAuth]);

  return {
    isAuthenticated,
    isLoading,
    user,
    logout,
    getUser,
    refreshAuth,
  };
}

export default useAuth;
