/**
 * Integration tests for Lawyer Dashboard Page
 * Task T027 - TDD RED Phase
 *
 * Tests for frontend/src/app/lawyer/dashboard/page.tsx:
 * - Page rendering with stats cards
 * - Recent cases display
 * - Upcoming events display
 * - Loading and error states
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';

// Mock next/navigation
const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/lawyer/dashboard',
}));

// Mock useRole hook
jest.mock('@/hooks/useRole', () => ({
  useRole: () => ({
    user: { id: 'user-1', role: 'lawyer' },
    role: 'lawyer',
    isAuthenticated: true,
    hasAccess: () => true,
    dashboardPath: '/lawyer/dashboard',
    roleDisplayName: '변호사',
    isLawyer: true,
    isAdmin: false,
    isClient: false,
    isDetective: false,
  }),
}));

// Mock dashboard API - must inline data for Jest hoisting
const mockGetDashboard = jest.fn();
const mockGetAnalytics = jest.fn();

jest.mock('@/lib/api/lawyer', () => ({
  getLawyerDashboard: (...args: unknown[]) => mockGetDashboard(...args),
  getLawyerAnalytics: (...args: unknown[]) => mockGetAnalytics(...args),
}));

// Import component after mocks
import LawyerDashboardPage from '@/app/lawyer/dashboard/page';

// Mock data defined after imports
const mockDashboardData = {
  stats: {
    total_cases: 10,
    active_cases: 5,
    pending_review: 3,
    completed_this_month: 2,
    stats_cards: [
      { label: '전체 케이스', value: 10, change: 2, trend: 'up' },
      { label: '진행 중', value: 5, change: 0, trend: 'stable' },
      { label: '검토 대기', value: 3, change: 1, trend: 'up' },
      { label: '이번 달 완료', value: 2, change: 2, trend: 'up' },
    ],
  },
  recent_cases: [
    {
      id: 'case-1',
      title: '이혼 소송 건',
      status: 'active',
      client_name: '김철수',
      updated_at: '2024-01-15T10:00:00Z',
      evidence_count: 5,
      progress: 60,
    },
    {
      id: 'case-2',
      title: '재산분할 건',
      status: 'open',
      client_name: '박영희',
      updated_at: '2024-01-14T15:00:00Z',
      evidence_count: 3,
      progress: 30,
    },
  ],
  upcoming_events: [
    {
      id: 'event-1',
      title: '재판 출석',
      event_type: 'court',
      start_time: '2024-01-20T09:00:00Z',
      case_id: 'case-1',
      case_title: '이혼 소송 건',
    },
  ],
};

describe('Lawyer Dashboard Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    // Set up default mock implementations
    mockGetDashboard.mockResolvedValue({
      data: mockDashboardData,
      error: null,
      status: 200,
    });
    mockGetAnalytics.mockResolvedValue({
      data: {
        status_distribution: [],
        monthly_stats: [],
        total_evidence: 0,
        avg_case_duration_days: 0,
      },
      error: null,
      status: 200,
    });
  });

  describe('Page Rendering', () => {
    test('should render dashboard title', async () => {
      render(<LawyerDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText(/대시보드|Dashboard/i)).toBeInTheDocument();
      });
    });

    test('should render welcome message with lawyer name', async () => {
      render(<LawyerDashboardPage />);

      await waitFor(() => {
        // Should show some form of welcome or greeting
        expect(
          screen.queryByText(/환영|안녕하세요|Welcome/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Stats Cards Display', () => {
    test('should render 4 stats cards', async () => {
      render(<LawyerDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('전체 케이스')).toBeInTheDocument();
        expect(screen.getByText('진행 중')).toBeInTheDocument();
        expect(screen.getByText('검토 대기')).toBeInTheDocument();
        expect(screen.getByText('이번 달 완료')).toBeInTheDocument();
      });
    });

    test('should display correct stats values', async () => {
      render(<LawyerDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('10')).toBeInTheDocument(); // total_cases
        expect(screen.getByText('5')).toBeInTheDocument(); // active_cases
        expect(screen.getByText('3')).toBeInTheDocument(); // pending_review
        expect(screen.getByText('2')).toBeInTheDocument(); // completed_this_month
      });
    });
  });

  describe('Recent Cases Section', () => {
    test('should render recent cases section', async () => {
      render(<LawyerDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText(/최근 케이스|Recent Cases/i)).toBeInTheDocument();
      });
    });

    test('should display case titles', async () => {
      render(<LawyerDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('이혼 소송 건')).toBeInTheDocument();
        expect(screen.getByText('재산분할 건')).toBeInTheDocument();
      });
    });

    test('should display client names', async () => {
      render(<LawyerDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('김철수')).toBeInTheDocument();
        expect(screen.getByText('박영희')).toBeInTheDocument();
      });
    });
  });

  describe('Upcoming Events Section', () => {
    test('should render upcoming events section', async () => {
      render(<LawyerDashboardPage />);

      await waitFor(() => {
        expect(
          screen.getByText(/예정된 일정|Upcoming|일정/i)
        ).toBeInTheDocument();
      });
    });

    test('should display event titles', async () => {
      render(<LawyerDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('재판 출석')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    test('should show loading spinner while fetching data', () => {
      // Make the mock return a never-resolving promise to keep loading state
      mockGetDashboard.mockImplementation(() => new Promise(() => {}));

      render(<LawyerDashboardPage />);

      // Should show loading indicator initially
      expect(
        screen.queryByText(/로딩|Loading/i) ||
          screen.queryByRole('progressbar') ||
          document.querySelector('.animate-pulse')
      ).toBeTruthy();
    });
  });

  describe('Error State', () => {
    test('should show error message when API fails', async () => {
      // Mock API error
      mockGetDashboard.mockRejectedValueOnce(new Error('Failed to load dashboard'));

      render(<LawyerDashboardPage />);

      await waitFor(() => {
        expect(
          screen.queryByText(/오류|Error|실패|Failed/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    test('should have link to cases page', async () => {
      render(<LawyerDashboardPage />);

      await waitFor(() => {
        // Find link by href attribute pointing to cases page
        const casesLink = screen.queryByRole('link', { name: /전체보기|케이스|Cases/i });
        expect(casesLink).toBeTruthy();
      });
    });

    test('should navigate to case detail when clicking a case', async () => {
      render(<LawyerDashboardPage />);

      await waitFor(() => {
        const caseItem = screen.getByText('이혼 소송 건');
        caseItem.click();
        expect(mockPush).toHaveBeenCalledWith(
          expect.stringContaining('/lawyer/cases/')
        );
      });
    });
  });
});
