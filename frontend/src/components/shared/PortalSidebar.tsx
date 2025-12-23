'use client';

/**
 * PortalSidebar Component
 * LDS2 Icon-only sidebar with tooltips (48px width)
 *
 * Features:
 * - Desktop: Icon-only mode with hover tooltips
 * - Mobile: Full sidebar with labels (unchanged)
 */

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Menu, X, LogOut, ChevronDown, ChevronRight } from 'lucide-react';
import { Logo } from './Logo';
import { NotificationDropdown } from './NotificationDropdown';
import { useAuth } from '@/hooks/useAuth';
import { useRole } from '@/hooks/useRole';
import { ROLE_DISPLAY_NAMES } from '@/types/user';

export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon: React.ReactNode;
  badge?: number;
}

export interface NavGroup {
  id: string;
  label?: string;
  items: NavItem[];
  collapsible?: boolean;
  defaultCollapsed?: boolean;
}

interface PortalSidebarProps {
  groups: NavGroup[];
  headerContent?: React.ReactNode;
  footerContent?: React.ReactNode;
}

// Simple Tooltip component for icon-only mode
function Tooltip({ children, content }: { children: React.ReactNode; content: string }) {
  return (
    <div className="relative group">
      {children}
      <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-xs rounded
        opacity-0 invisible group-hover:opacity-100 group-hover:visible
        transition-all duration-150 whitespace-nowrap z-50 top-1/2 -translate-y-1/2">
        {content}
        <div className="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900" />
      </div>
    </div>
  );
}

