/**
 * Lawyer Case List Page Integration Tests
 * 003-role-based-ui Feature - US3 (T042)
 *
 * Tests for case list page filtering, view mode toggle, and bulk actions.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LawyerCasesPage from '@/app/lawyer/cases/page';

// Mock useCaseList hook
const mockSetFilters = jest.fn();
const mockResetFilters = jest.fn();
const mockSetSort = jest.fn();
const mockSetSelectedIds = jest.fn();
const mockClearSelection = jest.fn();
const mockExecuteBulkAction = jest.fn();
const mockSetPage = jest.fn();

const mockCases = [
  {
    id: '1',
    title: '이혼 소송 A',
    clientName: '김철수',
    status: 'active',
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-03-20T14:30:00Z',
    evidenceCount: 5,
    memberCount: 2,
    progress: 60,
    daysSinceUpdate: 3,
    ownerName: '박변호사',
  },
  {
    id: '2',
    title: '재산분할 B',
    clientName: '이영희',
    status: 'in_progress',
    createdAt: '2024-02-10T09:00:00Z',
    updatedAt: '2024-03-18T11:00:00Z',
    evidenceCount: 3,
    memberCount: 1,
    progress: 30,
    daysSinceUpdate: 5,
    ownerName: '김변호사',
  },
];

const defaultHookReturn = {
  cases: mockCases,
  isLoading: false,
  error: null,
  pagination: { page: 1, pageSize: 20, total: 2, totalPages: 1 },
  setPage: mockSetPage,
  filters: { search: '', status: [], clientName: '' },
  statusCounts: { active: 1, in_progress: 1, closed: 0 },
  setFilters: mockSetFilters,
  resetFilters: mockResetFilters,
  sort: { sortBy: 'updated_at', sortOrder: 'desc' as const },
  setSort: mockSetSort,
  selectedIds: [] as string[],
  setSelectedIds: mockSetSelectedIds,
  clearSelection: mockClearSelection,
  executeBulkAction: mockExecuteBulkAction,
  isBulkActionLoading: false,
};

jest.mock('@/hooks/useCaseList', () => ({
  useCaseList: () => defaultHookReturn,
}));

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

// Re-import module to apply mock
const mockUseCaseList = jest.fn(() => defaultHookReturn);
jest.mock('@/hooks/useCaseList', () => ({
  useCaseList: () => mockUseCaseList(),
}));

describe('LawyerCasesPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseCaseList.mockReturnValue(defaultHookReturn);
  });

  describe('Rendering', () => {
    it('renders page title', () => {
      render(<LawyerCasesPage />);

      expect(screen.getByText('케이스 관리')).toBeInTheDocument();
    });

    it('renders total case count', () => {
      render(<LawyerCasesPage />);

      expect(screen.getByText(/총 2건의 케이스/)).toBeInTheDocument();
    });

    it('renders view mode toggle buttons', () => {
      render(<LawyerCasesPage />);

      expect(screen.getByTitle('카드 보기')).toBeInTheDocument();
      expect(screen.getByTitle('테이블 보기')).toBeInTheDocument();
    });

    it('renders case filter component', () => {
      render(<LawyerCasesPage />);

      // CaseFilter should render search and filter controls
      expect(screen.getByPlaceholderText(/검색/i)).toBeInTheDocument();
    });
  });

  describe('Loading State', () => {
    it('shows loading spinner when loading', () => {
      mockUseCaseList.mockReturnValue({
        ...defaultHookReturn,
        isLoading: true,
        cases: [],
      });

      render(<LawyerCasesPage />);

      // Loading spinner should be visible
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    it('shows error message when error occurs', () => {
      mockUseCaseList.mockReturnValue({
        ...defaultHookReturn,
        error: '케이스 목록을 불러오는데 실패했습니다.',
        cases: [],
      });

      render(<LawyerCasesPage />);

      expect(screen.getByText('케이스 목록을 불러오는데 실패했습니다.')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    it('shows empty state when no cases', () => {
      mockUseCaseList.mockReturnValue({
        ...defaultHookReturn,
        cases: [],
        pagination: { ...defaultHookReturn.pagination, total: 0, totalPages: 0 },
      });

      render(<LawyerCasesPage />);

      expect(screen.getByText('케이스 없음')).toBeInTheDocument();
      expect(screen.getByText('검색 조건에 맞는 케이스가 없습니다.')).toBeInTheDocument();
    });
  });

  describe('View Mode Toggle', () => {
    it('defaults to table view', () => {
      render(<LawyerCasesPage />);

      // Table view button should be active (has shadow)
      const tableButton = screen.getByTitle('테이블 보기');
      expect(tableButton).toHaveClass('bg-white');
    });

    it('switches to grid view when clicking grid button', async () => {
      render(<LawyerCasesPage />);

      const gridButton = screen.getByTitle('카드 보기');
      fireEvent.click(gridButton);

      // After clicking, grid button should be active
      await waitFor(() => {
        expect(gridButton).toHaveClass('bg-white');
      });
    });

    it('renders table in table view mode', () => {
      render(<LawyerCasesPage />);

      // Should see table headers
      expect(screen.getByText('케이스명')).toBeInTheDocument();
      expect(screen.getByText('의뢰인')).toBeInTheDocument();
    });
  });

  describe('Filtering', () => {
    it('calls setFilters when search input changes', async () => {
      const user = userEvent.setup();
      render(<LawyerCasesPage />);

      const searchInput = screen.getByPlaceholderText(/검색/i);
      await user.type(searchInput, '이혼');

      // Filter should be called (debounced)
      await waitFor(() => {
        expect(mockSetFilters).toHaveBeenCalled();
      }, { timeout: 1000 });
    });

    it('calls resetFilters when reset button clicked', async () => {
      mockUseCaseList.mockReturnValue({
        ...defaultHookReturn,
        filters: { search: '테스트', status: ['active'], clientName: '' },
      });

      render(<LawyerCasesPage />);

      // Find and click reset/clear button
      const resetButton = screen.getByText(/초기화|전체/i);
      if (resetButton) {
        fireEvent.click(resetButton);
        expect(mockResetFilters).toHaveBeenCalled();
      }
    });
  });

  describe('Pagination', () => {
    it('renders pagination when multiple pages exist', () => {
      mockUseCaseList.mockReturnValue({
        ...defaultHookReturn,
        pagination: { page: 1, pageSize: 20, total: 50, totalPages: 3 },
      });

      render(<LawyerCasesPage />);

      expect(screen.getByText('이전')).toBeInTheDocument();
      expect(screen.getByText('다음')).toBeInTheDocument();
      expect(screen.getByText('1 / 3')).toBeInTheDocument();
    });

    it('disables previous button on first page', () => {
      mockUseCaseList.mockReturnValue({
        ...defaultHookReturn,
        pagination: { page: 1, pageSize: 20, total: 50, totalPages: 3 },
      });

      render(<LawyerCasesPage />);

      const prevButton = screen.getByText('이전');
      expect(prevButton).toBeDisabled();
    });

    it('disables next button on last page', () => {
      mockUseCaseList.mockReturnValue({
        ...defaultHookReturn,
        pagination: { page: 3, pageSize: 20, total: 50, totalPages: 3 },
      });

      render(<LawyerCasesPage />);

      const nextButton = screen.getByText('다음');
      expect(nextButton).toBeDisabled();
    });

    it('calls setPage when clicking next button', () => {
      mockUseCaseList.mockReturnValue({
        ...defaultHookReturn,
        pagination: { page: 1, pageSize: 20, total: 50, totalPages: 3 },
      });

      render(<LawyerCasesPage />);

      const nextButton = screen.getByText('다음');
      fireEvent.click(nextButton);

      expect(mockSetPage).toHaveBeenCalledWith(2);
    });

    it('calls setPage when clicking previous button', () => {
      mockUseCaseList.mockReturnValue({
        ...defaultHookReturn,
        pagination: { page: 2, pageSize: 20, total: 50, totalPages: 3 },
      });

      render(<LawyerCasesPage />);

      const prevButton = screen.getByText('이전');
      fireEvent.click(prevButton);

      expect(mockSetPage).toHaveBeenCalledWith(1);
    });

    it('does not render pagination for single page', () => {
      render(<LawyerCasesPage />);

      expect(screen.queryByText('이전')).not.toBeInTheDocument();
      expect(screen.queryByText('다음')).not.toBeInTheDocument();
    });
  });

  describe('Bulk Actions', () => {
    it('renders bulk action bar', () => {
      mockUseCaseList.mockReturnValue({
        ...defaultHookReturn,
        selectedIds: ['1', '2'],
      });

      render(<LawyerCasesPage />);

      // BulkActionBar should show selected count
      expect(screen.getByText(/2개 선택/i)).toBeInTheDocument();
    });

    it('hides bulk action bar when no selection', () => {
      render(<LawyerCasesPage />);

      // BulkActionBar should not show when nothing selected
      expect(screen.queryByText(/선택됨/i)).not.toBeInTheDocument();
    });
  });

  describe('Case Table Integration', () => {
    it('renders cases in table format', () => {
      render(<LawyerCasesPage />);

      expect(screen.getByText('이혼 소송 A')).toBeInTheDocument();
      expect(screen.getByText('재산분할 B')).toBeInTheDocument();
    });

    it('renders client names', () => {
      render(<LawyerCasesPage />);

      expect(screen.getByText('김철수')).toBeInTheDocument();
      expect(screen.getByText('이영희')).toBeInTheDocument();
    });

    it('renders status badges in table', () => {
      render(<LawyerCasesPage />);

      // Status badges appear in both filter and table, so check for multiple
      const activeElements = screen.getAllByText('활성');
      const inProgressElements = screen.getAllByText('검토 대기');

      expect(activeElements.length).toBeGreaterThanOrEqual(1);
      expect(inProgressElements.length).toBeGreaterThanOrEqual(1);
    });
  });
});
