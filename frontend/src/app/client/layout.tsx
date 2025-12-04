'use client';

/**
 * Client Portal Layout
 * 003-role-based-ui Feature
 *
 * Layout for the client portal with simplified navigation.
 * Responsive design with mobile drawer.
 * Uses design system tokens.
 */

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import PortalSidebar, { NavIcons, NavItem, HamburgerIcon } from '@/components/shared/PortalSidebar';
import { logout } from '@/lib/api/auth';

// Client navigation items - simplified view
const clientNavItems: NavItem[] = [
  {
    id: 'dashboard',
    label: '내 현황',
    href: '/client/dashboard',
    icon: <NavIcons.Dashboard />,
  },
  {
    id: 'cases',
    label: '케이스 상태',
    href: '/client/cases',
    icon: <NavIcons.Cases />,
  },
  {
    id: 'messages',
    label: '변호사 소통',
    href: '/client/messages',
    icon: <NavIcons.Messages />,
    badge: 0,
  },
  {
    id: 'billing',
    label: '청구/결제',
    href: '/client/billing',
    icon: <NavIcons.Billing />,
  },
];

interface UserData {
  name: string;
  email: string;
  role: 'client';
}

export default function ClientLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const getUserData = () => {
      try {
        const userCookie = document.cookie
          .split('; ')
          .find(row => row.startsWith('user_data='));

        if (userCookie) {
          const userData = JSON.parse(decodeURIComponent(userCookie.split('=')[1]));
          if (userData && userData.role === 'client') {
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
        navItems={clientNavItems}
        onLogout={handleLogout}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main Content */}
      <main className="flex-1 lg:ml-64 min-h-screen">
        {/* Top Header */}
        <header className="sticky top-0 z-10 h-16 bg-white border-b border-[var(--color-border-default)] flex items-center px-4 lg:px-6">
          {/* Mobile menu button */}
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-lg hover:bg-[var(--color-bg-secondary)] transition-colors mr-2"
            aria-label="메뉴 열기"
          >
            <HamburgerIcon />
          </button>

          <div className="flex-1" />
          <div className="flex items-center gap-2 sm:gap-4">
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
        <div className="p-4 lg:p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
