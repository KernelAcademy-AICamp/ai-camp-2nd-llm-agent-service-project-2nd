/**
 * StatsCard Component
 * 003-role-based-ui Feature - US2
 *
 * Displays a statistics card with label, value, and optional trend indicator.
 */

'use client';

import { ReactNode } from 'react';

export interface StatsCardProps {
  /** Card label (e.g., "전체 케이스") */
  label: string;
  /** Numeric value to display */
  value: number;
  /** Change from previous period */
  change?: number;
  /** Trend direction */
  trend?: 'up' | 'down' | 'stable';
  /** Optional icon */
  icon?: ReactNode;
  /** Additional CSS classes */
  className?: string;
}

/**
 * StatsCard - Displays statistics with trend indicator
 *
 * Usage:
 * ```tsx
 * <StatsCard
 *   label="전체 케이스"
 *   value={25}
 *   change={3}
 *   trend="up"
 * />
 * ```
 */
export function StatsCard({
  label,
  value,
  change,
  trend,
  icon,
  className = '',
}: StatsCardProps) {
  const getTrendColor = () => {
    switch (trend) {
      case 'up':
        return 'text-green-600';
      case 'down':
        return 'text-red-600';
      default:
        return 'text-gray-500';
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return '↑';
      case 'down':
        return '↓';
      case 'stable':
        return '→';
      default:
        return null;
    }
  };

  const formatChange = () => {
    if (change === undefined || change === null) return null;
    const prefix = change > 0 ? '+' : '';
    return `${prefix}${change}`;
  };

  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}
      role="region"
      aria-label={`${label} 통계`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-600 mb-1">{label}</p>
          <p className="text-3xl font-bold text-gray-900">{value}</p>
        </div>
        {icon && (
          <div className="p-3 bg-[var(--color-primary-light,#e0f2fe)] rounded-lg">
            {icon}
          </div>
        )}
      </div>

      {(trend || change !== undefined) && (
        <div className={`mt-4 flex items-center gap-1 ${getTrendColor()}`}>
          {getTrendIcon() && (
            <span className="text-sm font-medium" data-trend={trend}>
              {getTrendIcon()}
            </span>
          )}
          {formatChange() !== null && (
            <span className="text-sm font-medium">{formatChange()}</span>
          )}
          <span className="text-xs text-gray-500 ml-1">지난 주 대비</span>
        </div>
      )}
    </div>
  );
}

/**
 * StatsCardSkeleton - Loading placeholder for StatsCard
 */
export function StatsCardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div
      className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse ${className}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="h-4 w-20 bg-gray-200 rounded mb-2" />
          <div className="h-8 w-16 bg-gray-200 rounded" />
        </div>
        <div className="w-12 h-12 bg-gray-200 rounded-lg" />
      </div>
      <div className="mt-4 h-4 w-24 bg-gray-200 rounded" />
    </div>
  );
}

export default StatsCard;
