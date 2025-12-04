/**
 * Integration tests for useRole Hook
 * Task T015 - TDD RED Phase
 *
 * Tests for frontend/src/hooks/useRole.ts:
 * - Role detection from localStorage
 * - Role-based boolean flags
 * - Feature access checking
 * - Portal access checking
 * - Navigation path helpers
 */

import { renderHook } from '@testing-library/react';
import { useRole } from '@/hooks/useRole';
import { UserRole } from '@/types/user';

// Mock localStorage
const mockLocalStorage = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
    get store() {
      return store;
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

describe('useRole Hook', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
    jest.clearAllMocks();
  });

  describe('User Data from Storage', () => {
    test('should return null user when not authenticated', () => {
      const { result } = renderHook(() => useRole());

      expect(result.current.user).toBeNull();
      expect(result.current.role).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });

    test('should return user data when authenticated', () => {
      const mockUser = {
        id: 'user-123',
        email: 'lawyer@example.com',
        name: 'Test Lawyer',
        role: 'lawyer' as UserRole,
        status: 'active' as const,
        created_at: '2024-01-01T00:00:00Z',
      };
      mockLocalStorage.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useRole());

      expect(result.current.user).toEqual(mockUser);
      expect(result.current.role).toBe('lawyer');
      expect(result.current.isAuthenticated).toBe(true);
    });

    test('should handle invalid JSON in localStorage gracefully', () => {
      mockLocalStorage.setItem('user', 'invalid-json');

      const { result } = renderHook(() => useRole());

      expect(result.current.user).toBeNull();
      expect(result.current.isAuthenticated).toBe(false);
    });
  });

  describe('Role Boolean Flags', () => {
    const roleTestCases: Array<{
      role: UserRole;
      expectedFlags: Record<string, boolean>;
    }> = [
      {
        role: 'admin',
        expectedFlags: {
          isAdmin: true,
          isLawyer: false,
          isStaff: false,
          isClient: false,
          isDetective: false,
          isInternal: true,
          isExternal: false,
        },
      },
      {
        role: 'lawyer',
        expectedFlags: {
          isAdmin: false,
          isLawyer: true,
          isStaff: false,
          isClient: false,
          isDetective: false,
          isInternal: true,
          isExternal: false,
        },
      },
      {
        role: 'staff',
        expectedFlags: {
          isAdmin: false,
          isLawyer: false,
          isStaff: true,
          isClient: false,
          isDetective: false,
          isInternal: true,
          isExternal: false,
        },
      },
      {
        role: 'client',
        expectedFlags: {
          isAdmin: false,
          isLawyer: false,
          isStaff: false,
          isClient: true,
          isDetective: false,
          isInternal: false,
          isExternal: true,
        },
      },
      {
        role: 'detective',
        expectedFlags: {
          isAdmin: false,
          isLawyer: false,
          isStaff: false,
          isClient: false,
          isDetective: true,
          isInternal: false,
          isExternal: true,
        },
      },
    ];

    test.each(roleTestCases)(
      'should set correct boolean flags for $role role',
      ({ role, expectedFlags }) => {
        const mockUser = {
          id: 'user-123',
          email: `${role}@example.com`,
          name: `Test ${role}`,
          role,
          status: 'active' as const,
          created_at: '2024-01-01T00:00:00Z',
        };
        mockLocalStorage.setItem('user', JSON.stringify(mockUser));

        const { result } = renderHook(() => useRole());

        expect(result.current.isAdmin).toBe(expectedFlags.isAdmin);
        expect(result.current.isLawyer).toBe(expectedFlags.isLawyer);
        expect(result.current.isStaff).toBe(expectedFlags.isStaff);
        expect(result.current.isClient).toBe(expectedFlags.isClient);
        expect(result.current.isDetective).toBe(expectedFlags.isDetective);
        expect(result.current.isInternal).toBe(expectedFlags.isInternal);
        expect(result.current.isExternal).toBe(expectedFlags.isExternal);
      }
    );
  });

  describe('Role Display Names', () => {
    const displayNameCases: Array<{ role: UserRole; expectedName: string }> = [
      { role: 'admin', expectedName: '관리자' },
      { role: 'lawyer', expectedName: '변호사' },
      { role: 'staff', expectedName: '직원' },
      { role: 'client', expectedName: '의뢰인' },
      { role: 'detective', expectedName: '탐정' },
    ];

    test.each(displayNameCases)(
      'should return correct display name for $role: $expectedName',
      ({ role, expectedName }) => {
        const mockUser = {
          id: 'user-123',
          email: `${role}@example.com`,
          name: `Test ${role}`,
          role,
          status: 'active' as const,
          created_at: '2024-01-01T00:00:00Z',
        };
        mockLocalStorage.setItem('user', JSON.stringify(mockUser));

        const { result } = renderHook(() => useRole());

        expect(result.current.roleDisplayName).toBe(expectedName);
      }
    );

    test('should return empty string for unauthenticated user', () => {
      const { result } = renderHook(() => useRole());

      expect(result.current.roleDisplayName).toBe('');
    });
  });

  describe('Navigation Paths', () => {
    const pathTestCases: Array<{
      role: UserRole;
      expectedDashboard: string;
      expectedPortal: string;
    }> = [
      {
        role: 'admin',
        expectedDashboard: '/admin/dashboard',
        expectedPortal: '/admin',
      },
      {
        role: 'lawyer',
        expectedDashboard: '/lawyer/dashboard',
        expectedPortal: '/lawyer',
      },
      {
        role: 'staff',
        expectedDashboard: '/lawyer/dashboard',
        expectedPortal: '/lawyer',
      },
      {
        role: 'client',
        expectedDashboard: '/client/dashboard',
        expectedPortal: '/client',
      },
      {
        role: 'detective',
        expectedDashboard: '/detective/dashboard',
        expectedPortal: '/detective',
      },
    ];

    test.each(pathTestCases)(
      'should return correct paths for $role',
      ({ role, expectedDashboard, expectedPortal }) => {
        const mockUser = {
          id: 'user-123',
          email: `${role}@example.com`,
          name: `Test ${role}`,
          role,
          status: 'active' as const,
          created_at: '2024-01-01T00:00:00Z',
        };
        mockLocalStorage.setItem('user', JSON.stringify(mockUser));

        const { result } = renderHook(() => useRole());

        expect(result.current.dashboardPath).toBe(expectedDashboard);
        expect(result.current.portalPath).toBe(expectedPortal);
      }
    );

    test('should return /login for dashboard when not authenticated', () => {
      const { result } = renderHook(() => useRole());

      expect(result.current.dashboardPath).toBe('/login');
    });
  });

  describe('Feature Access (hasAccess)', () => {
    test('should allow admin access to all features', () => {
      const mockUser = {
        id: 'user-123',
        email: 'admin@example.com',
        name: 'Admin',
        role: 'admin' as UserRole,
        status: 'active' as const,
        created_at: '2024-01-01T00:00:00Z',
      };
      mockLocalStorage.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useRole());

      expect(result.current.hasAccess('any-feature')).toBe(true);
      expect(result.current.hasAccess('billing')).toBe(true);
      expect(result.current.hasAccess('cases')).toBe(true);
    });

    test('should allow lawyer access to lawyer features', () => {
      const mockUser = {
        id: 'user-123',
        email: 'lawyer@example.com',
        name: 'Lawyer',
        role: 'lawyer' as UserRole,
        status: 'active' as const,
        created_at: '2024-01-01T00:00:00Z',
      };
      mockLocalStorage.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useRole());

      expect(result.current.hasAccess('dashboard')).toBe(true);
      expect(result.current.hasAccess('cases')).toBe(true);
      expect(result.current.hasAccess('billing')).toBe(true);
      expect(result.current.hasAccess('field')).toBe(false); // Detective-only
    });

    test('should allow client access to client features', () => {
      const mockUser = {
        id: 'user-123',
        email: 'client@example.com',
        name: 'Client',
        role: 'client' as UserRole,
        status: 'active' as const,
        created_at: '2024-01-01T00:00:00Z',
      };
      mockLocalStorage.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useRole());

      expect(result.current.hasAccess('dashboard')).toBe(true);
      expect(result.current.hasAccess('cases')).toBe(true);
      expect(result.current.hasAccess('messages')).toBe(true);
      expect(result.current.hasAccess('field')).toBe(false); // Detective-only
      expect(result.current.hasAccess('clients')).toBe(false); // Lawyer-only
    });

    test('should allow detective access to detective features', () => {
      const mockUser = {
        id: 'user-123',
        email: 'detective@example.com',
        name: 'Detective',
        role: 'detective' as UserRole,
        status: 'active' as const,
        created_at: '2024-01-01T00:00:00Z',
      };
      mockLocalStorage.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useRole());

      expect(result.current.hasAccess('dashboard')).toBe(true);
      expect(result.current.hasAccess('field')).toBe(true);
      expect(result.current.hasAccess('report')).toBe(true);
      expect(result.current.hasAccess('earnings')).toBe(true);
      expect(result.current.hasAccess('billing')).toBe(false); // Client/Lawyer only
      expect(result.current.hasAccess('clients')).toBe(false); // Lawyer-only
    });

    test('should deny access when not authenticated', () => {
      const { result } = renderHook(() => useRole());

      expect(result.current.hasAccess('dashboard')).toBe(false);
      expect(result.current.hasAccess('cases')).toBe(false);
    });
  });

  describe('Portal Access (canAccessPortal)', () => {
    test('should allow admin to access all portals', () => {
      const mockUser = {
        id: 'user-123',
        email: 'admin@example.com',
        name: 'Admin',
        role: 'admin' as UserRole,
        status: 'active' as const,
        created_at: '2024-01-01T00:00:00Z',
      };
      mockLocalStorage.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useRole());

      expect(result.current.canAccessPortal('admin')).toBe(true);
      expect(result.current.canAccessPortal('lawyer')).toBe(true);
      expect(result.current.canAccessPortal('client')).toBe(true);
      expect(result.current.canAccessPortal('detective')).toBe(true);
    });

    test('should allow lawyer to access lawyer portal only', () => {
      const mockUser = {
        id: 'user-123',
        email: 'lawyer@example.com',
        name: 'Lawyer',
        role: 'lawyer' as UserRole,
        status: 'active' as const,
        created_at: '2024-01-01T00:00:00Z',
      };
      mockLocalStorage.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useRole());

      expect(result.current.canAccessPortal('lawyer')).toBe(true);
      expect(result.current.canAccessPortal('admin')).toBe(false);
      expect(result.current.canAccessPortal('client')).toBe(false);
      expect(result.current.canAccessPortal('detective')).toBe(false);
    });

    test('should allow client to access client portal only', () => {
      const mockUser = {
        id: 'user-123',
        email: 'client@example.com',
        name: 'Client',
        role: 'client' as UserRole,
        status: 'active' as const,
        created_at: '2024-01-01T00:00:00Z',
      };
      mockLocalStorage.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useRole());

      expect(result.current.canAccessPortal('client')).toBe(true);
      expect(result.current.canAccessPortal('lawyer')).toBe(false);
      expect(result.current.canAccessPortal('detective')).toBe(false);
      expect(result.current.canAccessPortal('admin')).toBe(false);
    });

    test('should allow detective to access detective portal only', () => {
      const mockUser = {
        id: 'user-123',
        email: 'detective@example.com',
        name: 'Detective',
        role: 'detective' as UserRole,
        status: 'active' as const,
        created_at: '2024-01-01T00:00:00Z',
      };
      mockLocalStorage.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useRole());

      expect(result.current.canAccessPortal('detective')).toBe(true);
      expect(result.current.canAccessPortal('lawyer')).toBe(false);
      expect(result.current.canAccessPortal('client')).toBe(false);
      expect(result.current.canAccessPortal('admin')).toBe(false);
    });

    test('should allow staff to access lawyer portal', () => {
      const mockUser = {
        id: 'user-123',
        email: 'staff@example.com',
        name: 'Staff',
        role: 'staff' as UserRole,
        status: 'active' as const,
        created_at: '2024-01-01T00:00:00Z',
      };
      mockLocalStorage.setItem('user', JSON.stringify(mockUser));

      const { result } = renderHook(() => useRole());

      expect(result.current.canAccessPortal('lawyer')).toBe(true);
      expect(result.current.canAccessPortal('client')).toBe(false);
      expect(result.current.canAccessPortal('detective')).toBe(false);
    });

    test('should deny all portal access when not authenticated', () => {
      const { result } = renderHook(() => useRole());

      expect(result.current.canAccessPortal('admin')).toBe(false);
      expect(result.current.canAccessPortal('lawyer')).toBe(false);
      expect(result.current.canAccessPortal('client')).toBe(false);
      expect(result.current.canAccessPortal('detective')).toBe(false);
    });
  });
});
