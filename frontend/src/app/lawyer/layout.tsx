'use client';

/**
 * Lawyer Portal Layout
 * 003-role-based-ui Feature
 * Updated: navbar-sidebar-refactoring
 *
 * Layout for the lawyer portal with sidebar navigation.
 * Uses PortalSidebar with NavGroup for hierarchical navigation.
 */

import { PortalSidebar, NavGroup } from '@/components/shared/PortalSidebar';
import RoleGuard from '@/components/auth/RoleGuard';
import { useAuth } from '@/hooks/useAuth';
import { useRole } from '@/hooks/useRole';
import { UserRole } from '@/types/user';
import {
  LayoutDashboard,
  Briefcase,
  Users,
  Search,
  Calendar,
  MessageSquare,
  CreditCard,
} from 'lucide-react';

// Lawyer navigation groups with hierarchical structure
const lawyerNavGroups: NavGroup[] = [
  {
    id: 'core',
    items: [
      {
        id: 'dashboard',
        label: '대시보드',
        href: '/lawyer/dashboard',
        icon: <LayoutDashboard className="w-5 h-5" />,
      },
      {
        id: 'cases',
        label: '케이스',
        href: '/lawyer/cases',
        icon: <Briefcase className="w-5 h-5" />,
      },
    ],
  },
  {
    id: 'management',
    label: '관리',
    collapsible: true,
    defaultCollapsed: true,
    items: [
      {
        id: 'clients',
        label: '의뢰인',
        href: '/lawyer/clients',
        icon: <Users className="w-5 h-5" />,
      },
      {
        id: 'investigators',
        label: '탐정',
        href: '/lawyer/investigators',
        icon: <Search className="w-5 h-5" />,
      },
      {
        id: 'calendar',
        label: '일정',
        href: '/lawyer/calendar',
        icon: <Calendar className="w-5 h-5" />,
      },
      {
        id: 'messages',
        label: '메시지',
        href: '/lawyer/messages',
        icon: <MessageSquare className="w-5 h-5" />,
      },
      {
        id: 'billing',
        label: '청구/결제',
        href: '/lawyer/billing',
        icon: <CreditCard className="w-5 h-5" />,
      },
    ],
  },
];

const ALLOWED_ROLES: UserRole[] = ['lawyer', 'staff', 'admin'];

export default function LawyerLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  const { role } = useRole();

  const renderContent = () => {
    if (!user || !role) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
        </div>
      );
    }

    return (
      <div className="flex min-h-screen bg-[var(--color-bg-secondary)]">
        {/* Sidebar */}
        <PortalSidebar groups={lawyerNavGroups} />

        {/* Main Content */}
        <main className="flex-1 lg:ml-12 min-h-screen">
          {/* Mobile header spacing */}
          <div className="h-16 lg:hidden" />

          {/* Page Content */}
          <div className="p-2 lg:p-3">
            {children}
          </div>
        </main>
      </div>
    );
  };

  return (
    <RoleGuard allowedRoles={ALLOWED_ROLES}>
      {renderContent()}
    </RoleGuard>
  );
}
