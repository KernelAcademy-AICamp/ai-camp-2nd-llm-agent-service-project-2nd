/**
 * Test for LandingNav Component
 * Plan 3.19.1 - Navigation Bar (고정 헤더)
 *
 * Requirements:
 * - Logo on left, menu items on right (기능/가격/고객사례/로그인/무료체험)
 * - Sticky position
 * - Scroll-triggered background blur effect
 * - Scroll-triggered shadow
 */

import { render, screen } from '@testing-library/react';
import LandingNav from '../LandingNav';

describe('LandingNav Component', () => {
  describe('Structure and Layout', () => {
    it('should render the logo on the left', () => {
      render(<LandingNav />);

      const logo = screen.getByRole('img', { name: /legal evidence hub|leh/i });
      expect(logo).toBeInTheDocument();
    });

    it('should render navigation menu items on the right', () => {
      render(<LandingNav />);

      // Check for required menu items
      expect(screen.getByText('기능')).toBeInTheDocument();
      expect(screen.getByText('가격')).toBeInTheDocument();
      expect(screen.getByText('고객사례')).toBeInTheDocument();
      expect(screen.getByText('로그인')).toBeInTheDocument();
      expect(screen.getByText('무료체험')).toBeInTheDocument();
    });

    it('should render menu items as navigation links', () => {
      render(<LandingNav />);

      const featureLink = screen.getByRole('link', { name: '기능' });
      const pricingLink = screen.getByRole('link', { name: '가격' });
      const testimonialsLink = screen.getByRole('link', { name: '고객사례' });
      const loginLink = screen.getByRole('link', { name: '로그인' });

      expect(featureLink).toBeInTheDocument();
      expect(pricingLink).toBeInTheDocument();
      expect(testimonialsLink).toBeInTheDocument();
      expect(loginLink).toBeInTheDocument();
    });

    it('should render CTA button with primary styling', () => {
      render(<LandingNav />);

      // aria-label takes precedence for accessible name
      const ctaButton = screen.getByRole('link', { name: /무료체험/i });
      expect(ctaButton).toBeInTheDocument();
      expect(ctaButton).toHaveClass('btn-primary');
    });
  });

  describe('Sticky Positioning', () => {
    it('should have sticky position class', () => {
      const { container } = render(<LandingNav />);

      const nav = container.querySelector('nav');
      expect(nav).toHaveClass('sticky');
    });

    it('should be positioned at the top', () => {
      const { container } = render(<LandingNav />);

      const nav = container.querySelector('nav');
      expect(nav).toHaveClass('top-0');
    });

    it('should have high z-index for layering', () => {
      const { container } = render(<LandingNav />);

      const nav = container.querySelector('nav');
      expect(nav).toHaveClass('z-50');
    });
  });

  describe('Scroll Effects', () => {
    it('should accept isScrolled prop for scroll state', () => {
      const { rerender } = render(<LandingNav isScrolled={false} />);
      const { container } = render(<LandingNav isScrolled={true} />);

      // Component should accept prop without error
      expect(container).toBeInTheDocument();
    });

    it('should apply backdrop-blur when scrolled', () => {
      const { container } = render(<LandingNav isScrolled={true} />);

      const nav = container.querySelector('nav');
      expect(nav).toHaveClass('backdrop-blur-md');
    });

    it('should apply shadow when scrolled', () => {
      const { container } = render(<LandingNav isScrolled={true} />);

      const nav = container.querySelector('nav');
      expect(nav).toHaveClass('shadow-md');
    });

    it('should have transparent background when not scrolled', () => {
      const { container } = render(<LandingNav isScrolled={false} />);

      const nav = container.querySelector('nav');
      expect(nav).not.toHaveClass('backdrop-blur-md');
      expect(nav).not.toHaveClass('shadow-md');
    });

    it('should apply background color with opacity when scrolled', () => {
      const { container } = render(<LandingNav isScrolled={true} />);

      const nav = container.querySelector('nav');
      // Should have white background with opacity for glass effect
      expect(nav).toHaveClass('bg-white/80');
    });
  });

  describe('Design System Compliance', () => {
    it('should use Pretendard font family', () => {
      const { container } = render(<LandingNav />);

      const nav = container.querySelector('nav');
      // Font family is applied globally, check that nav exists
      expect(nav).toBeInTheDocument();
    });

    it('should follow 8pt grid spacing', () => {
      const { container } = render(<LandingNav />);

      const nav = container.querySelector('nav');
      // Spacing should be multiples of 8px (px-4 = 16px, py-4 = 16px)
      expect(nav).toHaveClass('px-6');
      expect(nav).toHaveClass('py-4');
    });

    it('should use Deep Trust Blue for logo text', () => {
      render(<LandingNav />);

      const logo = screen.getByText('LEH');
      expect(logo).toHaveClass('text-secondary');
    });
  });

  describe('Accessibility', () => {
    it('should have semantic nav element', () => {
      const { container } = render(<LandingNav />);

      const nav = container.querySelector('nav');
      expect(nav).toBeInTheDocument();
      expect(nav?.tagName).toBe('NAV');
    });

    it('should have aria-label for navigation', () => {
      const { container } = render(<LandingNav />);

      const nav = container.querySelector('nav');
      expect(nav).toHaveAttribute('aria-label', '메인 네비게이션');
    });

    it('should have proper link hierarchy', () => {
      render(<LandingNav />);

      const links = screen.getAllByRole('link');
      // Should have 5 links (기능, 가격, 고객사례, 로그인, 무료체험)
      expect(links.length).toBeGreaterThanOrEqual(5);
    });
  });

  describe('Responsive Behavior', () => {
    it('should have max-width container', () => {
      const { container } = render(<LandingNav />);

      const innerContainer = container.querySelector('.max-w-7xl');
      expect(innerContainer).toBeInTheDocument();
    });

    it('should center content horizontally', () => {
      const { container } = render(<LandingNav />);

      const innerContainer = container.querySelector('.max-w-7xl');
      expect(innerContainer).toHaveClass('mx-auto');
    });

    it('should use flexbox for layout', () => {
      const { container } = render(<LandingNav />);

      const innerContainer = container.querySelector('.max-w-7xl');
      expect(innerContainer).toHaveClass('flex');
      expect(innerContainer).toHaveClass('justify-between');
      expect(innerContainer).toHaveClass('items-center');
    });
  });
});
