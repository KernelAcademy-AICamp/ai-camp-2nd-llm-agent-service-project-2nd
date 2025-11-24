/**
 * Test for HeroSection Component
 * Plan 3.19.1 - Hero Section
 *
 * Requirements:
 * - Headline: "증거 정리 시간 90% 단축" (큰 폰트, Deep Trust Blue)
 * - Subheadline: "AI가 이혼 소송 증거를 자동 분석하고 초안을 작성합니다"
 * - CTA button: "무료로 시작하기" (Primary, 눈에 띄는 위치)
 * - Hero image/screenshot: 실제 제품 UI 미리보기
 */

import { render, screen } from '@testing-library/react';
import HeroSection from '../HeroSection';

describe('HeroSection Component', () => {
  describe('Content and Copy', () => {
    it('should render the main headline', () => {
      render(<HeroSection />);

      const headline = screen.getByRole('heading', {
        name: /증거 정리 시간 90% 단축/i,
      });
      expect(headline).toBeInTheDocument();
    });

    it('should render the subheadline', () => {
      render(<HeroSection />);

      const subheadline = screen.getByText(
        /AI가 이혼 소송 증거를 자동 분석하고 초안을 작성합니다/i
      );
      expect(subheadline).toBeInTheDocument();
    });

    it('should render the primary CTA button', () => {
      render(<HeroSection />);

      const ctaButton = screen.getByRole('link', { name: /무료로 시작하기/i });
      expect(ctaButton).toBeInTheDocument();
    });

    it('should have CTA button with primary styling', () => {
      render(<HeroSection />);

      const ctaButton = screen.getByRole('link', { name: /무료로 시작하기/i });
      expect(ctaButton).toHaveClass('btn-primary');
    });

    it('should link CTA button to signup page', () => {
      render(<HeroSection />);

      const ctaButton = screen.getByRole('link', { name: /무료로 시작하기/i });
      expect(ctaButton).toHaveAttribute('href', '/signup');
    });
  });

  describe('Hero Image', () => {
    it('should render hero image', () => {
      render(<HeroSection />);

      const heroImage = screen.getByRole('img', { name: /제품 미리보기|dashboard/i });
      expect(heroImage).toBeInTheDocument();
    });

    it('should have alt text for accessibility', () => {
      render(<HeroSection />);

      const heroImage = screen.getByRole('img');
      expect(heroImage).toHaveAttribute('alt');
      expect(heroImage.getAttribute('alt')).not.toBe('');
    });
  });

  describe('Design System Compliance', () => {
    it('should use Deep Trust Blue for headline', () => {
      render(<HeroSection />);

      const headline = screen.getByRole('heading', {
        name: /증거 정리 시간 90% 단축/i,
      });
      expect(headline).toHaveClass('text-deep-trust-blue');
    });

    it('should have large font size for headline', () => {
      render(<HeroSection />);

      const headline = screen.getByRole('heading', {
        name: /증거 정리 시간 90% 단축/i,
      });
      // Should be 4xl or larger (48px+)
      expect(headline).toHaveClass('text-5xl');
    });

    it('should have appropriate font weight for headline', () => {
      render(<HeroSection />);

      const headline = screen.getByRole('heading', {
        name: /증거 정리 시간 90% 단축/i,
      });
      expect(headline).toHaveClass('font-bold');
    });

    it('should use proper text color for subheadline', () => {
      render(<HeroSection />);

      const subheadline = screen.getByText(
        /AI가 이혼 소송 증거를 자동 분석하고 초안을 작성합니다/i
      );
      expect(subheadline).toHaveClass('text-gray-600');
    });

    it('should follow 8pt grid spacing', () => {
      const { container } = render(<HeroSection />);

      const section = container.querySelector('section');
      // Padding should be multiples of 8px
      expect(section).toHaveClass('py-20');
    });
  });

  describe('Layout and Structure', () => {
    it('should use semantic section element', () => {
      const { container } = render(<HeroSection />);

      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
    });

    it('should have max-width container', () => {
      const { container } = render(<HeroSection />);

      const innerContainer = container.querySelector('.max-w-7xl');
      expect(innerContainer).toBeInTheDocument();
    });

    it('should center content horizontally', () => {
      const { container } = render(<HeroSection />);

      const innerContainer = container.querySelector('.max-w-7xl');
      expect(innerContainer).toHaveClass('mx-auto');
    });

    it('should use grid layout for content and image', () => {
      const { container } = render(<HeroSection />);

      const gridContainer = container.querySelector('.grid');
      expect(gridContainer).toBeInTheDocument();
    });

    it('should have 2-column layout on desktop', () => {
      const { container } = render(<HeroSection />);

      const gridContainer = container.querySelector('.grid');
      expect(gridContainer).toHaveClass('lg:grid-cols-2');
    });
  });

  describe('Responsive Behavior', () => {
    it('should have mobile-friendly layout', () => {
      const { container } = render(<HeroSection />);

      const gridContainer = container.querySelector('.grid');
      // Should be 1 column on mobile
      expect(gridContainer).toHaveClass('grid-cols-1');
    });

    it('should have proper spacing between elements', () => {
      const { container } = render(<HeroSection />);

      const gridContainer = container.querySelector('.grid');
      expect(gridContainer).toHaveClass('gap-12');
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading hierarchy', () => {
      render(<HeroSection />);

      const headline = screen.getByRole('heading', {
        name: /증거 정리 시간 90% 단축/i,
      });
      // Should be h1
      expect(headline.tagName).toBe('H1');
    });

    it('should have descriptive section label', () => {
      const { container } = render(<HeroSection />);

      const section = container.querySelector('section');
      expect(section).toHaveAttribute('aria-label');
    });
  });

  describe('CTA Prominence', () => {
    it('should have CTA button in prominent position', () => {
      render(<HeroSection />);

      const ctaButton = screen.getByRole('link', { name: /무료로 시작하기/i });
      // Should have large padding for prominence
      expect(ctaButton).toHaveClass('px-8');
      expect(ctaButton).toHaveClass('py-4');
    });

    it('should have large text size for CTA', () => {
      render(<HeroSection />);

      const ctaButton = screen.getByRole('link', { name: /무료로 시작하기/i });
      expect(ctaButton).toHaveClass('text-lg');
    });
  });
});
