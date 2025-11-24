/**
 * Test for TestimonialsSection Component
 * Plan 3.19.1 - Testimonials (실제 후기)
 *
 * Requirements:
 * - Section title: "이미 사용 중인 변호사님들의 평가"
 * - 3 testimonial cards with:
 *   - Profile photo (or initials)
 *   - Name
 *   - Organization/affiliation
 *   - Rating (stars)
 *   - Short testimonial text (e.g., "증거 정리 시간이 1/10로 줄었습니다")
 * - Placeholder text when no real data
 */

import { render, screen } from '@testing-library/react';
import TestimonialsSection from '../TestimonialsSection';

describe('TestimonialsSection Component', () => {
  describe('Section Title', () => {
    it('should render the section title', () => {
      render(<TestimonialsSection />);

      const title = screen.getByRole('heading', { name: /이미 사용 중인 변호사님들의 평가/i });
      expect(title).toBeInTheDocument();
    });

    it('should style title with Deep Trust Blue', () => {
      render(<TestimonialsSection />);

      const title = screen.getByRole('heading', { name: /이미 사용 중인 변호사님들의 평가/i });
      expect(title).toHaveClass('text-deep-trust-blue');
    });

    it('should use appropriate heading level (h2)', () => {
      render(<TestimonialsSection />);

      const title = screen.getByRole('heading', { name: /이미 사용 중인 변호사님들의 평가/i });
      expect(title.tagName).toBe('H2');
    });
  });

  describe('Testimonial Cards', () => {
    it('should render 3 testimonial cards', () => {
      const { container } = render(<TestimonialsSection />);

      // Should have 3 testimonial cards
      const cards = container.querySelectorAll('.bg-white');
      expect(cards.length).toBeGreaterThanOrEqual(3);
    });

    it('should have rounded corners on cards', () => {
      const { container } = render(<TestimonialsSection />);

      const section = container.querySelector('section');
      const roundedCards = section?.querySelectorAll('.rounded-xl');
      expect(roundedCards?.length).toBeGreaterThanOrEqual(3);
    });

    it('should have shadow on cards', () => {
      const { container } = render(<TestimonialsSection />);

      const section = container.querySelector('section');
      const shadowCards = section?.querySelectorAll('.shadow-lg');
      expect(shadowCards?.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Testimonial Content', () => {
    it('should render reviewer names', () => {
      render(<TestimonialsSection />);

      // Should have at least 3 names (can be placeholder data)
      const nameElements = screen.getAllByText(/변호사|님/);
      expect(nameElements.length).toBeGreaterThanOrEqual(3);
    });

    it('should render reviewer organizations', () => {
      render(<TestimonialsSection />);

      // Should have organization/affiliation info
      const orgElements = screen.getAllByText(/법무법인|로펌|사무소/);
      expect(orgElements.length).toBeGreaterThanOrEqual(3);
    });

    it('should render testimonial text', () => {
      render(<TestimonialsSection />);

      // Should have testimonial quotes (broader pattern to match all testimonials)
      const testimonialTexts = screen.getAllByText(/시간|효율|추천|만족|분석|정확|케이스/);
      expect(testimonialTexts.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Rating Display', () => {
    it('should render star ratings', () => {
      const { container } = render(<TestimonialsSection />);

      // Should have star icons for ratings (5 stars × 3 testimonials = 15)
      const stars = container.querySelectorAll('svg');
      expect(stars.length).toBeGreaterThanOrEqual(15);
    });

    it('should style stars with accent color', () => {
      const { container } = render(<TestimonialsSection />);

      const stars = container.querySelectorAll('svg');
      let filledStars = 0;
      stars.forEach((star) => {
        if (star.classList.contains('fill-accent') || star.classList.contains('text-accent')) {
          filledStars++;
        }
      });
      expect(filledStars).toBeGreaterThanOrEqual(15);
    });
  });

  describe('Profile Display', () => {
    it('should render profile initials or avatars', () => {
      const { container } = render(<TestimonialsSection />);

      // Should have profile indicators (initials in circles or images)
      const section = container.querySelector('section');
      const profiles = section?.querySelectorAll('.rounded-full');
      expect(profiles?.length).toBeGreaterThanOrEqual(3);
    });

    it('should style profile indicators with background', () => {
      const { container } = render(<TestimonialsSection />);

      // Profile circles should have bg color
      const section = container.querySelector('section');
      const profileCircles = section?.querySelectorAll('.bg-accent, .bg-gray-200');
      expect(profileCircles?.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Layout Structure', () => {
    it('should render as a semantic section element', () => {
      const { container } = render(<TestimonialsSection />);

      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
    });

    it('should have grid layout for testimonials', () => {
      const { container } = render(<TestimonialsSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
    });

    it('should use 3-column layout on desktop', () => {
      const { container } = render(<TestimonialsSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('should use responsive grid columns', () => {
      const { container } = render(<TestimonialsSection />);

      const grid = container.querySelector('.grid');
      // 1 column on mobile, 3 on desktop
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('should have appropriate spacing between cards', () => {
      const { container } = render(<TestimonialsSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('gap-8');
    });

    it('should have max-width container', () => {
      const { container } = render(<TestimonialsSection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toBeInTheDocument();
    });

    it('should center content horizontally', () => {
      const { container } = render(<TestimonialsSection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toHaveClass('mx-auto');
    });
  });

  describe('Design System Compliance', () => {
    it('should follow 8pt grid spacing', () => {
      const { container } = render(<TestimonialsSection />);

      const section = container.querySelector('section');
      // Padding should be multiples of 8px
      expect(section).toHaveClass('py-20');
      expect(section).toHaveClass('px-6');
    });

    it('should use calm background color', () => {
      const { container } = render(<TestimonialsSection />);

      const section = container.querySelector('section');
      expect(section).toHaveClass('bg-calm-grey');
    });

    it('should use Deep Trust Blue for reviewer names', () => {
      const { container } = render(<TestimonialsSection />);

      // Names should use Deep Trust Blue
      const section = container.querySelector('section');
      const nameElements = section?.querySelectorAll('.text-deep-trust-blue');
      expect(nameElements?.length).toBeGreaterThanOrEqual(4); // Section title + 3 names
    });

    it('should use gray text for testimonials', () => {
      const { container } = render(<TestimonialsSection />);

      // Testimonial text should be readable gray
      const section = container.querySelector('section');
      const textElements = section?.querySelectorAll('.text-gray-600');
      expect(textElements?.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Accessibility', () => {
    it('should have aria-label for section', () => {
      const { container } = render(<TestimonialsSection />);

      const section = container.querySelector('section');
      expect(section).toHaveAttribute('aria-label', '고객 후기');
    });

    it('should have proper heading hierarchy', () => {
      render(<TestimonialsSection />);

      const mainHeading = screen.getByRole('heading', { name: /이미 사용 중인 변호사님들의 평가/i });
      expect(mainHeading.tagName).toBe('H2');
    });

    it('should have aria-labels for star icons', () => {
      const { container } = render(<TestimonialsSection />);

      const stars = container.querySelectorAll('svg');
      // Stars should have aria-labels
      let starsWithLabels = 0;
      stars.forEach((star) => {
        if (star.getAttribute('aria-label')) {
          starsWithLabels++;
        }
      });
      expect(starsWithLabels).toBeGreaterThanOrEqual(15);
    });
  });

  describe('Responsive Behavior', () => {
    it('should stack cards vertically on mobile', () => {
      const { container } = render(<TestimonialsSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
    });

    it('should display 3 columns on desktop', () => {
      const { container } = render(<TestimonialsSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });
  });

  describe('Visual Presentation', () => {
    it('should have consistent spacing within cards', () => {
      const { container } = render(<TestimonialsSection />);

      const section = container.querySelector('section');
      const spacedCards = section?.querySelectorAll('.space-y-4');
      expect(spacedCards?.length).toBeGreaterThanOrEqual(3);
    });

    it('should display testimonials with proper padding', () => {
      const { container } = render(<TestimonialsSection />);

      const section = container.querySelector('section');
      const paddedCards = section?.querySelectorAll('.p-8, .p-6');
      expect(paddedCards?.length).toBeGreaterThanOrEqual(3);
    });
  });
});
