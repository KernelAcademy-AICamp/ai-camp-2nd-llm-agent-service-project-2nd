'use client';

/**
 * Lawyer Case List Page
 * 003-role-based-ui Feature - US3
 * 010-dashboard-first-flow - Added case creation functionality
 * 011-production-bug-fixes - Added active/closed tabs and permanent delete
 *
 * Main case management page for lawyers with filtering, sorting, and bulk actions.
 */

import { useState } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { useCaseList } from '@/hooks/useCaseList';
import { CaseCard } from '@/components/lawyer/CaseCard';
import { CaseTable } from '@/components/lawyer/CaseTable';
import { BulkActionBar } from '@/components/lawyer/BulkActionBar';
import AddCaseModal from '@/components/cases/AddCaseModal';
import { CasesEmptyState } from '@/components/cases/CasesEmptyState';
import { ErrorState } from '@/components/shared/EmptyState';

type ViewMode = 'grid' | 'table';

export default function LawyerCasesPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const {
    cases,
    isLoading,
    error,
    pagination,
    setPage,
    statusCounts,
    sort,
    setSort,
    selectedIds,
    setSelectedIds,
    clearSelection,
    executeBulkAction,
    isBulkActionLoading,
    refresh,
    showClosed,
    setShowClosed,
    permanentDeleteCase,
  } = useCaseList();

  // Count for tabs
  const activeCount = (statusCounts.active || 0) + (statusCounts.open || 0) + (statusCounts.in_progress || 0);
  const closedCount = statusCounts.closed || 0;

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

  const handlePermanentDelete = async (caseId: string) => {
    const success = await permanentDeleteCase(caseId);
    if (success) {
      setDeleteConfirmId(null);
    } else {
      alert('삭제에 실패했습니다.');
    }
  };

  return (
    <div className="space-y-4">
      {/* Header - LDS2 Compact */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-[var(--color-text-primary)]">케이스 관리</h1>
          <p className="text-xs text-[var(--color-text-secondary)]">
            총 {pagination.total}건의 케이스
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* View Mode Toggle - LDS2 Compact */}
          <div className="flex bg-gray-100 dark:bg-neutral-700 rounded p-0.5">
            <button
              type="button"
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded ${viewMode === 'grid' ? 'bg-white dark:bg-neutral-800 shadow-sm' : ''}`}
              title="카드 보기"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded ${viewMode === 'table' ? 'bg-white dark:bg-neutral-800 shadow-sm' : ''}`}
              title="테이블 보기"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </button>
          </div>
          {/* Add Case Button - LDS2 Compact */}
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="flex items-center px-3 py-1.5 text-xs bg-[var(--color-primary)] text-white font-medium rounded shadow-sm hover:bg-[var(--color-primary-dark)] transition-colors"
          >
            <Plus className="w-4 h-4 mr-1" />
            새 사건 등록
          </button>
        </div>
      </div>

      {/* Active/Closed Tabs - LDS2 Compact */}
      <div className="flex border-b border-gray-200 dark:border-neutral-700">
        <button
          type="button"
          onClick={() => setShowClosed(false)}
          className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
            !showClosed
              ? 'border-[var(--color-primary)] text-[var(--color-primary)]'
              : 'border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
          }`}
        >
          활성 사건
          {activeCount > 0 && (
            <span className="ml-1.5 px-1.5 py-0.5 text-[10px] rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
              {activeCount}
            </span>
          )}
        </button>
        <button
          type="button"
          onClick={() => setShowClosed(true)}
          className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
            showClosed
              ? 'border-[var(--color-primary)] text-[var(--color-primary)]'
              : 'border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
          }`}
        >
          종료된 사건
          {closedCount > 0 && (
            <span className="ml-1.5 px-1.5 py-0.5 text-[10px] rounded-full bg-gray-100 text-gray-600 dark:bg-neutral-700 dark:text-gray-300">
              {closedCount}
            </span>
          )}
        </button>
      </div>

      {/* Error State */}
      {error && (
        <ErrorState
          title="사건 목록을 불러올 수 없습니다"
          message={error}
          onRetry={refresh}
          retryText="다시 불러오기"
        />
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
          {/* Closed cases: simple list with delete button - LDS2 Compact */}
          {showClosed ? (
            <div className="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg divide-y divide-gray-100 dark:divide-neutral-700">
              {cases.map((caseItem) => (
                <div key={caseItem.id} className="flex items-center justify-between px-3 py-2 hover:bg-gray-50 dark:hover:bg-neutral-750">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-xs font-medium text-[var(--color-text-primary)] truncate">
                      {caseItem.title}
                    </h3>
                    <p className="text-[10px] text-[var(--color-text-secondary)] mt-0.5">
                      {caseItem.clientName && `${caseItem.clientName} · `}
                      종료일: {new Date(caseItem.updatedAt).toLocaleDateString('ko-KR')}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setDeleteConfirmId(caseItem.id)}
                    className="ml-3 p-1.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                    title="완전 삭제"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : viewMode === 'grid' ? (
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
            <div className="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg overflow-hidden">
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
          {cases.length === 0 && !showClosed && (
            <CasesEmptyState
              onCreateCase={() => setIsModalOpen(true)}
              isNewUser={pagination.total === 0}
            />
          )}
          {cases.length === 0 && showClosed && (
            <div className="text-center py-12">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                종료된 케이스가 없습니다.
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
                className="px-3 py-1 rounded border border-gray-300 dark:border-neutral-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-neutral-700"
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
                className="px-3 py-1 rounded border border-gray-300 dark:border-neutral-700 text-sm disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-neutral-700"
              >
                다음
              </button>
            </div>
          )}
        </>
      )}

      {/* Bulk Action Bar (hide when showing closed cases) */}
      {!showClosed && (
        <BulkActionBar
          selectedCount={selectedIds.length}
          onAction={handleBulkAction}
          onClearSelection={clearSelection}
          isLoading={isBulkActionLoading}
        />
      )}

      {/* Add Case Modal */}
      <AddCaseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={refresh}
      />

      {/* Delete Confirmation Modal - LDS2 Compact */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50"
            onClick={() => setDeleteConfirmId(null)}
          />
          <div className="relative bg-white dark:bg-neutral-800 rounded-lg shadow-lg p-4 max-w-sm w-full mx-4">
            <h3 className="text-sm font-semibold text-[var(--color-text-primary)] mb-1.5">
              사건 완전 삭제
            </h3>
            <p className="text-xs text-[var(--color-text-secondary)] mb-4">
              이 사건을 완전히 삭제하시겠습니까?<br />
              <span className="text-red-500 font-medium">
                삭제된 데이터는 복구할 수 없습니다.
              </span>
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeleteConfirmId(null)}
                className="px-3 py-1.5 text-xs font-medium text-[var(--color-text-secondary)] hover:bg-gray-100 dark:hover:bg-neutral-700 rounded transition-colors"
              >
                취소
              </button>
              <button
                type="button"
                onClick={() => handlePermanentDelete(deleteConfirmId)}
                className="px-3 py-1.5 text-xs font-medium text-white bg-red-500 hover:bg-red-600 rounded transition-colors"
              >
                삭제
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
