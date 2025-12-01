/**
 * Test for SolutionSection Component
 * Plan 3.19.1 - Solution (3가지 핵심 기능)
 *
 * Requirements:
 * - Section title: "Legal Evidence Hub가 해결합니다"
 * - 3-column layout with core features:
 *   1. 자동 증거 분석: 이미지/음성/PDF를 AI가 자동 분류 및 요약
 *   2. 스마트 타임라인: 시간순 증거 정리, 유책사유 자동 태깅
 *   3. 초안 자동 생성: RAG 기반 사실 인용, 답변서 초안 1분 생성
 * - Each feature: icon, short description, screenshot
 * - Responsive layout
 */

import { render, screen } from '@testing-library/react';
import SolutionSection from '../SolutionSection';

describe('SolutionSection Component', () => {
  describe('Section Title', () => {
    it('should render the section title', () => {
      render(<SolutionSection />);

      const title = screen.getByRole('heading', { name: /legal evidence hub가 해결합니다/i });
      expect(title).toBeInTheDocument();
    });

    it('should style title with Deep Trust Blue', () => {
      render(<SolutionSection />);

      const title = screen.getByRole('heading', { name: /legal evidence hub가 해결합니다/i });
      expect(title).toHaveClass('text-secondary');
    });

    it('should use appropriate heading level (h2)', () => {
      render(<SolutionSection />);

      const title = screen.getByRole('heading', { name: /legal evidence hub가 해결합니다/i });
      expect(title.tagName).toBe('H2');
    });
  });

  describe('Feature 1: Auto Evidence Analysis', () => {
    it('should render feature heading', () => {
      render(<SolutionSection />);

      const heading = screen.getByRole('heading', { name: /자동 증거 분석/i });
      expect(heading).toBeInTheDocument();
    });

    it('should render feature description', () => {
      render(<SolutionSection />);

      expect(screen.getByText(/이미지\/음성\/PDF를 AI가 자동 분류 및 요약/i)).toBeInTheDocument();
    });

    it('should use h3 heading level for feature', () => {
      render(<SolutionSection />);

      const heading = screen.getByRole('heading', { name: /자동 증거 분석/i });
      expect(heading.tagName).toBe('H3');
    });
  });

  describe('Feature 2: Smart Timeline', () => {
    it('should render feature heading', () => {
      render(<SolutionSection />);

      const heading = screen.getByRole('heading', { name: /스마트 타임라인/i });
      expect(heading).toBeInTheDocument();
    });

    it('should render feature description', () => {
      render(<SolutionSection />);

      expect(screen.getByText(/시간순 증거 정리, 유책사유 자동 태깅/i)).toBeInTheDocument();
    });

    it('should use h3 heading level for feature', () => {
      render(<SolutionSection />);

      const heading = screen.getByRole('heading', { name: /스마트 타임라인/i });
      expect(heading.tagName).toBe('H3');
    });
  });

  describe('Feature 3: Auto Draft Generation', () => {
    it('should render feature heading', () => {
      render(<SolutionSection />);

      const heading = screen.getByRole('heading', { name: /초안 자동 생성/i });
      expect(heading).toBeInTheDocument();
    });

    it('should render feature description', () => {
      render(<SolutionSection />);

      expect(screen.getByText(/RAG 기반 사실 인용, 답변서 초안 1분 생성/i)).toBeInTheDocument();
    });

    it('should use h3 heading level for feature', () => {
      render(<SolutionSection />);

      const heading = screen.getByRole('heading', { name: /초안 자동 생성/i });
      expect(heading.tagName).toBe('H3');
    });
  });

  describe('Icons', () => {
    it('should render icons for each feature', () => {
      const { container } = render(<SolutionSection />);

      // Should have 3 icons (one per feature)
      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThanOrEqual(3);
    });

    it('should use consistent icon sizes', () => {
      const { container } = render(<SolutionSection />);

      const icons = container.querySelectorAll('svg');
      // At least the first 3 icons should have consistent sizing
      for (let i = 0; i < Math.min(3, icons.length); i++) {
        expect(icons[i]).toHaveClass('w-12');
        expect(icons[i]).toHaveClass('h-12');
      }
    });

    it('should style icons with accent color', () => {
      const { container } = render(<SolutionSection />);

      const icons = container.querySelectorAll('svg');
      // At least the first 3 icons should use accent color
      for (let i = 0; i < Math.min(3, icons.length); i++) {
        expect(icons[i]).toHaveClass('text-accent');
      }
    });
  });

  describe('Layout Structure', () => {
    it('should render as a semantic section element', () => {
      const { container } = render(<SolutionSection />);

      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
    });

    it('should have grid layout for features', () => {
      const { container } = render(<SolutionSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
    });

    it('should use 3-column layout on desktop', () => {
      const { container } = render(<SolutionSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('should use responsive grid columns', () => {
      const { container } = render(<SolutionSection />);

      const grid = container.querySelector('.grid');
      // 1 column on mobile, 3 on desktop
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('should have appropriate spacing between features', () => {
      const { container } = render(<SolutionSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('gap-8');
    });

    it('should have max-width container', () => {
      const { container } = render(<SolutionSection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toBeInTheDocument();
    });

    it('should center content horizontally', () => {
      const { container } = render(<SolutionSection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toHaveClass('mx-auto');
    });
  });

  describe('Feature Cards', () => {
    it('should render feature cards with card styling', () => {
      const { container } = render(<SolutionSection />);

      const cards = container.querySelectorAll('.bg-white');
      // Should have at least 3 white background cards
      expect(cards.length).toBeGreaterThanOrEqual(3);
    });

    it('should have rounded corners on cards', () => {
      const { container } = render(<SolutionSection />);

      const section = container.querySelector('section');
      const roundedCards = section?.querySelectorAll('.rounded-xl');
      expect(roundedCards?.length).toBeGreaterThanOrEqual(3);
    });

    it('should have shadow on cards', () => {
      const { container } = render(<SolutionSection />);

      const section = container.querySelector('section');
      const shadowCards = section?.querySelectorAll('.shadow-lg');
      expect(shadowCards?.length).toBeGreaterThanOrEqual(3);
    });

    it('should have padding on cards', () => {
      const { container } = render(<SolutionSection />);

      const section = container.querySelector('section');
      const paddedCards = section?.querySelectorAll('.p-8');
      expect(paddedCards?.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Design System Compliance', () => {
    it('should follow 8pt grid spacing', () => {
      const { container } = render(<SolutionSection />);

      const section = container.querySelector('section');
      // Padding should be multiples of 8px
      expect(section).toHaveClass('py-20');
      expect(section).toHaveClass('px-6');
    });

    it('should use calm background color', () => {
      const { container } = render(<SolutionSection />);

      const section = container.querySelector('section');
      expect(section).toHaveClass('bg-neutral-50');
    });

    it('should use appropriate text colors', () => {
      render(<SolutionSection />);

      // Feature descriptions should be readable gray
      const descriptions = [
        screen.getByText(/이미지\/음성\/PDF를 AI가 자동 분류 및 요약/i),
        screen.getByText(/시간순 증거 정리, 유책사유 자동 태깅/i),
        screen.getByText(/RAG 기반 사실 인용, 답변서 초안 1분 생성/i),
      ];

      descriptions.forEach((desc) => {
        expect(desc).toHaveClass('text-neutral-600');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have aria-label for section', () => {
      const { container } = render(<SolutionSection />);

      const section = container.querySelector('section');
      expect(section).toHaveAttribute('aria-label', '솔루션 핵심 기능');
    });

    it('should have proper heading hierarchy', () => {
      render(<SolutionSection />);

      const mainHeading = screen.getByRole('heading', { name: /legal evidence hub가 해결합니다/i });
      expect(mainHeading.tagName).toBe('H2');

      const featureHeadings = screen.getAllByRole('heading', { level: 3 });
      expect(featureHeadings.length).toBe(3);
    });

    it('should have aria-labels for icons', () => {
      const { container } = render(<SolutionSection />);

      const icons = container.querySelectorAll('svg');
      // At least the first 3 feature icons should have aria-labels
      for (let i = 0; i < Math.min(3, icons.length); i++) {
        expect(icons[i]).toHaveAttribute('aria-label');
      }
    });
  });

  describe('Responsive Behavior', () => {
    it('should stack features vertically on mobile', () => {
      const { container } = render(<SolutionSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
    });

    it('should display 3 columns on desktop', () => {
      const { container } = render(<SolutionSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });
  });

  describe('Visual Presentation', () => {
    it('should center-align content in feature cards', () => {
      const { container } = render(<SolutionSection />);

      const section = container.querySelector('section');
      const centeredCards = section?.querySelectorAll('.text-center');
      expect(centeredCards?.length).toBeGreaterThanOrEqual(3);
    });

    it('should have consistent spacing within cards', () => {
      const { container } = render(<SolutionSection />);

      const section = container.querySelector('section');
      const spacedCards = section?.querySelectorAll('.space-y-4');
      expect(spacedCards?.length).toBeGreaterThanOrEqual(3);
    });
  });
});
