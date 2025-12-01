/**
 * Test for FinalCTASection Component
 * Plan 3.19.1 - Final CTA (전환 유도)
 *
 * Requirements:
 * - Section title: "지금 바로 시작하세요"
 * - Subtext: "14일 무료 체험, 신용카드 필요 없음"
 * - Large primary CTA button: "무료로 시작하기" (center-aligned)
 * - Secondary button: "영업팀과 상담하기"
 * - Prominent conversion-focused design
 */

import { render, screen } from '@testing-library/react';
import FinalCTASection from '../FinalCTASection';

describe('FinalCTASection Component', () => {
  describe('Section Title', () => {
    it('should render the section title', () => {
      render(<FinalCTASection />);

      const title = screen.getByRole('heading', { name: /지금 바로 시작하세요/i });
      expect(title).toBeInTheDocument();
    });

    it('should style title with secondary color', () => {
      render(<FinalCTASection />);

      const title = screen.getByRole('heading', { name: /지금 바로 시작하세요/i });
      expect(title).toHaveClass('text-secondary');
    });

    it('should use appropriate heading level (h2)', () => {
      render(<FinalCTASection />);

      const title = screen.getByRole('heading', { name: /지금 바로 시작하세요/i });
      expect(title.tagName).toBe('H2');
    });

    it('should use large text size for title', () => {
      render(<FinalCTASection />);

      const title = screen.getByRole('heading', { name: /지금 바로 시작하세요/i });
      // Should have large font size (text-4xl or text-5xl)
      expect(title).toHaveClass('text-4xl');
    });
  });

  describe('Subtext', () => {
    it('should render free trial subtext', () => {
      render(<FinalCTASection />);

      expect(screen.getByText(/14일 무료 체험/i)).toBeInTheDocument();
    });

    it('should mention no credit card required', () => {
      render(<FinalCTASection />);

      expect(screen.getByText(/신용카드 필요 없음/i)).toBeInTheDocument();
    });

    it('should style subtext with neutral color', () => {
      render(<FinalCTASection />);

      const subtext = screen.getByText(/14일 무료 체험, 신용카드 필요 없음/i);
      expect(subtext).toHaveClass('text-neutral-600');
    });
  });

  describe('Primary CTA Button', () => {
    it('should render primary CTA button', () => {
      render(<FinalCTASection />);

      const button = screen.getByRole('link', { name: /무료로 시작하기/i });
      expect(button).toBeInTheDocument();
    });

    it('should style primary button with primary variant', () => {
      render(<FinalCTASection />);

      const button = screen.getByRole('button', { name: /무료로 시작하기/i });
      expect(button).toHaveClass('bg-primary');
    });

    it('should link to signup page', () => {
      render(<FinalCTASection />);

      const button = screen.getByRole('link', { name: /무료로 시작하기/i });
      expect(button).toHaveAttribute('href', '/signup');
    });

    it('should have large button size', () => {
      render(<FinalCTASection />);

      const button = screen.getByRole('button', { name: /무료로 시작하기/i });
      // Should have large padding for prominent CTA
      expect(button).toHaveClass('px-8');
      expect(button).toHaveClass('py-4');
    });
  });

  describe('Secondary CTA Button', () => {
    it('should render secondary CTA button', () => {
      render(<FinalCTASection />);

      const button = screen.getByRole('link', { name: /영업팀과 상담하기/i });
      expect(button).toBeInTheDocument();
    });

    it('should style secondary button differently from primary', () => {
      render(<FinalCTASection />);

      const button = screen.getByRole('button', { name: /영업팀과 상담하기/i });
      // Should NOT have bg-primary class
      expect(button).not.toHaveClass('bg-primary');
      // Should have neutral background styling
      expect(button).toHaveClass('bg-neutral-100');
    });

    it('should link to contact page or email', () => {
      render(<FinalCTASection />);

      const button = screen.getByRole('link', { name: /영업팀과 상담하기/i });
      const href = button.getAttribute('href');
      expect(href).toMatch(/contact|mailto:/i);
    });
  });

  describe('Button Layout', () => {
    it('should center-align buttons', () => {
      const { container } = render(<FinalCTASection />);

      const section = container.querySelector('section');
      const buttonContainer = section?.querySelector('.justify-center, .text-center');
      expect(buttonContainer).toBeInTheDocument();
    });

    it('should display buttons horizontally on desktop', () => {
      const { container } = render(<FinalCTASection />);

      const section = container.querySelector('section');
      // Button container should use flex layout
      const buttonContainer = section?.querySelector('.flex');
      expect(buttonContainer).toBeInTheDocument();
    });

    it('should have spacing between buttons', () => {
      const { container } = render(<FinalCTASection />);

      const section = container.querySelector('section');
      // Should have gap or space between buttons
      const buttonContainer = section?.querySelector('.gap-4, .space-x-4');
      expect(buttonContainer).toBeInTheDocument();
    });
  });

  describe('Layout Structure', () => {
    it('should render as a semantic section element', () => {
      const { container } = render(<FinalCTASection />);

      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
    });

    it('should have max-width container', () => {
      const { container } = render(<FinalCTASection />);

      const maxWidthContainer = container.querySelector('.max-w-4xl, .max-w-5xl');
      expect(maxWidthContainer).toBeInTheDocument();
    });

    it('should center content horizontally', () => {
      const { container } = render(<FinalCTASection />);

      const centeredContainer = container.querySelector('.mx-auto');
      expect(centeredContainer).toBeInTheDocument();
    });

    it('should center-align text content', () => {
      const { container } = render(<FinalCTASection />);

      const section = container.querySelector('section');
      const textCenter = section?.querySelector('.text-center');
      expect(textCenter).toBeInTheDocument();
    });
  });

  describe('Design System Compliance', () => {
    it('should follow 8pt grid spacing', () => {
      const { container } = render(<FinalCTASection />);

      const section = container.querySelector('section');
      // Padding should be multiples of 8px
      expect(section).toHaveClass('py-20');
      expect(section).toHaveClass('px-6');
    });

    it('should use neutral background color', () => {
      const { container } = render(<FinalCTASection />);

      const section = container.querySelector('section');
      expect(section).toHaveClass('bg-neutral-50');
    });

    it('should use secondary color for title', () => {
      render(<FinalCTASection />);

      const title = screen.getByRole('heading', { name: /지금 바로 시작하세요/i });
      expect(title).toHaveClass('text-secondary');
    });
  });

  describe('Accessibility', () => {
    it('should have aria-label for section', () => {
      const { container } = render(<FinalCTASection />);

      const section = container.querySelector('section');
      expect(section).toHaveAttribute('aria-label', '최종 행동 유도');
    });

    it('should have proper heading hierarchy', () => {
      render(<FinalCTASection />);

      const mainHeading = screen.getByRole('heading', { name: /지금 바로 시작하세요/i });
      expect(mainHeading.tagName).toBe('H2');
    });

    it('should have accessible button links', () => {
      render(<FinalCTASection />);

      const primaryButton = screen.getByRole('link', { name: /무료로 시작하기/i });
      const secondaryButton = screen.getByRole('link', { name: /영업팀과 상담하기/i });

      expect(primaryButton).toBeInTheDocument();
      expect(secondaryButton).toBeInTheDocument();
    });
  });

  describe('Visual Presentation', () => {
    it('should have generous spacing around content', () => {
      const { container } = render(<FinalCTASection />);

      const section = container.querySelector('section');
      const spacedContainer = section?.querySelector('.space-y-8');
      expect(spacedContainer).toBeInTheDocument();
    });

    it('should make CTA visually prominent', () => {
      const { container } = render(<FinalCTASection />);

      // Section should have substantial vertical padding
      const section = container.querySelector('section');
      expect(section).toHaveClass('py-20');
    });
  });

  describe('Responsive Behavior', () => {
    it('should stack buttons vertically on mobile', () => {
      const { container } = render(<FinalCTASection />);

      const section = container.querySelector('section');
      const buttonContainer = section?.querySelector('.flex-col, .flex');
      expect(buttonContainer).toBeInTheDocument();
    });
  });
});
