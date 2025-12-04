'use client';

/**
 * Lawyer Case List Page
 * 003-role-based-ui Feature - US3
 *
 * Main case management page for lawyers with filtering, sorting, and bulk actions.
 */

import { useState } from 'react';
import { useCaseList } from '@/hooks/useCaseList';
import { CaseCard } from '@/components/lawyer/CaseCard';
import { CaseTable } from '@/components/lawyer/CaseTable';
import { CaseFilter } from '@/components/lawyer/CaseFilter';
import { BulkActionBar } from '@/components/lawyer/BulkActionBar';

type ViewMode = 'grid' | 'table';

export default function LawyerCasesPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const {
    cases,
    isLoading,
    error,
    pagination,
    setPage,
    filters,
    statusCounts,
    setFilters,
    resetFilters,
    sort,
    setSort,
    selectedIds,
    setSelectedIds,
    clearSelection,
    executeBulkAction,
    isBulkActionLoading,
  } = useCaseList();

  const handleBulkAction = async (action: string, params?: Record<string, string>) => {
    const results = await executeBulkAction(action, params);
    const failed = results.filter((r) => !r.success);
    if (failed.length > 0) {
      alert(`${failed.length}개 케이스에서 오류가 발생했습니다.`);
    }
  };

  const handleCardSelect = (id: string, selected: boolean) => {
    if (selected) {
      setSelectedIds([...selectedIds, id]);
    } else {
      setSelectedIds(selectedIds.filter((i) => i !== id));
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)]">케이스 관리</h1>
          <p className="text-[var(--color-text-secondary)]">
            총 {pagination.total}건의 케이스
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded ${viewMode === 'grid' ? 'bg-white shadow' : ''}`}
              title="카드 보기"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('table')}
              className={`p-2 rounded ${viewMode === 'table' ? 'bg-white shadow' : ''}`}
              title="테이블 보기"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <CaseFilter
        filters={filters}
        statusCounts={statusCounts}
        onFilterChange={setFilters}
        onReset={resetFilters}
      />

      {/* Error State */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
        </div>
      )}

      {/* Case List */}
      {!isLoading && !error && (
        <>
          {viewMode === 'grid' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {cases.map((caseItem) => (
                <CaseCard
                  key={caseItem.id}
                  id={caseItem.id}
                  title={caseItem.title}
                  clientName={caseItem.clientName}
                  status={caseItem.status}
                  updatedAt={caseItem.updatedAt}
                  evidenceCount={caseItem.evidenceCount}
                  progress={caseItem.progress}
                  selected={selectedIds.includes(caseItem.id)}
                  onSelect={handleCardSelect}
                />
              ))}
            </div>
          ) : (
            <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <CaseTable
                cases={cases}
                selectedIds={selectedIds}
                onSelectionChange={setSelectedIds}
                sortBy={sort.sortBy}
                sortOrder={sort.sortOrder}
                onSort={setSort}
              />
            </div>
          )}

          {/* Empty State */}
          {cases.length === 0 && (
            <div className="text-center py-12">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">케이스 없음</h3>
              <p className="mt-1 text-sm text-gray-500">
                검색 조건에 맞는 케이스가 없습니다.
              </p>
            </div>
          )}

          {/* Pagination */}
          {pagination.totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <button
                type="button"
                onClick={() => setPage(pagination.page - 1)}
                disabled={pagination.page === 1}
                className="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                이전
              </button>
              <span className="text-sm text-[var(--color-text-secondary)]">
                {pagination.page} / {pagination.totalPages}
              </span>
              <button
                type="button"
                onClick={() => setPage(pagination.page + 1)}
                disabled={pagination.page === pagination.totalPages}
                className="px-3 py-1 rounded border border-gray-300 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                다음
              </button>
            </div>
          )}
        </>
      )}

      {/* Bulk Action Bar */}
      <BulkActionBar
        selectedCount={selectedIds.length}
        onAction={handleBulkAction}
        onClearSelection={clearSelection}
        isLoading={isBulkActionLoading}
      />
    </div>
  );
}
