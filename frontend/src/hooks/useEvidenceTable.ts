/**
 * Custom hook for Evidence Table logic
 * Separates data management from UI presentation
 */

import { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getPaginationRowModel,
  getFilteredRowModel,
  ColumnDef,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { Evidence } from '@/types/evidence';

export function useEvidenceTable(data: Evidence[]) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [pagination, setPagination] = useState({
    pageIndex: 0,
    pageSize: 10,
  });

  // Column definitions
  const columns = useMemo<ColumnDef<Evidence>[]>(
    () => [
      {
        accessorKey: 'type',
        header: '유형',
        cell: ({ row }) => row.original.type,
        filterFn: 'equals',
      },
      {
        accessorKey: 'filename',
        header: '파일명',
        cell: ({ row }) => row.original.filename,
      },
      {
        accessorKey: 'summary',
        header: 'AI 요약',
        cell: ({ row }) => row.original.summary || '-',
      },
      {
        accessorKey: 'uploadDate',
        header: '업로드 날짜',
        cell: ({ row }) => new Date(row.original.uploadDate).toLocaleDateString(),
        sortingFn: 'datetime',
      },
      {
        accessorKey: 'status',
        header: '상태',
        cell: ({ row }) => row.original.status,
      },
      {
        id: 'actions',
        header: '',
        cell: ({ row }) => row.original.id,
      },
    ],
    []
  );

  const table = useReactTable({
    data,
    columns,
    state: {
      sorting,
      columnFilters,
      pagination,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onPaginationChange: setPagination,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  // Custom filter helpers
  const setTypeFilter = (value: string) => {
    table.getColumn('type')?.setFilterValue(value === 'all' ? undefined : value);
  };

  const setDateFilter = (value: string) => {
    if (value === 'all') {
      table.getColumn('uploadDate')?.setFilterValue(undefined);
    } else {
      // Custom date filtering logic
      const now = new Date();
      table.getColumn('uploadDate')?.setFilterValue((originalValue: string) => {
        const itemDate = new Date(originalValue);
        const daysDiff = Math.floor((now.getTime() - itemDate.getTime()) / (1000 * 60 * 60 * 24));

        if (value === 'today') return daysDiff === 0;
        if (value === 'week') return daysDiff <= 7;
        if (value === 'month') return daysDiff <= 30;
        return true;
      });
    }
  };

  return {
    table,
    setTypeFilter,
    setDateFilter,
    pagination,
  };
}
