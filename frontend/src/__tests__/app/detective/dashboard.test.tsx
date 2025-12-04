/**
 * Integration tests for Detective Dashboard Page
 * Task T082 - US5 Tests
 *
 * Tests for frontend/src/app/detective/dashboard/page.tsx:
 * - Page rendering with stats
 * - Active investigations display
 * - Today's schedule display
 * - Quick actions
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
  usePathname: () => '/detective/dashboard',
}));

// Mock useRole hook
jest.mock('@/hooks/useRole', () => ({
  useRole: () => ({
    user: { id: 'user-1', role: 'detective' },
    role: 'detective',
    isAuthenticated: true,
    hasAccess: () => true,
    dashboardPath: '/detective',
    roleDisplayName: '탐정',
    isLawyer: false,
    isAdmin: false,
    isClient: false,
    isDetective: true,
  }),
}));

// Mock API
const mockGetDetectiveDashboard = jest.fn();

jest.mock('@/lib/api/detective-portal', () => ({
  getDetectiveDashboard: (...args: unknown[]) => mockGetDetectiveDashboard(...args),
}));

// Import component after mocks
import DetectiveDashboardPage from '@/app/detective/dashboard/page';

// Mock data
const mockDashboardData = {
  user_name: '홍길동 탐정',
  stats: {
    active_investigations: 5,
    pending_requests: 2,
    completed_this_month: 8,
    monthly_earnings: 2450000,
  },
  active_investigations: [
    {
      id: 'inv-1',
      title: '김영희 건 현장조사',
      lawyer_name: '김변호사',
      status: 'active',
      deadline: '마감 3일',
      record_count: 12,
    },
    {
      id: 'inv-2',
      title: '박철수 건 증거수집',
      lawyer_name: '이변호사',
      status: 'pending',
      record_count: 0,
    },
  ],
  today_schedule: [
    { id: 's-1', time: '10:00', title: '현장 조사 - 강남구', type: 'field' },
    { id: 's-2', time: '14:00', title: '변호사 미팅', type: 'meeting' },
  ],
};

describe('Detective Dashboard Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();

    mockGetDetectiveDashboard.mockResolvedValue({
      data: mockDashboardData,
      error: null,
      status: 200,
    });
  });

  describe('Page Rendering', () => {
    test('should render page title', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('대시보드')).toBeInTheDocument();
      });
    });

    test('should render page description', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(
          screen.getByText('오늘의 조사 현황을 확인하세요.')
        ).toBeInTheDocument();
      });
    });
  });

  describe('Stats Display', () => {
    test('should render active investigations stat', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getAllByText('진행중 의뢰').length).toBeGreaterThan(0);
      });
    });

    test('should render pending requests stat', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('대기중 요청')).toBeInTheDocument();
      });
    });

    test('should render completed this month stat', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('이번 달 완료')).toBeInTheDocument();
      });
    });

    test('should render monthly earnings stat', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('이번 달 수익')).toBeInTheDocument();
      });
    });
  });

  describe('Active Investigations Display', () => {
    test('should render investigations section title', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(
          screen.getByRole('heading', { name: '진행중 의뢰', level: 2 })
        ).toBeInTheDocument();
      });
    });

    test('should render investigation cards', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('김영희 건 현장조사')).toBeInTheDocument();
        expect(screen.getByText('박철수 건 증거수집')).toBeInTheDocument();
      });
    });

    test('should show investigation status badges', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('진행중')).toBeInTheDocument();
        expect(screen.getByText('대기중')).toBeInTheDocument();
      });
    });
  });

  describe("Today's Schedule Display", () => {
    test('should render schedule section title', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('오늘 일정')).toBeInTheDocument();
      });
    });

    test('should render schedule items with time', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('10:00')).toBeInTheDocument();
        expect(screen.getByText('14:00')).toBeInTheDocument();
      });
    });

    test('should render schedule item titles', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('현장 조사 - 강남구')).toBeInTheDocument();
        expect(screen.getByText('변호사 미팅')).toBeInTheDocument();
      });
    });
  });

  describe('Quick Actions', () => {
    test('should render cases list quick action', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('의뢰 목록')).toBeInTheDocument();
      });
    });

    test('should render earnings quick action', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('수익 현황')).toBeInTheDocument();
      });
    });

    test('should render messages quick action', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        expect(screen.getByText('메시지')).toBeInTheDocument();
      });
    });
  });

  describe('Navigation Links', () => {
    test('should have link to all cases', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        const links = document.querySelectorAll('a[href="/detective/cases"]');
        expect(links.length).toBeGreaterThan(0);
      });
    });

    test('should have link to calendar', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        const link = document.querySelector('a[href="/detective/calendar"]');
        expect(link).toBeInTheDocument();
      });
    });

    test('should have link to earnings page', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        const link = document.querySelector('a[href="/detective/earnings"]');
        expect(link).toBeInTheDocument();
      });
    });

    test('should have link to messages page', async () => {
      render(<DetectiveDashboardPage />);

      await waitFor(() => {
        const link = document.querySelector('a[href="/detective/messages"]');
        expect(link).toBeInTheDocument();
      });
    });
  });
});
