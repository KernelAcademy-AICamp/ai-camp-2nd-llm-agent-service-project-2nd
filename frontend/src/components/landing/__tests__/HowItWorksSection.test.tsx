/**
 * Test for HowItWorksSection Component
 * Plan 3.19.1 - How It Works (4단계 프로세스)
 *
 * Requirements:
 * - Section title: "4단계로 완성되는 초안"
 * - Step-by-step flow with 4 steps:
 *   1️⃣ 증거 업로드 (드래그 앤 드롭)
 *   2️⃣ AI 자동 분석 (OCR, STT, 감정 분석)
 *   3️⃣ 타임라인 검토 (증거 확인)
 *   4️⃣ 초안 다운로드 (HWP/DOCX)
 * - Each step: number badge, icon, title, description
 * - Visual flow with arrows/connectors
 */

import { render, screen } from '@testing-library/react';
import HowItWorksSection from '../HowItWorksSection';

describe('HowItWorksSection Component', () => {
  describe('Section Title', () => {
    it('should render the section title', () => {
      render(<HowItWorksSection />);

      const title = screen.getByRole('heading', { name: /4단계로 완성되는 초안/i });
      expect(title).toBeInTheDocument();
    });

    it('should style title with Deep Trust Blue', () => {
      render(<HowItWorksSection />);

      const title = screen.getByRole('heading', { name: /4단계로 완성되는 초안/i });
      expect(title).toHaveClass('text-secondary');
    });

    it('should use appropriate heading level (h2)', () => {
      render(<HowItWorksSection />);

      const title = screen.getByRole('heading', { name: /4단계로 완성되는 초안/i });
      expect(title.tagName).toBe('H2');
    });
  });

  describe('Step 1: Evidence Upload', () => {
    it('should render step number', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText('1')).toBeInTheDocument();
    });

    it('should render step title', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText(/증거 업로드/i)).toBeInTheDocument();
    });

    it('should render step description', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText(/드래그 앤 드롭/i)).toBeInTheDocument();
    });
  });

  describe('Step 2: AI Analysis', () => {
    it('should render step number', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('should render step title', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText(/AI 자동 분석/i)).toBeInTheDocument();
    });

    it('should render step description', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText(/OCR, STT, 감정 분석/i)).toBeInTheDocument();
    });
  });

  describe('Step 3: Timeline Review', () => {
    it('should render step number', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText('3')).toBeInTheDocument();
    });

    it('should render step title', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText(/타임라인 검토/i)).toBeInTheDocument();
    });

    it('should render step description', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText(/증거 확인/i)).toBeInTheDocument();
    });
  });

  describe('Step 4: Draft Download', () => {
    it('should render step number', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText('4')).toBeInTheDocument();
    });

    it('should render step title', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText(/초안 다운로드/i)).toBeInTheDocument();
    });

    it('should render step description', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText(/HWP\/DOCX/i)).toBeInTheDocument();
    });
  });

  describe('Step Number Badges', () => {
    it('should render all 4 step number badges', () => {
      render(<HowItWorksSection />);

      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
      expect(screen.getByText('4')).toBeInTheDocument();
    });

    it('should style step numbers with accent color', () => {
      const { container } = render(<HowItWorksSection />);

      // Step numbers should have accent background
      const stepBadges = container.querySelectorAll('.bg-accent');
      expect(stepBadges.length).toBeGreaterThanOrEqual(4);
    });

    it('should make step numbers circular', () => {
      const { container } = render(<HowItWorksSection />);

      // Step badges should be circular (rounded-full)
      const stepBadges = container.querySelectorAll('.rounded-full');
      expect(stepBadges.length).toBeGreaterThanOrEqual(4);
    });
  });

  describe('Icons', () => {
    it('should render icons for each step', () => {
      const { container } = render(<HowItWorksSection />);

      // Should have 4 icons (one per step)
      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThanOrEqual(4);
    });

    it('should use consistent icon sizes', () => {
      const { container } = render(<HowItWorksSection />);

      const icons = container.querySelectorAll('svg');
      // At least the first 4 icons should have consistent sizing
      for (let i = 0; i < Math.min(4, icons.length); i++) {
        expect(icons[i]).toHaveClass('w-8');
        expect(icons[i]).toHaveClass('h-8');
      }
    });

    it('should style icons with Deep Trust Blue', () => {
      const { container } = render(<HowItWorksSection />);

      const icons = container.querySelectorAll('svg');
      // At least the first 4 icons should use Deep Trust Blue
      for (let i = 0; i < Math.min(4, icons.length); i++) {
        expect(icons[i]).toHaveClass('text-secondary');
      }
    });
  });

  describe('Layout Structure', () => {
    it('should render as a semantic section element', () => {
      const { container } = render(<HowItWorksSection />);

      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
    });

    it('should have grid layout for steps', () => {
      const { container } = render(<HowItWorksSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
    });

    it('should use 4-column layout on desktop', () => {
      const { container } = render(<HowItWorksSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-4');
    });

    it('should use responsive grid columns', () => {
      const { container } = render(<HowItWorksSection />);

      const grid = container.querySelector('.grid');
      // 1 column on mobile, 2 on tablet, 4 on desktop
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('md:grid-cols-2');
      expect(grid).toHaveClass('lg:grid-cols-4');
    });

    it('should have appropriate spacing between steps', () => {
      const { container } = render(<HowItWorksSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('gap-8');
    });

    it('should have max-width container', () => {
      const { container } = render(<HowItWorksSection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toBeInTheDocument();
    });

    it('should center content horizontally', () => {
      const { container } = render(<HowItWorksSection />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toHaveClass('mx-auto');
    });
  });

  describe('Design System Compliance', () => {
    it('should follow 8pt grid spacing', () => {
      const { container } = render(<HowItWorksSection />);

      const section = container.querySelector('section');
      // Padding should be multiples of 8px
      expect(section).toHaveClass('py-20');
      expect(section).toHaveClass('px-6');
    });

    it('should use white background color', () => {
      const { container } = render(<HowItWorksSection />);

      const section = container.querySelector('section');
      expect(section).toHaveClass('bg-white');
    });

    it('should use appropriate text colors for step titles', () => {
      const { container } = render(<HowItWorksSection />);

      // Step titles should use Deep Trust Blue
      const section = container.querySelector('section');
      const titles = section?.querySelectorAll('.text-secondary');
      expect(titles?.length).toBeGreaterThanOrEqual(5); // Section title + 4 step titles
    });

    it('should use gray text for descriptions', () => {
      render(<HowItWorksSection />);

      const descriptions = [
        screen.getByText(/드래그 앤 드롭/i),
        screen.getByText(/OCR, STT, 감정 분석/i),
        screen.getByText(/증거 확인/i),
        screen.getByText(/HWP\/DOCX/i),
      ];

      descriptions.forEach((desc) => {
        expect(desc).toHaveClass('text-neutral-600');
      });
    });
  });

  describe('Accessibility', () => {
    it('should have aria-label for section', () => {
      const { container } = render(<HowItWorksSection />);

      const section = container.querySelector('section');
      expect(section).toHaveAttribute('aria-label', '사용 방법 4단계');
    });

    it('should have proper heading hierarchy', () => {
      render(<HowItWorksSection />);

      const mainHeading = screen.getByRole('heading', { name: /4단계로 완성되는 초안/i });
      expect(mainHeading.tagName).toBe('H2');
    });

    it('should have step titles as h3 headings', () => {
      render(<HowItWorksSection />);

      const stepHeadings = screen.getAllByRole('heading', { level: 3 });
      expect(stepHeadings.length).toBe(4);
    });

    it('should have aria-labels for icons', () => {
      const { container } = render(<HowItWorksSection />);

      const icons = container.querySelectorAll('svg');
      // At least the first 4 step icons should have aria-labels
      for (let i = 0; i < Math.min(4, icons.length); i++) {
        expect(icons[i]).toHaveAttribute('aria-label');
      }
    });
  });

  describe('Responsive Behavior', () => {
    it('should stack steps vertically on mobile', () => {
      const { container } = render(<HowItWorksSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
    });

    it('should display 2 columns on tablet', () => {
      const { container } = render(<HowItWorksSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('md:grid-cols-2');
    });

    it('should display 4 columns on desktop', () => {
      const { container } = render(<HowItWorksSection />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-4');
    });
  });

  describe('Visual Presentation', () => {
    it('should center-align content in step cards', () => {
      const { container } = render(<HowItWorksSection />);

      const section = container.querySelector('section');
      const centeredSteps = section?.querySelectorAll('.text-center');
      expect(centeredSteps?.length).toBeGreaterThanOrEqual(4);
    });

    it('should have consistent spacing within steps', () => {
      const { container } = render(<HowItWorksSection />);

      const section = container.querySelector('section');
      const spacedSteps = section?.querySelectorAll('.space-y-4');
      expect(spacedSteps?.length).toBeGreaterThanOrEqual(4);
    });
  });
});
