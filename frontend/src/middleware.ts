/**
 * Next.js Middleware for Role-Based Routing
 * 003-role-based-ui Feature
 *
 * Handles:
 * - Authentication check
 * - Role-based portal access
 * - Automatic redirection to appropriate portal
 */

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

// Role type (must match backend)
type UserRole = 'admin' | 'lawyer' | 'staff' | 'client' | 'detective';

// Portal paths per role
const ROLE_PORTALS: Record<UserRole, string> = {
  admin: '/admin',
  lawyer: '/lawyer',
  staff: '/lawyer',
  client: '/client',
  detective: '/detective',
};

// Public routes that don't require authentication
const PUBLIC_ROUTES = [
  '/',
  '/login',
  '/signup',
  '/forgot-password',
  '/reset-password',
  '/about',
  '/pricing',
  '/contact',
  '/privacy',
  '/terms',
];

// API routes (should be handled by API, not middleware)
const API_PREFIX = '/api';

// Static file patterns
const STATIC_PATTERNS = [
  '/_next',
  '/favicon.ico',
  '/images',
  '/fonts',
  '/robots.txt',
  '/sitemap.xml',
];

// Role-to-portal mapping for access control
// Note: admin can access ALL portals
const PORTAL_ROLES: Record<string, UserRole[]> = {
  '/admin': ['admin'],
  '/lawyer': ['lawyer', 'staff', 'admin'],
  '/client': ['client', 'admin'],
  '/detective': ['detective', 'admin'],
};

/**
 * Check if the path is public (no auth required)
 */
function isPublicRoute(pathname: string): boolean {
  // Exact match for public routes
  if (PUBLIC_ROUTES.includes(pathname)) {
    return true;
  }

  // Check for public route prefixes (e.g., /reset-password/[token])
  return PUBLIC_ROUTES.some(
    (route) => route !== '/' && pathname.startsWith(`${route}/`)
  );
}

/**
 * Check if the path is a static file or API route
 */
function isStaticOrApi(pathname: string): boolean {
  if (pathname.startsWith(API_PREFIX)) {
    return true;
  }
  return STATIC_PATTERNS.some((pattern) => pathname.startsWith(pattern));
}

/**
 * Get the portal path from a full pathname
 */
function getPortalFromPath(pathname: string): string | null {
  const portals = Object.keys(PORTAL_ROLES);
  for (const portal of portals) {
    if (pathname.startsWith(portal)) {
      return portal;
    }
  }
  return null;
}

/**
 * Check if a role can access a portal
 */
function canAccessPortal(role: UserRole, portal: string): boolean {
  const allowedRoles = PORTAL_ROLES[portal];
  if (!allowedRoles) return false;
  return allowedRoles.includes(role);
}

/**
 * Parse user data from cookie
 */
function getUserFromCookie(request: NextRequest): { role: UserRole } | null {
  const userCookie = request.cookies.get('user_data');
  if (!userCookie?.value) {
    return null;
  }

  try {
    const userData = JSON.parse(decodeURIComponent(userCookie.value));
    if (userData && userData.role) {
      return { role: userData.role as UserRole };
    }
  } catch {
    // Invalid cookie format
  }

  return null;
}

/**
 * Check if user has valid auth token
 */
function hasAuthToken(request: NextRequest): boolean {
  const accessToken = request.cookies.get('access_token');
  return !!accessToken?.value;
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip static files and API routes
  if (isStaticOrApi(pathname)) {
    return NextResponse.next();
  }

  // Allow public routes
  if (isPublicRoute(pathname)) {
    // If user is already logged in and tries to access login/signup, redirect to portal
    if (['/login', '/signup'].includes(pathname)) {
      const user = getUserFromCookie(request);
      if (user && hasAuthToken(request)) {
        const portalPath = ROLE_PORTALS[user.role] || '/lawyer';
        return NextResponse.redirect(
          new URL(`${portalPath}/dashboard`, request.url)
        );
      }
    }
    return NextResponse.next();
  }

  // Check authentication for protected routes
  if (!hasAuthToken(request)) {
    // Redirect to login with return URL
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('returnUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Get user data
  const user = getUserFromCookie(request);
  if (!user) {
    // No user data, redirect to login
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('returnUrl', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Check portal access
  const portal = getPortalFromPath(pathname);
  if (portal) {
    if (!canAccessPortal(user.role, portal)) {
      // User trying to access wrong portal, redirect to their portal
      const correctPortal = ROLE_PORTALS[user.role] || '/lawyer';
      return NextResponse.redirect(
        new URL(`${correctPortal}/dashboard`, request.url)
      );
    }
  }

  // Handle legacy /cases route - redirect to role-appropriate portal
  if (pathname === '/cases' || pathname.startsWith('/cases/')) {
    const portalPath = ROLE_PORTALS[user.role] || '/lawyer';
    const newPath = pathname.replace('/cases', `${portalPath}/cases`);
    return NextResponse.redirect(new URL(newPath, request.url));
  }

  // Handle /dashboard redirect to role-appropriate dashboard
  if (pathname === '/dashboard') {
    const portalPath = ROLE_PORTALS[user.role] || '/lawyer';
    return NextResponse.redirect(
      new URL(`${portalPath}/dashboard`, request.url)
    );
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
};
