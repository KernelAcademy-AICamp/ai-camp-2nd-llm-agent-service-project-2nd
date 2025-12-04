/**
 * Integration tests for ProgressTracker Component
 * Task T059 - US4 Tests
 *
 * Tests for frontend/src/components/client/ProgressTracker.tsx:
 * - Rendering progress steps with correct status
 * - Progress bar calculation
 * - Empty state handling
 * - Orientation variants
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import ProgressTracker, { ProgressBar } from '@/components/client/ProgressTracker';
import type { ProgressStep } from '@/types/client-portal';

describe('ProgressTracker Component', () => {
  const mockSteps: ProgressStep[] = [
    { step: 1, title: '상담 접수', status: 'completed', date: '2024-01-10' },
    { step: 2, title: '증거 수집', status: 'completed', date: '2024-01-15' },
    { step: 3, title: '서류 작성', status: 'current' },
    { step: 4, title: '법원 제출', status: 'pending' },
    { step: 5, title: '재판 진행', status: 'pending' },
  ];

  describe('Basic Rendering', () => {
    test('should render all step titles', () => {
      render(<ProgressTracker steps={mockSteps} />);

      expect(screen.getByText('상담 접수')).toBeInTheDocument();
      expect(screen.getByText('증거 수집')).toBeInTheDocument();
      expect(screen.getByText('서류 작성')).toBeInTheDocument();
      expect(screen.getByText('법원 제출')).toBeInTheDocument();
      expect(screen.getByText('재판 진행')).toBeInTheDocument();
    });

    test('should render progress percentage', () => {
      render(<ProgressTracker steps={mockSteps} />);

      // 2 completed + 0.5 current = 2.5 / 5 = 50%
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    test('should render overall progress label', () => {
      render(<ProgressTracker steps={mockSteps} />);

      expect(screen.getByText('전체 진행률')).toBeInTheDocument();
    });

    test('should render dates for completed steps', () => {
      render(<ProgressTracker steps={mockSteps} />);

      expect(screen.getByText('2024-01-10')).toBeInTheDocument();
      expect(screen.getByText('2024-01-15')).toBeInTheDocument();
    });
  });

  describe('Step Status Visualization', () => {
    test('should show checkmark for completed steps', () => {
      render(<ProgressTracker steps={mockSteps} />);

      // Completed steps should have checkmark SVG paths
      const svgPaths = document.querySelectorAll('path[d="M5 13l4 4L19 7"]');
      expect(svgPaths.length).toBe(2); // 2 completed steps
    });

    test('should show step number for current step', () => {
      render(<ProgressTracker steps={mockSteps} />);

      // Step 3 is current, should show "3"
      expect(screen.getByText('3')).toBeInTheDocument();
    });

    test('should show step numbers for pending steps', () => {
      render(<ProgressTracker steps={mockSteps} />);

      // Steps 4 and 5 are pending
      expect(screen.getByText('4')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    test('should show empty message when no steps', () => {
      render(<ProgressTracker steps={[]} />);

      expect(screen.getByText('진행 단계 정보가 없습니다')).toBeInTheDocument();
    });

    test('should not show progress bar when no steps', () => {
      render(<ProgressTracker steps={[]} />);

      expect(screen.queryByText('전체 진행률')).not.toBeInTheDocument();
    });
  });

  describe('Progress Calculation', () => {
    test('should calculate 0% when all steps pending', () => {
      const allPending: ProgressStep[] = [
        { step: 1, title: 'Step 1', status: 'pending' },
        { step: 2, title: 'Step 2', status: 'pending' },
      ];
      render(<ProgressTracker steps={allPending} />);

      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    test('should calculate 100% when all steps completed', () => {
      const allCompleted: ProgressStep[] = [
        { step: 1, title: 'Step 1', status: 'completed' },
        { step: 2, title: 'Step 2', status: 'completed' },
      ];
      render(<ProgressTracker steps={allCompleted} />);

      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    test('should include 50% of current step in calculation', () => {
      const withCurrent: ProgressStep[] = [
        { step: 1, title: 'Step 1', status: 'current' },
        { step: 2, title: 'Step 2', status: 'pending' },
      ];
      render(<ProgressTracker steps={withCurrent} />);

      // 0 completed + 0.5 current = 0.5 / 2 = 25%
      expect(screen.getByText('25%')).toBeInTheDocument();
    });
  });

  describe('Orientation', () => {
    test('should render vertical layout by default', () => {
      render(<ProgressTracker steps={mockSteps} />);

      // In vertical mode, container should have flex-col class
      const container = document.querySelector('.flex.flex-col');
      expect(container).toBeInTheDocument();
    });

    test('should render horizontal layout when specified', () => {
      render(<ProgressTracker steps={mockSteps} orientation="horizontal" />);

      // In horizontal mode, container should have flex and items-start
      const container = document.querySelector('.flex.items-start');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    test('should apply custom className', () => {
      const { container } = render(
        <ProgressTracker steps={mockSteps} className="custom-class" />
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });
  });
});

describe('ProgressBar Component', () => {
  describe('Basic Rendering', () => {
    test('should render percentage label', () => {
      render(<ProgressBar percent={75} />);

      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    test('should render progress label', () => {
      render(<ProgressBar percent={50} />);

      expect(screen.getByText('진행률')).toBeInTheDocument();
    });

    test('should render 0% correctly', () => {
      render(<ProgressBar percent={0} />);

      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    test('should render 100% correctly', () => {
      render(<ProgressBar percent={100} />);

      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });

  describe('Value Clamping', () => {
    test('should clamp value above 100 to 100', () => {
      render(<ProgressBar percent={150} />);

      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    test('should clamp negative value to 0', () => {
      render(<ProgressBar percent={-10} />);

      expect(screen.getByText('0%')).toBeInTheDocument();
    });
  });

  describe('Label Visibility', () => {
    test('should hide label when showLabel is false', () => {
      render(<ProgressBar percent={50} showLabel={false} />);

      expect(screen.queryByText('진행률')).not.toBeInTheDocument();
      expect(screen.queryByText('50%')).not.toBeInTheDocument();
    });

    test('should show label by default', () => {
      render(<ProgressBar percent={50} />);

      expect(screen.getByText('진행률')).toBeInTheDocument();
    });
  });

  describe('Custom Styling', () => {
    test('should apply custom className', () => {
      const { container } = render(
        <ProgressBar percent={50} className="custom-progress" />
      );

      expect(container.firstChild).toHaveClass('custom-progress');
    });
  });
});
