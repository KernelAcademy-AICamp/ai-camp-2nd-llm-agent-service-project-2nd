/**
 * Evidence DataTable Component
 * Shadcn/ui style with TanStack Table integration
 *
 * Responsibilities:
 * - Render table structure
 * - Display evidence data with sorting
 * - Integrate with useEvidenceTable hook for logic
 */

import { useState } from 'react';
import { flexRender } from '@tanstack/react-table';
import { ArrowUpDown, MoreVertical, Filter } from 'lucide-react';
import { Evidence } from '@/types/evidence';
import { useEvidenceTable } from '@/hooks/useEvidenceTable';
import { EvidenceTypeIcon } from './EvidenceTypeIcon';
import { EvidenceStatusBadge } from './EvidenceStatusBadge';
import { DataTablePagination } from './DataTablePagination';

interface EvidenceDataTableProps {
  items: Evidence[];
}

export function EvidenceDataTable({ items }: EvidenceDataTableProps) {
  const [typeFilter, setTypeFilterValue] = useState<string>('all');
  const [dateFilter, setDateFilterValue] = useState<string>('all');

  const { table, setTypeFilter, setDateFilter } = useEvidenceTable(items);

  const handleTypeFilterChange = (value: string) => {
    setTypeFilterValue(value);
    setTypeFilter(value);
  };

  const handleDateFilterChange = (value: string) => {
    setDateFilterValue(value);
    setDateFilter(value);
  };

  return (
    <div className="space-y-4">
      {/* Filter Controls - Calm Control UX */}
      <div className="flex items-center space-x-4 bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <Filter className="w-5 h-5 text-gray-400" />

        <div className="flex items-center space-x-2">
          <label htmlFor="type-filter" className="text-sm font-medium text-gray-700">
            유형 필터:
          </label>
          <select
            id="type-filter"
            value={typeFilter}
            onChange={(e) => handleTypeFilterChange(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-accent transition-all"
          >
            <option value="all">전체</option>
            <option value="text">텍스트</option>
            <option value="image">이미지</option>
            <option value="audio">오디오</option>
            <option value="video">비디오</option>
            <option value="pdf">PDF</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <label htmlFor="date-filter" className="text-sm font-medium text-gray-700">
            날짜 필터:
          </label>
          <select
            id="date-filter"
            value={dateFilter}
            onChange={(e) => handleDateFilterChange(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-accent transition-all"
          >
            <option value="all">전체</option>
            <option value="today">오늘</option>
            <option value="week">최근 7일</option>
            <option value="month">최근 30일</option>
          </select>
        </div>

        <div className="text-sm text-gray-500 ml-auto">
          {table.getFilteredRowModel().rows.length}개 / 전체 {items.length}개
        </div>
      </div>

      {/* DataTable - Shadcn/ui style */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  유형
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  <button
                    onClick={() => table.getColumn('filename')?.toggleSorting()}
                    className="flex items-center space-x-1 hover:text-deep-trust-blue transition-colors"
                  >
                    <span>파일명</span>
                    <ArrowUpDown className="w-4 h-4" />
                  </button>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  AI 요약
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  <button
                    onClick={() => table.getColumn('uploadDate')?.toggleSorting()}
                    className="flex items-center space-x-1 hover:text-deep-trust-blue transition-colors"
                  >
                    <span>업로드 날짜</span>
                    <ArrowUpDown className="w-4 h-4" />
                  </button>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  상태
                </th>
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {table.getRowModel().rows.map((row, index) => {
                const evidence = row.original;
                const zebraBackground = index % 2 === 0 ? 'bg-white' : 'bg-gray-50/70';

                return (
                  <tr
                    key={evidence.id}
                    className={`group transition-colors ${zebraBackground} hover:bg-accent/5`}
                  >
                    {/* Type Icon */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <EvidenceTypeIcon type={evidence.type} />
                    </td>

                    {/* Filename */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {evidence.filename}
                      </div>
                      <div className="text-xs text-gray-500">
                        {(evidence.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                      <div className="text-[11px] text-gray-400 hidden group-hover:block mt-1">
                        클릭하여 상세 · 타임라인 연결 옵션 보기
                      </div>
                    </td>

                    {/* AI Summary */}
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500 truncate max-w-xs">
                        {evidence.summary || '-'}
                      </div>
                    </td>

                    {/* Upload Date */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(evidence.uploadDate).toLocaleDateString()}
                    </td>

                    {/* Status Badge */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <EvidenceStatusBadge status={evidence.status} />
                    </td>

                    {/* Actions */}
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        className="text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
                        aria-label={`${evidence.filename} 추가 작업`}
                      >
                        <MoreVertical className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <DataTablePagination table={table} />
      </div>
    </div>
  );
}
