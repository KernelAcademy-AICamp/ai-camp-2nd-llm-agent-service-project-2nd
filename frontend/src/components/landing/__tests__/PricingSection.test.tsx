/**
 * Test for PricingSection Component
 * Plan 3.19.1 - Pricing (명확한 가격 정책)
 *
 * Requirements:
 * - Section title: "투명한 가격, 숨은 비용 없음"
 * - 3-tier pricing table:
 *   - Basic: ₩49,000/월 (개인 변호사)
 *   - Professional: ₩99,000/월 (소형 로펌, 가장 인기) - highlighted
 *   - Enterprise: ₩199,000/월 (대형 로펌, 맞춤 기능)
 * - Feature list with checkmarks for each plan
 * - "14일 무료 체험" emphasis
 */

import { render, screen } from '@testing-library/react';
import PricingSection from '../PricingSection';

describe('PricingSection Component', () => {
  describe('Section Title', () => {
    it('should render the section title', () => {
      render(<PricingSection />);

      const title = screen.getByRole('heading', { name: /투명한 가격, 숨은 비용 없음/i });
      expect(title).toBeInTheDocument();
    });

    it('should style title with Deep Trust Blue', () => {
      render(<PricingSection />);

      const title = screen.getByRole('heading', { name: /투명한 가격, 숨은 비용 없음/i });
      expect(title).toHaveClass('text-deep-trust-blue');
    });

    it('should use appropriate heading level (h2)', () => {
      render(<PricingSection />);

      const title = screen.getByRole('heading', { name: /투명한 가격, 숨은 비용 없음/i });
      expect(title.tagName).toBe('H2');
    });
  });

  describe('Basic Plan', () => {
    it('should render Basic plan name', () => {
      render(<PricingSection />);

      expect(screen.getByRole('heading', { name: /Basic/i })).toBeInTheDocument();
    });

    it('should render Basic plan price', () => {
      render(<PricingSection />);

      expect(screen.getByText(/₩49,000/i)).toBeInTheDocument();
      // "월" appears multiple times (in price and features), just verify price exists
      const monthTexts = screen.getAllByText(/월/);
      expect(monthTexts.length).toBeGreaterThanOrEqual(1);
    });

    it('should render Basic plan target audience', () => {
      render(<PricingSection />);

      expect(screen.getByText(/개인 변호사/i)).toBeInTheDocument();
    });
  });

  describe('Professional Plan', () => {
    it('should render Professional plan name', () => {
      render(<PricingSection />);

      expect(screen.getByRole('heading', { name: /Professional/i })).toBeInTheDocument();
    });

    it('should render Professional plan price', () => {
      render(<PricingSection />);

      expect(screen.getByText(/₩99,000/i)).toBeInTheDocument();
    });

    it('should render Professional plan target audience', () => {
      render(<PricingSection />);

      expect(screen.getByText(/소형 로펌/i)).toBeInTheDocument();
    });

    it('should highlight Professional as most popular', () => {
      render(<PricingSection />);

      expect(screen.getByText(/가장 인기/i)).toBeInTheDocument();
    });
  });

  describe('Enterprise Plan', () => {
    it('should render Enterprise plan name', () => {
      render(<PricingSection />);

      expect(screen.getByRole('heading', { name: /Enterprise/i })).toBeInTheDocument();
    });

    it('should render Enterprise plan price', () => {
      render(<PricingSection />);

      expect(screen.getByText(/₩199,000/i)).toBeInTheDocument();
    });

    it('should render Enterprise plan target audience', () => {
      render(<PricingSection />);

      expect(screen.getByText(/대형 로펌/i)).toBeInTheDocument();
    });

    it('should mention custom features for Enterprise', () => {
      render(<PricingSection />);

      expect(screen.getByText(/맞춤 기능/i)).toBeInTheDocument();
    });
  });

  describe('Free Trial Badge', () => {
    it('should display 14-day free trial message', () => {
      render(<PricingSection />);

      expect(screen.getByText(/14일 무료 체험/i)).toBeInTheDocument();
    });

    it('should emphasize free trial with accent styling', () => {
      const { container } = render(<PricingSection />);

      const trialBadge = screen.getByText(/14일 무료 체험/i);
      expect(trialBadge).toHaveClass('text-accent');
    });
  });

  describe('Feature Lists', () => {
    it('should render feature checkmarks for each plan', () => {
      const { container } = render(<PricingSection />);

      // Should have checkmark icons (at least 3 plans worth of features)
      const checkIcons = container.querySelectorAll('svg');
      expect(checkIcons.length).toBeGreaterThanOrEqual(9); // 3+ features per plan × 3 plans
    });

    it('should style checkmarks with accent color', () => {
      const { container } = render(<PricingSection />);

      const checkIcons = container.querySelectorAll('svg');
      // Most icons should be checkmarks with accent color
      let accentCheckCount = 0;
      checkIcons.forEach((icon) => {
        if (icon.classList.contains('text-accent')) {
          accentCheckCount++;
        }
      });
      expect(accentCheckCount).toBeGreaterThanOrEqual(9);
    });
  });

  describe('Pricing Card Structure', () => {
    it('should render 3 pricing cards', () => {
      const { container } = render(<PricingSection />);

      // Should have 3 plan cards (Basic, Professional, Enterprise)
      const cards = container.querySelectorAll('.bg-white');
      expect(cards.length).toBeGreaterThanOrEqual(3);
    });

    it('should have rounded corners on cards', () => {
      const { container } = render(<PricingSection />);

      const section = container.querySelector('section');
      const roundedCards = section?.querySelectorAll('.rounded-xl');
      expect(roundedCards?.length).toBeGreaterThanOrEqual(3);
    });

    it('should have shadow on cards', () => {
      const { container } = render(<PricingSection />);

      const section = container.querySelector('section');
      const shadowCards = section?.querySelectorAll('.shadow-lg');
      expect(shadowCards?.length).toBeGreaterThanOrEqual(3);
    });

    it('should highlight Professional plan card', () => {
      const { container } = render(<PricingSection />);

      // Professional card should have special styling (border or scale)
      const section = container.querySelector('section');
      const highlightedCards = section?.querySelectorAll('.border-accent, .ring-accent, .scale-105');
      expect(highlightedCards?.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Layout Structure', () => {
    it('should render as a semantic section element', () => {
      const { container } = render(<PricingSection />);

      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
    });

    it('should have grid layout for pricing cards', () => {
      const { container } = render(<PricingSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
    });

    it('should use 3-column layout on desktop', () => {
      const { container } = render(<PricingSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('should use responsive grid columns', () => {
      const { container } = render(<PricingSection />);

      const grid = container.querySelector('.grid');
      // 1 column on mobile, 3 on desktop
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('should have appropriate spacing between cards', () => {
      const { container } = render(<PricingSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('gap-8');
    });

    it('should have max-width container', () => {
      const { container } = render(<PricingSection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toBeInTheDocument();
    });

    it('should center content horizontally', () => {
      const { container } = render(<PricingSection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toHaveClass('mx-auto');
    });
  });

  describe('Design System Compliance', () => {
    it('should follow 8pt grid spacing', () => {
      const { container } = render(<PricingSection />);

      const section = container.querySelector('section');
      // Padding should be multiples of 8px
      expect(section).toHaveClass('py-20');
      expect(section).toHaveClass('px-6');
    });

    it('should use white background color', () => {
      const { container } = render(<PricingSection />);

      const section = container.querySelector('section');
      expect(section).toHaveClass('bg-white');
    });

    it('should use Deep Trust Blue for plan names', () => {
      render(<PricingSection />);

      const planNames = [
        screen.getByRole('heading', { name: /Basic/i }),
        screen.getByRole('heading', { name: /Professional/i }),
        screen.getByRole('heading', { name: /Enterprise/i }),
      ];

      planNames.forEach((name) => {
        expect(name).toHaveClass('text-deep-trust-blue');
      });
    });

    it('should use gray text for descriptions', () => {
      render(<PricingSection />);

      const descriptions = [
        screen.getByText(/개인 변호사/i),
        screen.getByText(/소형 로펌/i),
        screen.getByText(/대형 로펌/i),
      ];

      descriptions.forEach((desc) => {
        expect(desc).toHaveClass('text-gray-600');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have aria-label for section', () => {
      const { container } = render(<PricingSection />);

      const section = container.querySelector('section');
      expect(section).toHaveAttribute('aria-label', '가격 플랜');
    });

    it('should have proper heading hierarchy', () => {
      render(<PricingSection />);

      const mainHeading = screen.getByRole('heading', { name: /투명한 가격, 숨은 비용 없음/i });
      expect(mainHeading.tagName).toBe('H2');

      const planHeadings = screen.getAllByRole('heading', { level: 3 });
      expect(planHeadings.length).toBe(3);
    });

    it('should have aria-labels for checkmark icons', () => {
      const { container } = render(<PricingSection />);

      const checkIcons = container.querySelectorAll('svg');
      // Checkmark icons should have aria-labels
      let checkIconsWithLabels = 0;
      checkIcons.forEach((icon) => {
        if (icon.getAttribute('aria-label')) {
          checkIconsWithLabels++;
        }
      });
      expect(checkIconsWithLabels).toBeGreaterThanOrEqual(9);
    });
  });

  describe('Responsive Behavior', () => {
    it('should stack cards vertically on mobile', () => {
      const { container } = render(<PricingSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
    });

    it('should display 3 columns on desktop', () => {
      const { container } = render(<PricingSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });
  });

  describe('Visual Presentation', () => {
    it('should center-align content in pricing cards', () => {
      const { container } = render(<PricingSection />);

      const section = container.querySelector('section');
      const centeredCards = section?.querySelectorAll('.text-center');
      expect(centeredCards?.length).toBeGreaterThanOrEqual(3);
    });

    it('should have consistent spacing within cards', () => {
      const { container } = render(<PricingSection />);

      const section = container.querySelector('section');
      const spacedCards = section?.querySelectorAll('.space-y-6');
      expect(spacedCards?.length).toBeGreaterThanOrEqual(3);
    });
  });
});
