/**
 * Integration tests for Role-Based Routing Middleware
 * Task T014 - TDD RED Phase
 *
 * Tests for frontend/src/middleware.ts:
 * - Public routes access
 * - Authentication check
 * - Role-based portal redirection
 * - Legacy route handling
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Store original NextResponse methods
const originalNext = NextResponse.next;
const originalRedirect = NextResponse.redirect;

// Create mock functions
const mockNext = jest.fn(() => ({ type: 'next' }));
const mockRedirect = jest.fn((url: URL) => ({
  type: 'redirect',
  url: url.toString(),
}));

// Import middleware
import { middleware, config } from '@/middleware';

describe('Middleware - Role-Based Routing', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Replace NextResponse methods with mocks
    (NextResponse as any).next = mockNext;
    (NextResponse as any).redirect = mockRedirect;
  });

  afterAll(() => {
    // Restore original methods
    (NextResponse as any).next = originalNext;
    (NextResponse as any).redirect = originalRedirect;
  });

  /**
   * Helper to create a mock NextRequest
   */
  function createMockRequest(
    pathname: string,
    cookies: Record<string, string> = {}
  ): NextRequest {
    const url = new URL(`http://localhost:3000${pathname}`);
    return {
      nextUrl: url,
      url: url.toString(),
      cookies: {
        get: (name: string) => {
          const value = cookies[name];
          return value ? { name, value } : undefined;
        },
        getAll: () =>
          Object.entries(cookies).map(([name, value]) => ({ name, value })),
        has: (name: string) => name in cookies,
      },
    } as unknown as NextRequest;
  }

  describe('Public Routes', () => {
    const publicRoutes = ['/', '/login', '/signup', '/about', '/pricing'];

    test.each(publicRoutes)(
      'should allow access to public route: %s',
      (route) => {
        const request = createMockRequest(route);
        middleware(request);

        expect(mockNext).toHaveBeenCalled();
      }
    );

    test('should redirect logged-in user from /login to their portal', () => {
      const request = createMockRequest('/login', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'lawyer' })),
      });

      const result = middleware(request);

      expect(mockRedirect).toHaveBeenCalled();
      expect(result).toMatchObject({
        type: 'redirect',
      });
    });

    test('should redirect logged-in client from /login to client portal', () => {
      const request = createMockRequest('/login', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'client' })),
      });

      const result = middleware(request);

      expect(mockRedirect).toHaveBeenCalled();
    });

    test('should redirect logged-in detective from /login to detective portal', () => {
      const request = createMockRequest('/login', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'detective' })),
      });

      const result = middleware(request);

      expect(mockRedirect).toHaveBeenCalled();
    });
  });

  describe('Protected Routes - Authentication', () => {
    test('should redirect unauthenticated user to login', () => {
      const request = createMockRequest('/lawyer/dashboard');

      const result = middleware(request);

      expect(mockRedirect).toHaveBeenCalled();
      expect(result).toMatchObject({
        type: 'redirect',
      });
    });

    test('should redirect to login with returnUrl when accessing protected route', () => {
      const request = createMockRequest('/lawyer/cases/123');

      middleware(request);

      expect(mockRedirect).toHaveBeenCalled();
    });
  });

  describe('Role-Based Portal Access', () => {
    test('should allow lawyer to access /lawyer portal', () => {
      const request = createMockRequest('/lawyer/dashboard', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'lawyer' })),
      });

      middleware(request);

      expect(mockNext).toHaveBeenCalled();
    });

    test('should redirect client trying to access /lawyer portal', () => {
      const request = createMockRequest('/lawyer/dashboard', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'client' })),
      });

      const result = middleware(request);

      expect(mockRedirect).toHaveBeenCalled();
    });

    test('should allow client to access /client portal', () => {
      const request = createMockRequest('/client/dashboard', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'client' })),
      });

      middleware(request);

      expect(mockNext).toHaveBeenCalled();
    });

    test('should redirect lawyer trying to access /client portal', () => {
      const request = createMockRequest('/client/dashboard', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'lawyer' })),
      });

      const result = middleware(request);

      expect(mockRedirect).toHaveBeenCalled();
    });

    test('should allow detective to access /detective portal', () => {
      const request = createMockRequest('/detective/dashboard', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'detective' })),
      });

      middleware(request);

      expect(mockNext).toHaveBeenCalled();
    });

    test('should redirect client trying to access /detective portal', () => {
      const request = createMockRequest('/detective/dashboard', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'client' })),
      });

      const result = middleware(request);

      expect(mockRedirect).toHaveBeenCalled();
    });

    test('should allow admin to access any portal', () => {
      const portals = [
        '/lawyer/dashboard',
        '/client/dashboard',
        '/detective/dashboard',
      ];

      for (const portal of portals) {
        mockNext.mockClear();
        const request = createMockRequest(portal, {
          access_token: 'valid_token',
          user_data: encodeURIComponent(JSON.stringify({ role: 'admin' })),
        });

        middleware(request);

        // Admin should have access (next is called)
        expect(mockNext).toHaveBeenCalled();
      }
    });

    test('should allow staff to access /lawyer portal', () => {
      const request = createMockRequest('/lawyer/dashboard', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'staff' })),
      });

      middleware(request);

      expect(mockNext).toHaveBeenCalled();
    });
  });

  describe('Legacy Route Handling', () => {
    test('should redirect /dashboard to role-appropriate dashboard for lawyer', () => {
      const request = createMockRequest('/dashboard', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'lawyer' })),
      });

      const result = middleware(request);

      expect(mockRedirect).toHaveBeenCalled();
    });

    test('should redirect /dashboard to client dashboard for client', () => {
      const request = createMockRequest('/dashboard', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'client' })),
      });

      const result = middleware(request);

      expect(mockRedirect).toHaveBeenCalled();
    });

    test('should redirect /cases to role-appropriate portal for lawyer', () => {
      const request = createMockRequest('/cases', {
        access_token: 'valid_token',
        user_data: encodeURIComponent(JSON.stringify({ role: 'lawyer' })),
      });

      const result = middleware(request);

      expect(mockRedirect).toHaveBeenCalled();
    });
  });

  describe('Static and API Routes', () => {
    test('should skip middleware for API routes', () => {
      const request = createMockRequest('/api/auth/login');

      middleware(request);

      expect(mockNext).toHaveBeenCalled();
    });

    test('should skip middleware for static files', () => {
      const staticRoutes = [
        '/_next/static/chunk.js',
        '/favicon.ico',
        '/images/logo.png',
      ];

      for (const route of staticRoutes) {
        mockNext.mockClear();
        const request = createMockRequest(route);

        middleware(request);

        expect(mockNext).toHaveBeenCalled();
      }
    });
  });

  describe('Middleware Config', () => {
    test('should have correct matcher config', () => {
      expect(config.matcher).toBeDefined();
      expect(Array.isArray(config.matcher)).toBe(true);
    });
  });
});
