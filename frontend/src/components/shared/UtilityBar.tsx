'use client';

/**
 * UtilityBar Component
 * LDS2 Top utility bar for case detail pages
 *
 * Features:
 * - Left: Breadcrumb + Case name
 * - Center: Status badge + Assignee + Deadline (uses empty space)
 * - Right: Action icons (Settings, Notifications, Share)
 */

import { Settings, Share2, ChevronRight } from 'lucide-react';
import Link from 'next/link';
import { NotificationDropdown } from './NotificationDropdown';

export type CaseStatus = 'pending' | 'in_progress' | 'completed' | 'on_hold';

interface UtilityBarProps {
  // Breadcrumb
  breadcrumbs?: { label: string; href?: string }[];

  // Case info for center area
  caseStatus?: CaseStatus;
  assignee?: string;
  deadline?: Date;

  // Actions
  onSettingsClick?: () => void;
  onShareClick?: () => void;
  showNotifications?: boolean;
}

// Status badge configuration
const STATUS_CONFIG: Record<CaseStatus, { label: string; className: string }> = {
  pending: {
    label: '대기중',
    className: 'bg-gray-100 text-gray-700',
  },
  in_progress: {
    label: '진행중',
    className: 'bg-blue-100 text-blue-700',
  },
  completed: {
    label: '완료',
    className: 'bg-green-100 text-green-700',
  },
  on_hold: {
    label: '보류',
    className: 'bg-yellow-100 text-yellow-700',
  },
};

// Calculate days until deadline
function getDaysUntil(deadline: Date): number {
  const now = new Date();
  const diff = deadline.getTime() - now.getTime();
  return Math.ceil(diff / (1000 * 60 * 60 * 24));
}

// Simple icon button
function IconButton({
  icon: Icon,
  tooltip,
  onClick,
}: {
  icon: React.ComponentType<{ className?: string }>;
  tooltip: string;
  onClick?: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="relative group p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
      aria-label={tooltip}
    >
      <Icon className="w-4 h-4" />
      <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 text-xs text-white bg-gray-900 rounded opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all whitespace-nowrap">
        {tooltip}
      </span>
    </button>
  );
}

export function UtilityBar({
  breadcrumbs = [],
  caseStatus,
  assignee,
  deadline,
  onSettingsClick,
  onShareClick,
  showNotifications = true,
}: UtilityBarProps) {
  const daysLeft = deadline ? getDaysUntil(deadline) : null;

  return (
    <div className="h-10 px-4 flex items-center gap-4 border-b border-gray-200 bg-white">
      {/* Left: Breadcrumb */}
      <nav className="flex items-center gap-1.5 text-sm">
        {breadcrumbs.map((crumb, index) => (
          <span key={index} className="flex items-center gap-1.5">
            {index > 0 && <ChevronRight className="w-3 h-3 text-gray-400" />}
            {crumb.href ? (
              <Link
                href={crumb.href}
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                {crumb.label}
              </Link>
            ) : (
              <span className="font-medium text-gray-900">{crumb.label}</span>
            )}
          </span>
        ))}
      </nav>

      {/* Center: Status info (fills empty space) */}
      <div className="flex-1 flex items-center justify-center gap-3">
        {caseStatus && (
          <span
            className={`px-2 py-0.5 text-xs font-medium rounded ${STATUS_CONFIG[caseStatus].className}`}
          >
            {STATUS_CONFIG[caseStatus].label}
          </span>
        )}

        {assignee && (
          <span className="text-xs text-gray-500">
            담당: <span className="text-gray-700">{assignee}</span>
          </span>
        )}

        {daysLeft !== null && (
          <span
            className={`text-xs font-medium ${
              daysLeft < 0
                ? 'text-red-600'
                : daysLeft <= 3
                  ? 'text-orange-600'
                  : 'text-gray-500'
            }`}
          >
            {daysLeft < 0 ? `D+${Math.abs(daysLeft)}` : `D-${daysLeft}`}
          </span>
        )}
      </div>

      {/* Right: Action icons */}
      <div className="flex items-center gap-1">
        {onSettingsClick && (
          <IconButton icon={Settings} tooltip="설정" onClick={onSettingsClick} />
        )}

        {showNotifications && <NotificationDropdown />}

        {onShareClick && (
          <IconButton icon={Share2} tooltip="공유" onClick={onShareClick} />
        )}
      </div>
    </div>
  );
}

export default UtilityBar;
