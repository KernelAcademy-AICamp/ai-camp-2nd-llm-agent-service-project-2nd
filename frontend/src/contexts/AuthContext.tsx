/**
 * AuthContext
 * 003-role-based-ui Feature
 *
 * Global authentication context with role information.
 * Provides user state and auth methods to the entire app.
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
import { User, UserRole, getDashboardPath } from '@/types/user';
import { login as apiLogin, logout as apiLogout } from '@/lib/api/auth';

interface AuthContextType {
  // User state
  user: User | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Auth methods
  login: (email: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => Promise<void>;
  refreshUser: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = () => {
      try {
        const userStr = localStorage.getItem('user');
        const token = localStorage.getItem('authToken');

        if (userStr && token) {
          setUser(JSON.parse(userStr) as User);
        }
      } catch {
        // Invalid data, clear storage
        localStorage.removeItem('user');
        localStorage.removeItem('authToken');
      } finally {
        setIsLoading(false);
      }
    };

    loadUser();
  }, []);

  const refreshUser = useCallback(() => {
    try {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        setUser(JSON.parse(userStr) as User);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    }
  }, []);

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

        // Store auth token
        localStorage.setItem('authToken', response.data.access_token);

        // Store and set user
        if (response.data.user) {
          localStorage.setItem('user', JSON.stringify(response.data.user));
          setUser(response.data.user as User);

          // Set user_data cookie for middleware
          const userData = {
            name: response.data.user.name,
            email: response.data.user.email,
            role: response.data.user.role,
          };
          document.cookie = `user_data=${encodeURIComponent(JSON.stringify(userData))}; path=/; max-age=${7 * 24 * 60 * 60}`;

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
      await apiLogout();
    } finally {
      // Clear all auth data
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
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
