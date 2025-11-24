/**
 * Test for AITransparencySection Component
 * Plan 3.19.1 - AI Transparency & Security (법률 컴플라이언스 준수)
 *
 * Requirements:
 * - Section title: "법률 컴플라이언스 준수"
 * - 2-column layout:
 *   - Left: AI Transparency
 *     - "모든 AI 결과는 근거 증거 표시"
 *     - "최종 결정은 변호사님께"
 *   - Right: Security & Compliance
 *     - AES-256 암호화
 *     - PIPA(개인정보보호법) 준수
 *     - ISO 27001 인증 (준비 중)
 * - Trust badge icons (lock, shield)
 */

import { render, screen } from '@testing-library/react';
import AITransparencySection from '../AITransparencySection';

describe('AITransparencySection Component', () => {
  describe('Section Title', () => {
    it('should render the section title', () => {
      render(<AITransparencySection />);

      const title = screen.getByRole('heading', { name: /법률 컴플라이언스 준수/i });
      expect(title).toBeInTheDocument();
    });

    it('should style title with Deep Trust Blue', () => {
      render(<AITransparencySection />);

      const title = screen.getByRole('heading', { name: /법률 컴플라이언스 준수/i });
      expect(title).toHaveClass('text-deep-trust-blue');
    });

    it('should use appropriate heading level (h2)', () => {
      render(<AITransparencySection />);

      const title = screen.getByRole('heading', { name: /법률 컴플라이언스 준수/i });
      expect(title.tagName).toBe('H2');
    });
  });

  describe('AI Transparency Column', () => {
    it('should render AI Transparency heading', () => {
      render(<AITransparencySection />);

      const heading = screen.getByRole('heading', { name: /AI 투명성/i });
      expect(heading).toBeInTheDocument();
    });

    it('should render evidence display message', () => {
      render(<AITransparencySection />);

      expect(screen.getByText(/모든 AI 결과는 근거 증거 표시/i)).toBeInTheDocument();
    });

    it('should render lawyer decision message', () => {
      render(<AITransparencySection />);

      expect(screen.getByText(/최종 결정은 변호사님께/i)).toBeInTheDocument();
    });

    it('should use h3 for AI Transparency heading', () => {
      render(<AITransparencySection />);

      const heading = screen.getByRole('heading', { name: /AI 투명성/i });
      expect(heading.tagName).toBe('H3');
    });
  });

  describe('Security & Compliance Column', () => {
    it('should render Security heading', () => {
      render(<AITransparencySection />);

      const heading = screen.getByRole('heading', { name: /보안 및 규정 준수/i });
      expect(heading).toBeInTheDocument();
    });

    it('should render AES-256 encryption message', () => {
      render(<AITransparencySection />);

      expect(screen.getByText(/AES-256 암호화/i)).toBeInTheDocument();
    });

    it('should render PIPA compliance message', () => {
      render(<AITransparencySection />);

      expect(screen.getByText(/PIPA\(개인정보보호법\) 준수/i)).toBeInTheDocument();
    });

    it('should render ISO 27001 certification message', () => {
      render(<AITransparencySection />);

      expect(screen.getByText(/ISO 27001 인증 \(준비 중\)/i)).toBeInTheDocument();
    });

    it('should use h3 for Security heading', () => {
      render(<AITransparencySection />);

      const heading = screen.getByRole('heading', { name: /보안 및 규정 준수/i });
      expect(heading.tagName).toBe('H3');
    });
  });

  describe('Trust Badge Icons', () => {
    it('should render icons for trust badges', () => {
      const { container } = render(<AITransparencySection />);

      // Should have icons (lock, shield, etc.)
      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThanOrEqual(2);
    });

    it('should use consistent icon sizes', () => {
      const { container } = render(<AITransparencySection />);

      const icons = container.querySelectorAll('svg');
      // Icons should have w-6 h-6 or similar sizing
      for (let i = 0; i < Math.min(2, icons.length); i++) {
        expect(icons[i]).toHaveClass('w-6');
        expect(icons[i]).toHaveClass('h-6');
      }
    });

    it('should style icons with accent color', () => {
      const { container } = render(<AITransparencySection />);

      const icons = container.querySelectorAll('svg');
      for (let i = 0; i < Math.min(2, icons.length); i++) {
        expect(icons[i]).toHaveClass('text-accent');
      }
    });
  });

  describe('Layout Structure', () => {
    it('should render as a semantic section element', () => {
      const { container } = render(<AITransparencySection />);

      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
    });

    it('should have grid layout for columns', () => {
      const { container } = render(<AITransparencySection />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
    });

    it('should use 2-column layout on desktop', () => {
      const { container } = render(<AITransparencySection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-2');
    });

    it('should use responsive grid columns', () => {
      const { container } = render(<AITransparencySection />);

      const grid = container.querySelector('.grid');
      // 1 column on mobile, 2 on desktop
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('lg:grid-cols-2');
    });

    it('should have appropriate spacing between columns', () => {
      const { container } = render(<AITransparencySection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('gap-12');
    });

    it('should have max-width container', () => {
      const { container } = render(<AITransparencySection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toBeInTheDocument();
    });

    it('should center content horizontally', () => {
      const { container } = render(<AITransparencySection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toHaveClass('mx-auto');
    });
  });

  describe('Design System Compliance', () => {
    it('should follow 8pt grid spacing', () => {
      const { container } = render(<AITransparencySection />);

      const section = container.querySelector('section');
      // Padding should be multiples of 8px
      expect(section).toHaveClass('py-20');
      expect(section).toHaveClass('px-6');
    });

    it('should use calm background color', () => {
      const { container } = render(<AITransparencySection />);

      const section = container.querySelector('section');
      expect(section).toHaveClass('bg-calm-grey');
    });

    it('should use Deep Trust Blue for headings', () => {
      render(<AITransparencySection />);

      const headings = screen.getAllByRole('heading', { level: 3 });
      headings.forEach((heading) => {
        expect(heading).toHaveClass('text-deep-trust-blue');
      });
    });

    it('should use gray text for feature descriptions', () => {
      render(<AITransparencySection />);

      const features = [
        screen.getByText(/모든 AI 결과는 근거 증거 표시/i),
        screen.getByText(/최종 결정은 변호사님께/i),
        screen.getByText(/AES-256 암호화/i),
      ];

      features.forEach((feature) => {
        expect(feature).toHaveClass('text-gray-600');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have aria-label for section', () => {
      const { container } = render(<AITransparencySection />);

      const section = container.querySelector('section');
      expect(section).toHaveAttribute('aria-label', 'AI 투명성 및 보안');
    });

    it('should have proper heading hierarchy', () => {
      render(<AITransparencySection />);

      const mainHeading = screen.getByRole('heading', { name: /법률 컴플라이언스 준수/i });
      expect(mainHeading.tagName).toBe('H2');

      const subHeadings = screen.getAllByRole('heading', { level: 3 });
      expect(subHeadings.length).toBe(2);
    });

    it('should have aria-labels for icons', () => {
      const { container } = render(<AITransparencySection />);

      const icons = container.querySelectorAll('svg');
      // Icons should have aria-labels
      icons.forEach((icon) => {
        expect(icon).toHaveAttribute('aria-label');
      });
    });
  });

  describe('Responsive Behavior', () => {
    it('should stack columns vertically on mobile', () => {
      const { container } = render(<AITransparencySection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
    });

    it('should display 2 columns on desktop', () => {
      const { container } = render(<AITransparencySection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-2');
    });
  });

  describe('Visual Presentation', () => {
    it('should have consistent spacing within columns', () => {
      const { container } = render(<AITransparencySection />);

      const section = container.querySelector('section');
      const spacedColumns = section?.querySelectorAll('.space-y-6');
      expect(spacedColumns?.length).toBeGreaterThanOrEqual(2);
    });

    it('should display features as a list', () => {
      const { container } = render(<AITransparencySection />);

      const section = container.querySelector('section');
      const featureLists = section?.querySelectorAll('.space-y-4');
      expect(featureLists?.length).toBeGreaterThanOrEqual(2);
    });
  });
});
