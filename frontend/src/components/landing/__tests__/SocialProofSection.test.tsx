/**
 * Test for SocialProofSection Component
 * Plan 3.19.1 - Social Proof
 *
 * Requirements:
 * - "50개 로펌 사용 중" (신뢰 배지)
 * - 로고 슬라이더 (유명 로펌 로고, 실제 데이터 없을 경우 "leading law firms")
 * - 평균 평점 표시 (5.0/5.0)
 */

import { render, screen } from '@testing-library/react';
import SocialProofSection from '../SocialProofSection';

describe('SocialProofSection Component', () => {
  describe('Trust Badge', () => {
    it('should display the number of law firms using the service', () => {
      render(<SocialProofSection />);

      const number = screen.getByText('50개');
      const text = screen.getByText(/로펌 사용 중/i);

      expect(number).toBeInTheDocument();
      expect(text).toBeInTheDocument();
    });

    it('should highlight the number prominently', () => {
      render(<SocialProofSection />);

      const number = screen.getByText('50개');
      expect(number).toHaveClass('font-bold');
    });
  });

  describe('Rating Display', () => {
    it('should display the average rating', () => {
      render(<SocialProofSection />);

      const ratings = screen.getAllByText(/5\.0/);
      expect(ratings.length).toBeGreaterThanOrEqual(1);
    });

    it('should display rating with star visualization', () => {
      render(<SocialProofSection />);

      // Should have 5 star icons
      const stars = screen.getAllByLabelText(/별/i);
      expect(stars.length).toBe(5);
    });

    it('should display rating denominator', () => {
      render(<SocialProofSection />);

      const denominatorText = screen.getByText(/만점/);
      expect(denominatorText).toBeInTheDocument();
    });
  });

  describe('Logo Slider', () => {
    it('should display law firm logos', () => {
      render(<SocialProofSection />);

      // Should have multiple logo images
      const logos = screen.getAllByRole('img');
      expect(logos.length).toBeGreaterThanOrEqual(3);
    });

    it('should have alt text for each logo', () => {
      render(<SocialProofSection />);

      const logos = screen.getAllByRole('img');
      logos.forEach((logo) => {
        expect(logo).toHaveAttribute('alt');
        expect(logo.getAttribute('alt')).not.toBe('');
      });
    });

    it('should display placeholder text when no real logos', () => {
      render(<SocialProofSection />);

      // Should have "leading law firms" or similar text
      const placeholderText = screen.getByText(/leading|신뢰받는|주요/i);
      expect(placeholderText).toBeInTheDocument();
    });
  });

  describe('Layout and Structure', () => {
    it('should use semantic section element', () => {
      const { container } = render(<SocialProofSection />);

      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
    });

    it('should have centered layout', () => {
      const { container } = render(<SocialProofSection />);

      const section = container.querySelector('section');
      expect(section).toHaveClass('text-center');
    });

    it('should have max-width container', () => {
      const { container } = render(<SocialProofSection />);

      const innerContainer = container.querySelector('.max-w-7xl');
      expect(innerContainer).toBeInTheDocument();
    });

    it('should have appropriate spacing', () => {
      const { container } = render(<SocialProofSection />);

      const section = container.querySelector('section');
      expect(section).toHaveClass('py-12');
    });
  });

  describe('Design System Compliance', () => {
    it('should use gray background', () => {
      const { container } = render(<SocialProofSection />);

      const section = container.querySelector('section');
      expect(section).toHaveClass('bg-gray-50');
    });

    it('should use appropriate text colors', () => {
      render(<SocialProofSection />);

      const trustBadge = screen.getByText(/로펌 사용 중/);
      expect(trustBadge).toHaveClass('text-gray-700');
    });

    it('should use accent color for rating', () => {
      render(<SocialProofSection />);

      const ratings = screen.getAllByText(/5\.0/);
      const accentRating = ratings.find((el) => el.className.includes('text-accent'));
      expect(accentRating).toBeTruthy();
    });

    it('should follow 8pt grid spacing', () => {
      const { container } = render(<SocialProofSection />);

      const section = container.querySelector('section');
      // py-12 = 48px = 6 * 8pt
      expect(section).toHaveClass('py-12');
    });
  });

  describe('Accessibility', () => {
    it('should have descriptive section label', () => {
      const { container } = render(<SocialProofSection />);

      const section = container.querySelector('section');
      expect(section).toHaveAttribute('aria-label');
    });

    it('should have proper image alt texts', () => {
      render(<SocialProofSection />);

      const logos = screen.getAllByRole('img');
      logos.forEach((logo) => {
        const alt = logo.getAttribute('alt');
        expect(alt).toBeTruthy();
        expect(alt?.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('should stack elements vertically on mobile', () => {
      const { container } = render(<SocialProofSection />);

      const gridContainer = container.querySelector('.space-y-8');
      expect(gridContainer).toBeInTheDocument();
    });

    it('should have horizontal logo slider', () => {
      const { container } = render(<SocialProofSection />);

      const logoContainer = container.querySelector('.flex');
      expect(logoContainer).toBeInTheDocument();
    });
  });

  describe('Visual Hierarchy', () => {
    it('should display trust badge prominently', () => {
      render(<SocialProofSection />);

      const text = screen.getByText(/로펌 사용 중/i);
      expect(text).toHaveClass('text-lg');
    });

    it('should use appropriate font weights', () => {
      render(<SocialProofSection />);

      const number = screen.getByText('50개');
      expect(number).toHaveClass('font-bold');
    });
  });

  describe('Logo Slider Animation', () => {
    it('should have overflow handling for slider', () => {
      const { container } = render(<SocialProofSection />);

      const slider = container.querySelector('.overflow-hidden');
      expect(slider).toBeInTheDocument();
    });

    it('should have gap between logos', () => {
      const { container } = render(<SocialProofSection />);

      const logoContainer = container.querySelector('.gap-8');
      expect(logoContainer).toBeInTheDocument();
    });
  });
});
