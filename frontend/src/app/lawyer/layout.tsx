'use client';

/**
 * Lawyer Portal Layout
 * 003-role-based-ui Feature
 *
 * Layout for the lawyer portal with sidebar navigation.
 * Uses design system tokens.
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import PortalSidebar, { NavIcons, NavItem } from '@/components/shared/PortalSidebar';
import { logout } from '@/lib/api/auth';

// Lawyer navigation items
const lawyerNavItems: NavItem[] = [
  {
    id: 'dashboard',
    label: '대시보드',
    href: '/lawyer/dashboard',
    icon: <NavIcons.Dashboard />,
  },
  {
    id: 'cases',
    label: '케이스 관리',
    href: '/lawyer/cases',
    icon: <NavIcons.Cases />,
  },
  {
    id: 'clients',
    label: '의뢰인 관리',
    href: '/lawyer/clients',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
  {
    id: 'investigators',
    label: '탐정/조사원',
    href: '/lawyer/investigators',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
  },
  {
    id: 'calendar',
    label: '일정 관리',
    href: '/lawyer/calendar',
    icon: <NavIcons.Calendar />,
  },
  {
    id: 'messages',
    label: '메시지',
    href: '/lawyer/messages',
    icon: <NavIcons.Messages />,
    badge: 0, // Will be updated with unread count
  },
  {
    id: 'billing',
    label: '청구/정산',
    href: '/lawyer/billing',
    icon: <NavIcons.Billing />,
  },
];

interface UserData {
  name: string;
  email: string;
  role: 'lawyer' | 'staff' | 'admin';
}

export default function LawyerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Get user data from cookie
    const getUserData = () => {
      try {
        const userCookie = document.cookie
          .split('; ')
          .find(row => row.startsWith('user_data='));

        if (userCookie) {
          const userData = JSON.parse(decodeURIComponent(userCookie.split('=')[1]));
          if (userData && ['lawyer', 'staff', 'admin'].includes(userData.role)) {
            setUser(userData);
          } else {
            // Invalid role for lawyer portal
            router.push('/login');
          }
        } else {
          router.push('/login');
        }
      } catch {
        router.push('/login');
      } finally {
        setLoading(false);
      }
    };

    getUserData();
  }, [router]);

  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      // Clear cookies and redirect
      document.cookie = 'access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      document.cookie = 'user_data=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      router.push('/login');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]"></div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex min-h-screen bg-[var(--color-bg-secondary)]">
      {/* Sidebar */}
      <PortalSidebar
        role={user.role}
        userName={user.name}
        userEmail={user.email}
        navItems={lawyerNavItems}
        onLogout={handleLogout}
      />

      {/* Main Content */}
      <main
        className="flex-1 ml-64"
        style={{
          minHeight: '100vh',
        }}
      >
        {/* Top Header */}
        <header className="sticky top-0 z-10 h-16 bg-white border-b border-[var(--color-border-default)] flex items-center px-6">
          <div className="flex-1">
            {/* Breadcrumb or page title can go here */}
          </div>
          <div className="flex items-center gap-4">
            {/* Notification bell */}
            <button
              className="relative p-2 rounded-lg hover:bg-[var(--color-bg-secondary)] transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
              aria-label="알림"
            >
              <svg className="w-5 h-5 text-[var(--color-text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              {/* Badge for unread notifications */}
              <span className="absolute top-1 right-1 w-2 h-2 bg-[var(--color-error)] rounded-full"></span>
            </button>

            {/* User menu */}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-[var(--color-primary)] flex items-center justify-center text-white font-semibold text-sm">
                {user.name.slice(0, 2).toUpperCase()}
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
