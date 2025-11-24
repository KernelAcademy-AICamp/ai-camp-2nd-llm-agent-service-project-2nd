/**
 * Test for ProblemStatementSection Component
 * Plan 3.19.1 - Problem Statement (이런 고민 있으셨나요?)
 *
 * Requirements:
 * - Section title: "이런 고민 있으셨나요?"
 * - 3-4 pain points with icons and text
 * - Pain points:
 *   - 📂 "수백 개 카톡 대화, 일일이 읽기 힘드시죠?"
 *   - ⏰ "증거 정리에만 며칠씩 걸리시나요?"
 *   - 📝 "초안 작성할 때마다 반복 작업에 지치셨나요?"
 *   - 🔍 "중요한 증거를 놓칠까 불안하신가요?"
 * - Icons should be visually distinct
 * - Clean, empathetic messaging
 */

import { render, screen } from '@testing-library/react';
import ProblemStatementSection from '../ProblemStatementSection';

describe('ProblemStatementSection Component', () => {
  describe('Section Title', () => {
    it('should render the section title', () => {
      render(<ProblemStatementSection />);

      const title = screen.getByRole('heading', { name: /이런 고민 있으셨나요\?/i });
      expect(title).toBeInTheDocument();
    });

    it('should style title with Deep Trust Blue', () => {
      render(<ProblemStatementSection />);

      const title = screen.getByRole('heading', { name: /이런 고민 있으셨나요\?/i });
      expect(title).toHaveClass('text-deep-trust-blue');
    });

    it('should use appropriate heading level (h2)', () => {
      render(<ProblemStatementSection />);

      const title = screen.getByRole('heading', { name: /이런 고민 있으셨나요\?/i });
      expect(title.tagName).toBe('H2');
    });
  });

  describe('Pain Points Content', () => {
    it('should render pain point about KakaoTalk messages', () => {
      render(<ProblemStatementSection />);

      expect(screen.getByText(/수백 개 카톡 대화, 일일이 읽기 힘드시죠\?/i)).toBeInTheDocument();
    });

    it('should render pain point about time spent organizing evidence', () => {
      render(<ProblemStatementSection />);

      expect(screen.getByText(/증거 정리에만 며칠씩 걸리시나요\?/i)).toBeInTheDocument();
    });

    it('should render pain point about repetitive draft writing', () => {
      render(<ProblemStatementSection />);

      expect(screen.getByText(/초안 작성할 때마다 반복 작업에 지치셨나요\?/i)).toBeInTheDocument();
    });

    it('should render pain point about missing evidence', () => {
      render(<ProblemStatementSection />);

      expect(screen.getByText(/중요한 증거를 놓칠까 불안하신가요\?/i)).toBeInTheDocument();
    });
  });

  describe('Icons', () => {
    it('should render icons for each pain point', () => {
      const { container } = render(<ProblemStatementSection />);

      // Each pain point should have an icon (Lucide icon components)
      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThanOrEqual(4);
    });

    it('should use appropriate icon sizes', () => {
      const { container } = render(<ProblemStatementSection />);

      const icons = container.querySelectorAll('svg');
      icons.forEach((icon) => {
        // Icons should have w-12 h-12 or similar sizing
        expect(icon).toHaveClass('w-12');
        expect(icon).toHaveClass('h-12');
      });
    });

    it('should style icons with accent color', () => {
      const { container } = render(<ProblemStatementSection />);

      const icons = container.querySelectorAll('svg');
      icons.forEach((icon) => {
        expect(icon).toHaveClass('text-accent');
      });
    });
  });

  describe('Layout Structure', () => {
    it('should render as a semantic section element', () => {
      const { container } = render(<ProblemStatementSection />);

      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
    });

    it('should have grid layout for pain points', () => {
      const { container } = render(<ProblemStatementSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
    });

    it('should use responsive grid columns', () => {
      const { container } = render(<ProblemStatementSection />);

      const grid = container.querySelector('.grid');
      // Should be 1 column on mobile, 2 on tablet, 4 on desktop
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('md:grid-cols-2');
      expect(grid).toHaveClass('lg:grid-cols-4');
    });

    it('should have appropriate spacing between items', () => {
      const { container } = render(<ProblemStatementSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('gap-8');
    });

    it('should have max-width container', () => {
      const { container } = render(<ProblemStatementSection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toBeInTheDocument();
    });

    it('should center content horizontally', () => {
      const { container } = render(<ProblemStatementSection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toHaveClass('mx-auto');
    });
  });

  describe('Design System Compliance', () => {
    it('should follow 8pt grid spacing', () => {
      const { container } = render(<ProblemStatementSection />);

      const section = container.querySelector('section');
      // Padding should be multiples of 8px
      expect(section).toHaveClass('py-16');
      expect(section).toHaveClass('px-6');
    });

    it('should use calm background color', () => {
      const { container } = render(<ProblemStatementSection />);

      const section = container.querySelector('section');
      expect(section).toHaveClass('bg-white');
    });

    it('should use appropriate text colors', () => {
      render(<ProblemStatementSection />);

      // Pain point text should be readable gray
      const painPoints = screen.getAllByText(/시나요\?|시죠\?/);
      painPoints.forEach((point) => {
        expect(point).toHaveClass('text-gray-700');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have aria-label for section', () => {
      const { container } = render(<ProblemStatementSection />);

      const section = container.querySelector('section');
      expect(section).toHaveAttribute('aria-label', '고객이 겪는 문제점');
    });

    it('should have proper heading hierarchy', () => {
      render(<ProblemStatementSection />);

      const heading = screen.getByRole('heading', { name: /이런 고민 있으셨나요\?/i });
      expect(heading.tagName).toBe('H2');
    });

    it('should have aria-labels for icons', () => {
      const { container } = render(<ProblemStatementSection />);

      const icons = container.querySelectorAll('svg');
      icons.forEach((icon) => {
        expect(icon).toHaveAttribute('aria-label');
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('should stack items vertically on mobile', () => {
      const { container } = render(<ProblemStatementSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
    });

    it('should display 2 columns on tablet', () => {
      const { container } = render(<ProblemStatementSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('md:grid-cols-2');
    });

    it('should display 4 columns on desktop', () => {
      const { container } = render(<ProblemStatementSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-4');
    });
  });

  describe('Visual Presentation', () => {
    it('should center-align text for each pain point', () => {
      const { container } = render(<ProblemStatementSection />);

      const painPointCards = container.querySelectorAll('.text-center');
      expect(painPointCards.length).toBeGreaterThanOrEqual(4);
    });

    it('should have consistent card styling', () => {
      const { container } = render(<ProblemStatementSection />);

      const section = container.querySelector('section');
      const painPointContainers = section?.querySelectorAll('.space-y-4');
      expect(painPointContainers?.length).toBeGreaterThanOrEqual(4);
    });
  });
});
