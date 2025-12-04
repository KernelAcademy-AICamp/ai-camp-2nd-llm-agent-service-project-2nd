/**
 * AuthContext
 * 003-role-based-ui Feature
 *
 * Global authentication context with role information.
 * Provides user state and auth methods to the entire app.
 *
 * Security: Uses HTTP-only cookie for authentication (XSS protection)
 * - Token is NEVER stored in localStorage
 * - Auth status is verified by calling /auth/me endpoint
 * - Only user display info is cached in localStorage (not sensitive)
 */

'use client';

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  ReactNode,
} from 'react';
import { useRouter } from 'next/navigation';
import { User, UserRole, UserStatus, getDashboardPath } from '@/types/user';
import { login as apiLogin, logout as apiLogout, getCurrentUser } from '@/lib/api/auth';

interface AuthContextType {
  // User state
  user: User | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Auth methods
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

const USER_CACHE_KEY = 'userCache';

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check authentication by calling /auth/me
  const checkAuth = useCallback(async () => {
    setIsLoading(true);

    // Clear legacy localStorage tokens (migration)
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');

    try {
      // Call /auth/me to verify authentication via HTTP-only cookie
      const response = await getCurrentUser();

      if (response.data) {
        const userData: User = {
          id: response.data.id,
          email: response.data.email,
          name: response.data.name,
          role: response.data.role as UserRole,
          status: (response.data.status as UserStatus) || 'active',
          created_at: response.data.created_at || new Date().toISOString(),
        };
        setUser(userData);
        // Cache user info for display purposes only
        localStorage.setItem(USER_CACHE_KEY, JSON.stringify(userData));
      } else {
        // Not authenticated
        setUser(null);
        localStorage.removeItem(USER_CACHE_KEY);
      }
    } catch {
      // Error checking auth - treat as not authenticated
      setUser(null);
      localStorage.removeItem(USER_CACHE_KEY);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Initialize auth state
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const refreshUser = useCallback(async () => {
    await checkAuth();
  }, [checkAuth]);

  const login = useCallback(
    async (email: string, password: string): Promise<{ success: boolean; error?: string }> => {
      try {
        const response = await apiLogin(email, password);

        if (response.error || !response.data) {
          return {
            success: false,
            error: response.error || '로그인에 실패했습니다.',
          };
        }

        // Authentication token is now handled via HTTP-only cookie (set by backend)
        // We only cache user display info locally, NOT the auth token

        // Store and set user (display info only)
        if (response.data.user) {
          const userData: User = {
            id: response.data.user.id,
            email: response.data.user.email,
            name: response.data.user.name,
            role: response.data.user.role as UserRole,
            status: 'active', // Default status for newly logged in users
            created_at: new Date().toISOString(), // Will be updated on refresh
          };

          setUser(userData);
          localStorage.setItem(USER_CACHE_KEY, JSON.stringify(userData));

          // Set user_data cookie for middleware
          const userDisplayData = {
            name: response.data.user.name,
            email: response.data.user.email,
            role: response.data.user.role,
          };
          document.cookie = `user_data=${encodeURIComponent(JSON.stringify(userDisplayData))}; path=/; max-age=${7 * 24 * 60 * 60}`;

          // Redirect based on role
          const dashboardPath = getDashboardPath(response.data.user.role as UserRole);
          router.push(dashboardPath);
        }

        return { success: true };
      } catch {
        return {
          success: false,
          error: '로그인 중 오류가 발생했습니다.',
        };
      }
    },
    [router]
  );

  const logout = useCallback(async () => {
    try {
      // Call logout API to clear HTTP-only cookies
      await apiLogout();
    } finally {
      // Clear all local auth data
      localStorage.removeItem(USER_CACHE_KEY);
      // Clear legacy tokens if any (migration)
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      // Clear display cookie
      document.cookie = 'user_data=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      setUser(null);
      router.push('/login');
    }
  }, [router]);

  const value: AuthContextType = {
    user,
    role: user?.role || null,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

/**
 * Hook to access auth context
 *
 * Usage:
 * ```tsx
 * const { user, role, isAuthenticated, login, logout } = useAuth();
 * ```
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}

export default AuthContext;
