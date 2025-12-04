'use client';

/**
 * CaseFilter Component
 * 003-role-based-ui Feature - US3
 *
 * Filter controls for case list.
 */

import { useState } from 'react';

interface FilterState {
  search: string;
  status: string[];
  clientName: string;
}

interface StatusCount {
  [key: string]: number;
}

interface CaseFilterProps {
  filters: FilterState;
  statusCounts?: StatusCount;
  onFilterChange: (filters: FilterState) => void;
  onReset: () => void;
}

const statusOptions = [
  { value: 'active', label: '활성', color: 'bg-blue-100 text-blue-800' },
  { value: 'open', label: '진행 중', color: 'bg-green-100 text-green-800' },
  { value: 'in_progress', label: '검토 대기', color: 'bg-yellow-100 text-yellow-800' },
  { value: 'closed', label: '종료', color: 'bg-gray-100 text-gray-800' },
];

export function CaseFilter({
  filters,
  statusCounts = {},
  onFilterChange,
  onReset,
}: CaseFilterProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filters, search: e.target.value });
  };

  const handleStatusToggle = (status: string) => {
    const newStatus = filters.status.includes(status)
      ? filters.status.filter((s) => s !== status)
      : [...filters.status, status];
    onFilterChange({ ...filters, status: newStatus });
  };

  const handleClientNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({ ...filters, clientName: e.target.value });
  };

  const hasActiveFilters = filters.search || filters.status.length > 0 || filters.clientName;

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-4">
      {/* Search Bar */}
      <div className="relative">
        <input
          type="text"
          placeholder="케이스 검색..."
          value={filters.search}
          onChange={handleSearchChange}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
        />
        <svg
          className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>

      {/* Status Chips */}
      <div className="flex flex-wrap gap-2">
        {statusOptions.map((option) => {
          const isSelected = filters.status.includes(option.value);
          const count = statusCounts[option.value] || 0;
          return (
            <button
              key={option.value}
              type="button"
              onClick={() => handleStatusToggle(option.value)}
              className={`
                px-3 py-1.5 rounded-full text-sm font-medium transition-all
                ${isSelected
                  ? 'bg-[var(--color-primary)] text-white'
                  : `${option.color} hover:opacity-80`
                }
              `}
            >
              {option.label}
              {count > 0 && (
                <span className={`ml-1.5 px-1.5 py-0.5 rounded-full text-xs ${isSelected ? 'bg-white/20' : 'bg-black/10'}`}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Expanded Filters */}
      {isExpanded && (
        <div className="pt-4 border-t border-gray-200 space-y-4">
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1">
              의뢰인 이름
            </label>
            <input
              type="text"
              placeholder="의뢰인 이름으로 검색"
              value={filters.clientName}
              onChange={handleClientNameChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
            />
          </div>
        </div>
      )}

      {/* Filter Actions */}
      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm text-[var(--color-primary)] hover:underline"
        >
          {isExpanded ? '간단히 보기' : '상세 필터'}
        </button>

        {hasActiveFilters && (
          <button
            type="button"
            onClick={onReset}
            className="text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-error)]"
          >
            필터 초기화
          </button>
        )}
      </div>
    </div>
  );
}

export default CaseFilter;
