'use client';

/**
 * Detective Portal Layout
 * 003-role-based-ui Feature
 *
 * Layout for the detective portal with field investigation tools.
 * Uses design system tokens.
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import PortalSidebar, { NavIcons, NavItem } from '@/components/shared/PortalSidebar';
import { logout } from '@/lib/api/auth';

// Detective navigation items
const detectiveNavItems: NavItem[] = [
  {
    id: 'dashboard',
    label: '대시보드',
    href: '/detective/dashboard',
    icon: <NavIcons.Dashboard />,
  },
  {
    id: 'cases',
    label: '의뢰 관리',
    href: '/detective/cases',
    icon: <NavIcons.Cases />,
  },
  {
    id: 'field',
    label: '현장 조사',
    href: '/detective/field',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    id: 'calendar',
    label: '일정 관리',
    href: '/detective/calendar',
    icon: <NavIcons.Calendar />,
  },
  {
    id: 'messages',
    label: '메시지',
    href: '/detective/messages',
    icon: <NavIcons.Messages />,
    badge: 0,
  },
  {
    id: 'earnings',
    label: '정산/수익',
    href: '/detective/earnings',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
];

interface UserData {
  name: string;
  email: string;
  role: 'detective';
}

export default function DetectiveLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const getUserData = () => {
      try {
        const userCookie = document.cookie
          .split('; ')
          .find(row => row.startsWith('user_data='));

        if (userCookie) {
          const userData = JSON.parse(decodeURIComponent(userCookie.split('=')[1]));
          if (userData && userData.role === 'detective') {
            setUser(userData);
          } else {
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
        navItems={detectiveNavItems}
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
          <div className="flex-1" />
          <div className="flex items-center gap-4">
            {/* Quick field record button */}
            <button
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] transition-colors min-h-[44px]"
              onClick={() => router.push('/detective/field')}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span className="text-sm font-medium">현장 기록</span>
            </button>

            {/* Notification bell */}
            <button
              className="relative p-2 rounded-lg hover:bg-[var(--color-bg-secondary)] transition-colors min-h-[44px] min-w-[44px] flex items-center justify-center"
              aria-label="알림"
            >
              <svg className="w-5 h-5 text-[var(--color-text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
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
