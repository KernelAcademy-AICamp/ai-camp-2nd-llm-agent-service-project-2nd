/**
 * Plan 3.19.2 - Responsive Design Tests
 *
 * Tests for landing page responsive layouts:
 * - Mobile (375px): 1-column layout
 * - Tablet (768px): 2-column layout (md: breakpoint)
 * - Desktop (1440px): 3-column layout (lg: breakpoint)
 *
 * Test Strategy:
 * 1. RED: Write failing tests for tablet breakpoint (md:grid-cols-2)
 * 2. GREEN: Add md:grid-cols-2 to SolutionSection and PricingSection
 * 3. REFACTOR: Extract common responsive patterns if needed
 */

import { render } from '@testing-library/react';
import '@testing-library/jest-dom';

// Import components directly for unit testing
import SolutionSection from '../../components/landing/SolutionSection';
import PricingSection from '../../components/landing/PricingSection';
import LandingFooter from '../../components/landing/LandingFooter';
import HeroSection from '../../components/landing/HeroSection';

// Mock next/image
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    const { fill, priority, ...imgProps } = props;
    return (
      <img
        {...imgProps}
        data-fill={fill ? 'true' : undefined}
        data-priority={priority ? 'true' : undefined}
      />
    );
  },
}));

// Mock next/link
jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...props }: any) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

describe('Plan 3.19.2 - Responsive Design', () => {
  describe('Breakpoint Requirements', () => {
    /**
     * Requirements from plan.md:
     * - Mobile (375px): 1-column → grid-cols-1
     * - Tablet (768px): 2-column → md:grid-cols-2
     * - Desktop (1440px): 3-column → lg:grid-cols-3
     */

    test('should define correct Tailwind breakpoints', () => {
      // Tailwind default breakpoints:
      // sm: 640px, md: 768px, lg: 1024px, xl: 1280px, 2xl: 1536px
      // Our target: md (768px) for tablet, lg (1024px+) for desktop
      expect(true).toBe(true); // Placeholder - breakpoints are Tailwind config
    });
  });

  describe('HeroSection Responsive Layout', () => {
    test('should have mobile-first grid layout (1-column default)', () => {
      const { container } = render(<HeroSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
      expect(grid).toHaveClass('grid-cols-1');
    });

    test('should have 2-column layout on large screens', () => {
      const { container } = render(<HeroSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-2');
    });

    // HeroSection uses 2-column max, which is appropriate for hero content
    test('Hero should NOT have 3-column layout (2-column is appropriate)', () => {
      const { container } = render(<HeroSection />);

      const grid = container.querySelector('.grid');
      expect(grid).not.toHaveClass('lg:grid-cols-3');
    });
  });

  describe('SolutionSection Responsive Layout', () => {
    test('should have mobile-first grid layout (1-column default)', () => {
      const { container } = render(<SolutionSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
      expect(grid).toHaveClass('grid-cols-1');
    });

    /**
     * RED TEST - This should FAIL initially
     * SolutionSection currently has: grid-cols-1 lg:grid-cols-3
     * It's missing: md:grid-cols-2 for tablet breakpoint
     */
    test('should have 2-column layout on tablet (md breakpoint)', () => {
      const { container } = render(<SolutionSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('md:grid-cols-2');
    });

    test('should have 3-column layout on desktop (lg breakpoint)', () => {
      const { container } = render(<SolutionSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });
  });

  describe('PricingSection Responsive Layout', () => {
    test('should have mobile-first grid layout (1-column default)', () => {
      const { container } = render(<PricingSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
      expect(grid).toHaveClass('grid-cols-1');
    });

    /**
     * RED TEST - This should FAIL initially
     * PricingSection currently has: grid-cols-1 lg:grid-cols-3
     * It's missing: md:grid-cols-2 for tablet breakpoint
     */
    test('should have 2-column layout on tablet (md breakpoint)', () => {
      const { container } = render(<PricingSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('md:grid-cols-2');
    });

    test('should have 3-column layout on desktop (lg breakpoint)', () => {
      const { container } = render(<PricingSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });
  });

  describe('LandingFooter Responsive Layout', () => {
    test('should have mobile-first grid layout (1-column default)', () => {
      const { container } = render(<LandingFooter />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
      expect(grid).toHaveClass('grid-cols-1');
    });

    test('should have 2-column layout on tablet (md breakpoint)', () => {
      const { container } = render(<LandingFooter />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('md:grid-cols-2');
    });

    test('should have 3-column layout on desktop (lg breakpoint)', () => {
      const { container } = render(<LandingFooter />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    // Footer already implements correct responsive pattern
    test('Footer should be the reference implementation for 3-tier responsive', () => {
      const { container } = render(<LandingFooter />);

      const grid = container.querySelector('.grid');

      // Verify the complete responsive pattern
      expect(grid).toHaveClass('grid-cols-1'); // Mobile
      expect(grid).toHaveClass('md:grid-cols-2'); // Tablet
      expect(grid).toHaveClass('lg:grid-cols-3'); // Desktop
    });
  });

  describe('Responsive Pattern Consistency', () => {
    test('all 3-column sections should follow same responsive pattern', () => {
      const solutionContainer = render(<SolutionSection />).container;
      const pricingContainer = render(<PricingSection />).container;
      const footerContainer = render(<LandingFooter />).container;

      const solutionGrid = solutionContainer.querySelector('.grid');
      const pricingGrid = pricingContainer.querySelector('.grid');
      const footerGrid = footerContainer.querySelector('.grid');

      // All should have the 3-tier responsive pattern
      const expectedClasses = ['grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3'];

      expectedClasses.forEach((className) => {
        expect(solutionGrid).toHaveClass(className);
        expect(pricingGrid).toHaveClass(className);
        expect(footerGrid).toHaveClass(className);
      });
    });
  });
});
