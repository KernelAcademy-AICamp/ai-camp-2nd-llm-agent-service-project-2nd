/**
 * Authentication Hook
 * Handles login state, logout, user info, and version-based session invalidation
 */

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/router';

// App version - update this when deploying new versions
// This will force logout on version mismatch
const APP_VERSION = '0.2.0';
const AUTH_TOKEN_KEY = 'authToken';
const APP_VERSION_KEY = 'appVersion';
const USER_KEY = 'user';

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export function useAuth() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState<User | null>(null);

  // Check version and invalidate session if version changed
  const checkVersionAndAuth = useCallback(() => {
    const storedVersion = localStorage.getItem(APP_VERSION_KEY);
    const token = localStorage.getItem(AUTH_TOKEN_KEY);

    // If version changed, clear auth and force re-login
    if (storedVersion && storedVersion !== APP_VERSION) {
      console.log(`App version changed: ${storedVersion} -> ${APP_VERSION}. Logging out.`);
      localStorage.removeItem(AUTH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      localStorage.setItem(APP_VERSION_KEY, APP_VERSION);
      setIsAuthenticated(false);
      setUser(null);
      return false;
    }

    // Store current version
    localStorage.setItem(APP_VERSION_KEY, APP_VERSION);

    if (token) {
      setIsAuthenticated(true);
      // Load user from localStorage
      const storedUser = localStorage.getItem(USER_KEY);
      if (storedUser) {
        try {
          setUser(JSON.parse(storedUser));
        } catch {
          setUser(null);
        }
      }
      return true;
    }

    setIsAuthenticated(false);
    setUser(null);
    return false;
  }, []);

  // Initialize auth state
  useEffect(() => {
    checkVersionAndAuth();
    setIsLoading(false);
  }, [checkVersionAndAuth]);

  // Logout handler
  const logout = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setIsAuthenticated(false);
    setUser(null);
    router.push('/login');
  }, [router]);

  // Get auth token
  const getToken = useCallback(() => {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  }, []);

  // Get user info
  const getUser = useCallback((): User | null => {
    const storedUser = localStorage.getItem(USER_KEY);
    if (storedUser) {
      try {
        return JSON.parse(storedUser);
      } catch {
        return null;
      }
    }
    return null;
  }, []);

  return {
    isAuthenticated,
    isLoading,
    user,
    logout,
    getToken,
    getUser,
    checkVersionAndAuth,
  };
}

export default useAuth;