export function PortalSidebar({
  groups,
  headerContent,
  footerContent,
}: PortalSidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { role } = useRole();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(
    () => new Set(groups.filter(g => g.defaultCollapsed).map(g => g.id))
  );

  const toggleGroup = (groupId: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupId)) {
        next.delete(groupId);
      } else {
        next.add(groupId);
      }
      return next;
    });
  };

  const isActiveLink = (href: string) => {
    if (!pathname) return false;
    if (href === '/dashboard') {
      return pathname === '/dashboard';
    }
    return pathname.startsWith(href);
  };

  // Desktop icon-only nav item
  const renderDesktopNavItem = (item: NavItem) => {
    const isActive = isActiveLink(item.href);

    return (
      <Tooltip key={item.id} content={item.label}>
        <Link
          href={item.href}
          className={`relative w-10 h-10 flex items-center justify-center rounded-lg transition-all duration-150 ${
            isActive
              ? 'bg-primary/10 text-primary border-l-2 border-primary -ml-[2px] pl-[2px]'
              : 'text-gray-500 hover:bg-gray-100 hover:text-gray-700'
          }`}
        >
          {item.icon}
          {item.badge !== undefined && item.badge > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] font-medium rounded-full flex items-center justify-center">
              {item.badge > 9 ? '9+' : item.badge}
            </span>
          )}
        </Link>
      </Tooltip>
    );
  };

  // Desktop icon-only sidebar content
  const desktopSidebarContent = (
    <div className="flex flex-col h-full items-center py-2">
      {/* Logo - compact */}
      <Link href="/dashboard" className="mb-4 mt-1">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
          <span className="text-white font-bold text-sm">L</span>
        </div>
      </Link>

      {/* Navigation Items - icon only */}
      <nav className="flex-1 flex flex-col items-center gap-1 w-full px-1">
        {groups.map((group) => (
          <div key={group.id} className="w-full flex flex-col items-center gap-1">
            {group.items.map(renderDesktopNavItem)}
            {/* Separator between groups */}
            {group.id !== groups[groups.length - 1].id && (
              <div className="w-6 h-px bg-gray-200 my-2" />
            )}
          </div>
        ))}
      </nav>

      {/* User Avatar & Logout */}
      <div className="flex flex-col items-center gap-2 mt-2 pt-2 border-t border-gray-100 w-full">
        <Tooltip content={user?.name || '사용자'}>
          <div className="w-8 h-8 bg-primary-light rounded-full flex items-center justify-center cursor-default">
            <span className="text-primary font-semibold text-xs">
              {user?.name?.charAt(0) || 'U'}
            </span>
          </div>
        </Tooltip>
        <Tooltip content="로그아웃">
          <button
            onClick={logout}
            className="w-10 h-10 flex items-center justify-center text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </Tooltip>
      </div>
    </div>
  );

  // Mobile nav item (with labels)
  const renderMobileNavItem = (item: NavItem) => {
    const isActive = isActiveLink(item.href);

    return (
      <Link
        key={item.id}
        href={item.href}
        onClick={() => setIsMobileMenuOpen(false)}
        className={`flex items-center gap-2 px-2 py-2 rounded-lg text-sm font-medium transition-colors ${
          isActive
            ? 'bg-primary text-white shadow-sm'
            : 'text-gray-700 hover:bg-gray-100'
        }`}
      >
        <span className={isActive ? 'text-white' : 'text-gray-500'}>
          {item.icon}
        </span>
        <span className="flex-1">{item.label}</span>
        {item.badge !== undefined && item.badge > 0 && (
          <span
            className={`px-2 py-0.5 text-xs font-medium rounded-full ${
              isActive ? 'bg-white/20 text-white' : 'bg-primary-light text-primary'
            }`}
          >
            {item.badge}
          </span>
        )}
      </Link>
    );
  };

  // Mobile nav group (with labels)
  const renderMobileNavGroup = (group: NavGroup) => {
    const isCollapsed = collapsedGroups.has(group.id);

    return (
      <div key={group.id} className="mb-4">
        {group.label && (
          <button
            onClick={() => group.collapsible && toggleGroup(group.id)}
            className={`w-full flex items-center justify-between px-2 py-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider ${
              group.collapsible ? 'hover:text-gray-700 cursor-pointer' : ''
            }`}
          >
            <span>{group.label}</span>
            {group.collapsible && (
              <span className="text-gray-400">
                {isCollapsed ? (
                  <ChevronRight className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </span>
            )}
          </button>
        )}
        {!isCollapsed && (
          <div className="space-y-1">{group.items.map(renderMobileNavItem)}</div>
        )}
      </div>
    );
  };

  return (
    <>
      {/* Desktop Sidebar - Icon only (48px) */}
      <aside className="hidden lg:flex lg:flex-col lg:w-12 lg:fixed lg:inset-y-0 lg:left-0 bg-white border-r border-gray-200 z-30">
        {desktopSidebarContent}
      </aside>

      {/* Mobile Header */}
      <header className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-40 px-4 flex items-center justify-between">
        <Link href="/dashboard">
          <Logo size="sm" />
        </Link>
        <div className="flex items-center gap-2">
          <NotificationDropdown />
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
            aria-label="메뉴"
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>
      </header>

      {/* Mobile Sidebar Overlay */}
      {isMobileMenuOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Mobile Sidebar - Full width with labels */}
      <aside
        className={`lg:hidden fixed top-0 right-0 bottom-0 w-72 bg-white z-50 transform transition-transform duration-300 ease-in-out flex flex-col ${
          isMobileMenuOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-100">
          <Link href="/dashboard">
            <Logo size="sm" />
          </Link>
          <button
            onClick={() => setIsMobileMenuOpen(false)}
            className="p-2 text-gray-600 hover:text-gray-900"
            aria-label="닫기"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <nav className="flex-1 px-3 py-4 overflow-y-auto">
          {groups.map(renderMobileNavGroup)}
        </nav>
        <div className="px-4 py-4 border-t border-gray-100">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-10 h-10 bg-primary-light rounded-full flex items-center justify-center">
              <span className="text-primary font-semibold text-sm">
                {user?.name?.charAt(0) || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.name || '사용자'}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {role ? ROLE_DISPLAY_NAMES[role] : ''}
              </p>
            </div>
          </div>
          <button
            onClick={() => {
              logout();
              setIsMobileMenuOpen(false);
            }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut className="w-4 h-4" />
            로그아웃
          </button>
        </div>
      </aside>
    </>
  );
}

export default PortalSidebar;
