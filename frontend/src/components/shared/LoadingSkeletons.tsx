/**
 * Loading Skeleton Components
 * 003-role-based-ui Feature - T154
 *
 * Reusable skeleton components for loading states across all portals.
 */

'use client';

import React from 'react';

// Base skeleton with pulse animation
export function Skeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
  );
}

// Stats card skeleton
export function StatsCardSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-16" />
        </div>
        <Skeleton className="h-12 w-12 rounded-full" />
      </div>
      <Skeleton className="h-3 w-20 mt-2" />
    </div>
  );
}

// Dashboard skeleton layout
export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <StatsCardSkeleton key={i} />
        ))}
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Large Section */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <Skeleton className="h-5 w-32" />
          </div>
          <div className="divide-y divide-gray-200">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="p-4 flex items-center gap-4">
                <Skeleton className="h-10 w-10 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-3 w-1/2" />
                </div>
                <Skeleton className="h-6 w-16 rounded-full" />
              </div>
            ))}
          </div>
        </div>

        {/* Small Section */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200">
            <Skeleton className="h-5 w-28" />
          </div>
          <div className="p-4 space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="p-3 rounded-lg bg-gray-50">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-3 w-2/3 mt-2" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Table skeleton
export function TableSkeleton({ rows = 5, columns = 4 }: { rows?: number; columns?: number }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex gap-4">
          {[...Array(columns)].map((_, i) => (
            <Skeleton key={i} className="h-4 flex-1" />
          ))}
        </div>
      </div>
      {/* Rows */}
      <div className="divide-y divide-gray-200">
        {[...Array(rows)].map((_, i) => (
          <div key={i} className="p-4 flex gap-4">
            {[...Array(columns)].map((_, j) => (
              <Skeleton key={j} className="h-4 flex-1" />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

// Card list skeleton
export function CardListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {[...Array(count)].map((_, i) => (
        <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
          <div className="flex items-start justify-between mb-4">
            <div className="space-y-2">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-3 w-24" />
            </div>
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
          <div className="space-y-2">
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-3/4" />
          </div>
          <div className="flex gap-2 mt-4">
            <Skeleton className="h-8 w-20 rounded" />
            <Skeleton className="h-8 w-20 rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

// Form skeleton
export function FormSkeleton() {
  return (
    <div className="space-y-6">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-10 w-full rounded-lg" />
        </div>
      ))}
      <div className="flex gap-3 justify-end pt-4">
        <Skeleton className="h-10 w-24 rounded-lg" />
        <Skeleton className="h-10 w-24 rounded-lg" />
      </div>
    </div>
  );
}

// Case detail skeleton
export function CaseDetailSkeleton() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-48" />
        </div>
        <Skeleton className="h-10 w-32 rounded-lg" />
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <Skeleton className="h-4 w-20 mb-2" />
            <Skeleton className="h-6 w-full" />
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200">
        {[...Array(4)].map((_, i) => (
          <Skeleton key={i} className="h-8 w-20" />
        ))}
      </div>

      {/* Content */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-12 w-12 rounded" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Chat/Message skeleton
export function MessageSkeleton() {
  return (
    <div className="space-y-4">
      {[...Array(5)].map((_, i) => (
        <div key={i} className={`flex ${i % 2 === 0 ? '' : 'justify-end'}`}>
          <div className={`max-w-[70%] ${i % 2 === 0 ? '' : 'order-2'}`}>
            <div className="flex items-end gap-2">
              {i % 2 === 0 && <Skeleton className="h-8 w-8 rounded-full" />}
              <div className="space-y-1">
                <Skeleton className={`h-4 w-${12 + (i * 4)} max-w-full rounded-lg`} />
                <Skeleton className="h-16 w-48 rounded-lg" />
                <Skeleton className="h-3 w-16" />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// Full page loading skeleton
export function PageSkeleton({ title = true }: { title?: boolean }) {
  return (
    <div className="space-y-6 p-6">
      {title && (
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-72" />
        </div>
      )}
      <DashboardSkeleton />
    </div>
  );
}
