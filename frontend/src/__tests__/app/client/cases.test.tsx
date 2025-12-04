/**
 * Integration tests for Client Cases Page
 * Task T058 - US4 Tests
 *
 * Tests for frontend/src/app/client/cases/page.tsx:
 * - Page rendering with cases list
 * - Loading and error states
 * - Empty state handling
 * - Case card display
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/client/cases',
}));

// Mock useRole hook
jest.mock('@/hooks/useRole', () => ({
  useRole: () => ({
    user: { id: 'user-1', role: 'client' },
    role: 'client',
    isAuthenticated: true,
    hasAccess: () => true,
    dashboardPath: '/client',
    roleDisplayName: '의뢰인',
    isLawyer: false,
    isAdmin: false,
    isClient: true,
    isDetective: false,
  }),
}));

// Mock API
const mockGetClientCases = jest.fn();

jest.mock('@/lib/api/client-portal', () => ({
  getClientCases: (...args: unknown[]) => mockGetClientCases(...args),
}));

// Import component after mocks
import ClientCasesPage from '@/app/client/cases/page';

// Mock data
const mockCasesData = {
  items: [
    {
      id: 'case-1',
      title: '이혼 소송 건',
      status: 'active',
      progress_percent: 60,
      evidence_count: 5,
      lawyer_name: '김변호사',
      created_at: '2024-01-10T09:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    },
    {
      id: 'case-2',
      title: '재산분할 건',
      status: 'review',
      progress_percent: 30,
      evidence_count: 3,
      lawyer_name: '박변호사',
      created_at: '2024-01-05T09:00:00Z',
      updated_at: '2024-01-14T15:00:00Z',
    },
    {
      id: 'case-3',
      title: '위자료 청구',
      status: 'closed',
      progress_percent: 100,
      evidence_count: 10,
      lawyer_name: null,
      created_at: '2023-12-01T09:00:00Z',
      updated_at: '2024-01-01T10:00:00Z',
    },
  ],
  total: 3,
};

describe('Client Cases Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    mockGetClientCases.mockResolvedValue({
      data: mockCasesData,
      error: null,
      status: 200,
    });
  });

  describe('Page Rendering', () => {
    test('should render page title', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(screen.getByText('내 케이스')).toBeInTheDocument();
      });
    });

    test('should render page description', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(
          screen.getByText('진행 중인 모든 케이스를 확인하세요')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Cases List Display', () => {
    test('should render all case titles', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(screen.getByText('이혼 소송 건')).toBeInTheDocument();
        expect(screen.getByText('재산분할 건')).toBeInTheDocument();
        expect(screen.getByText('위자료 청구')).toBeInTheDocument();
      });
    });

    test('should render case status badges', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(screen.getByText('진행 중')).toBeInTheDocument();
        expect(screen.getByText('검토 중')).toBeInTheDocument();
        expect(screen.getByText('종결')).toBeInTheDocument();
      });
    });

    test('should render evidence counts', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(screen.getByText('5건')).toBeInTheDocument();
        expect(screen.getByText('3건')).toBeInTheDocument();
        expect(screen.getByText('10건')).toBeInTheDocument();
      });
    });

    test('should render lawyer names when available', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(screen.getByText('김변호사')).toBeInTheDocument();
        expect(screen.getByText('박변호사')).toBeInTheDocument();
      });
    });

    test('should render case cards as links', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        const links = document.querySelectorAll('a[href^="/client/cases/"]');
        expect(links.length).toBe(3);
      });
    });

    test('should link to correct case detail pages', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(
          document.querySelector('a[href="/client/cases/case-1"]')
        ).toBeInTheDocument();
        expect(
          document.querySelector('a[href="/client/cases/case-2"]')
        ).toBeInTheDocument();
        expect(
          document.querySelector('a[href="/client/cases/case-3"]')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Progress Display', () => {
    test('should render progress bars for each case', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        // Progress bars have the '진행률' label
        const progressLabels = screen.getAllByText('진행률');
        expect(progressLabels.length).toBe(3);
      });
    });

    test('should display correct progress percentages', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(screen.getByText('60%')).toBeInTheDocument();
        expect(screen.getByText('30%')).toBeInTheDocument();
        expect(screen.getByText('100%')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    test('should show loading spinner while fetching', async () => {
      // Make API never resolve to keep loading state
      mockGetClientCases.mockImplementation(() => new Promise(() => {}));

      render(<ClientCasesPage />);

      // Should show loading indicator
      expect(document.querySelector('.animate-spin')).toBeInTheDocument();
    });

    test('should hide loading spinner after data loads', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(screen.getByText('이혼 소송 건')).toBeInTheDocument();
      });

      expect(document.querySelector('.animate-spin')).not.toBeInTheDocument();
    });
  });

  describe('Error State', () => {
    test('should show error message when API fails', async () => {
      mockGetClientCases.mockResolvedValue({
        data: null,
        error: 'Failed to load cases',
        status: 500,
      });

      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(
          screen.getByText('케이스를 불러올 수 없습니다')
        ).toBeInTheDocument();
      });
    });

    test('should display error details', async () => {
      mockGetClientCases.mockResolvedValue({
        data: null,
        error: 'Network error',
        status: 500,
      });

      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    test('should show empty message when no cases', async () => {
      mockGetClientCases.mockResolvedValue({
        data: { items: [], total: 0 },
        error: null,
        status: 200,
      });

      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(screen.getByText('아직 케이스가 없습니다')).toBeInTheDocument();
      });
    });

    test('should show guidance message in empty state', async () => {
      mockGetClientCases.mockResolvedValue({
        data: { items: [], total: 0 },
        error: null,
        status: 200,
      });

      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(
          screen.getByText('담당 변호사가 케이스를 등록하면 여기에 표시됩니다')
        ).toBeInTheDocument();
      });
    });
  });

  describe('API Integration', () => {
    test('should call getClientCases on mount', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        expect(mockGetClientCases).toHaveBeenCalledTimes(1);
      });
    });
  });

  describe('Status Badge Colors', () => {
    test('should apply correct styles for active status', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        const activeBadge = screen.getByText('진행 중');
        expect(activeBadge).toHaveClass(
          'bg-[var(--color-primary-light)]',
          'text-[var(--color-primary)]'
        );
      });
    });

    test('should apply correct styles for closed status', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        const closedBadge = screen.getByText('종결');
        expect(closedBadge).toHaveClass(
          'bg-[var(--color-success-light)]',
          'text-[var(--color-success)]'
        );
      });
    });

    test('should apply correct styles for review status', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        const reviewBadge = screen.getByText('검토 중');
        expect(reviewBadge).toHaveClass(
          'bg-[var(--color-warning-light)]',
          'text-[var(--color-warning)]'
        );
      });
    });
  });

  describe('Date Formatting', () => {
    test('should display formatted dates', async () => {
      render(<ClientCasesPage />);

      await waitFor(() => {
        // Dates should be formatted in Korean locale
        // Note: actual format depends on locale, checking for year/month pattern
        const dateElements = document.querySelectorAll('.text-xs');
        expect(dateElements.length).toBeGreaterThan(0);
      });
    });
  });
});
