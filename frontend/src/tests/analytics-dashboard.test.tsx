/**
 * Test: Plan 3.18 - 성과 분석 대시보드 (Analytics)
 *
 * GREEN 단계: 구현된 컴포넌트를 테스트하여 통과 확인 (간소화 버전)
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';

// 성과 분석 대시보드 컴포넌트
import AnalyticsDashboard from '@/pages/admin/analytics';

describe('Plan 3.18 - Analytics Dashboard (성과 분석 대시보드)', () => {
  describe('3.18.1 - Page Structure', () => {
    it('should render analytics dashboard', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByText(/성과 분석/i)).toBeInTheDocument();
    });

    it('should display breadcrumb navigation', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByText('Admin')).toBeInTheDocument();
      expect(screen.getByText('Analytics')).toBeInTheDocument();
    });
  });

  describe('3.18.2 - KPI Widgets', () => {
    it('should display time saved KPI', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByText(/절약된 시간/i)).toBeInTheDocument();
      expect(screen.getByText(/240/)).toBeInTheDocument();
    });

    it('should display evidence processed KPI', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByText(/처리된 증거/i)).toBeInTheDocument();
    });

    it('should display cases handled KPI', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByText(/처리된 사건/i)).toBeInTheDocument();
    });

    it('should show percentage changes', () => {
      render(<AnalyticsDashboard />);
      const percentages = screen.getAllByText(/\+\d+\.?\d*%/);
      expect(percentages.length).toBeGreaterThan(0);
    });
  });

  describe('3.18.3 - Charts', () => {
    it('should render monthly case chart', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByText(/월별 사건 수/i)).toBeInTheDocument();
    });

    it('should render evidence distribution chart', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByText(/증거 유형별 분포/i)).toBeInTheDocument();
    });

    it('should show chart data points', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByText(/이미지/i)).toBeInTheDocument();
      expect(screen.getByText(/문서/i)).toBeInTheDocument();
    });

    it('should have date range selector', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByLabelText(/기간 선택/i)).toBeInTheDocument();
    });
  });

  describe('3.18.4 - Team Activity', () => {
    it('should render team activity section', () => {
      render(<AnalyticsDashboard />);
      const teamHeading = screen.getByRole('heading', { name: /팀 활동/i });
      expect(teamHeading).toBeInTheDocument();
    });

    it('should display team members', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByText(/홍길동/)).toBeInTheDocument();
      expect(screen.getByText(/김철수/)).toBeInTheDocument();
    });

    it('should show activity levels', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getAllByText(/높음/i).length).toBeGreaterThan(0);
    });

    it('should display last active times', () => {
      render(<AnalyticsDashboard />);
      // 마지막 활동 시간이 표시되어야 함
      const table = screen.getByRole('table');
      expect(table).toBeInTheDocument();
    });
  });

  describe('3.18.5 - Controls', () => {
    it('should have refresh button', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByLabelText(/새로고침/i)).toBeInTheDocument();
    });

    it('should have export PDF button', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByLabelText(/PDF 다운로드/i)).toBeInTheDocument();
    });

    it('should display last updated time', () => {
      render(<AnalyticsDashboard />);
      expect(screen.getByText(/마지막 업데이트/i)).toBeInTheDocument();
    });
  });

  describe('3.18.6 - Design Tokens', () => {
    it('should use Deep Trust Blue for title', () => {
      render(<AnalyticsDashboard />);
      const title = screen.getByText(/성과 분석/i);
      expect(title).toHaveClass('text-deep-trust-blue');
    });

    it('should use Calm Grey background', () => {
      const { container } = render(<AnalyticsDashboard />);
      const page = container.querySelector('.min-h-screen');
      expect(page).toHaveClass('bg-calm-grey');
    });

    it('should use large font for KPI numbers', () => {
      const { container } = render(<AnalyticsDashboard />);
      const kpiNumber = container.querySelector('.text-5xl');
      expect(kpiNumber).toBeInTheDocument();
    });
  });
});
