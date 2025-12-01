/**
 * Plan 3.19.2 - Accessibility Tests
 *
 * Tests for WCAG 2.1 AA compliance:
 * - Semantic HTML (section, article, nav)
 * - ARIA labels for CTA buttons
 * - Focus visible for keyboard navigation
 * - Color contrast ratio ≥ 4.5:1
 *
 * Test Strategy:
 * 1. RED: Write failing tests for accessibility features
 * 2. GREEN: Implement accessibility improvements
 * 3. REFACTOR: Clean up while keeping tests green
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Import components
import LandingNav from '../../components/landing/LandingNav';
import HeroSection from '../../components/landing/HeroSection';
import SolutionSection from '../../components/landing/SolutionSection';
import PricingSection from '../../components/landing/PricingSection';
import FinalCTASection from '../../components/landing/FinalCTASection';
import LandingFooter from '../../components/landing/LandingFooter';

// Mock next/image
jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: any) => {
    const { fill, priority, ...imgProps } = props;
    return <img {...imgProps} />;
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

describe('Plan 3.19.2 - Accessibility (WCAG 2.1 AA)', () => {
  describe('Semantic HTML Structure', () => {
    test('LandingNav should use semantic <nav> element', () => {
      const { container } = render(<LandingNav />);
      const nav = container.querySelector('nav');
      expect(nav).toBeInTheDocument();
    });

    test('LandingNav should have aria-label for screen readers', () => {
      render(<LandingNav />);
      const nav = screen.getByRole('navigation');
      expect(nav).toHaveAttribute('aria-label');
    });

    test('HeroSection should use semantic <section> element with aria-label', () => {
      const { container } = render(<HeroSection />);
      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
      expect(section).toHaveAttribute('aria-label');
    });

    test('SolutionSection should use semantic <section> element with aria-label', () => {
      const { container } = render(<SolutionSection />);
      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
      expect(section).toHaveAttribute('aria-label');
    });

    test('PricingSection should use semantic <section> element with aria-label', () => {
      const { container } = render(<PricingSection />);
      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
      expect(section).toHaveAttribute('aria-label');
    });

    test('FinalCTASection should use semantic <section> element with aria-label', () => {
      const { container } = render(<FinalCTASection />);
      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
      expect(section).toHaveAttribute('aria-label');
    });

    test('LandingFooter should use semantic <footer> element', () => {
      const { container } = render(<LandingFooter />);
      const footer = container.querySelector('footer');
      expect(footer).toBeInTheDocument();
    });
  });

  describe('ARIA Labels for CTA Buttons', () => {
    /**
     * RED TEST - CTA buttons should have descriptive aria-labels
     * for better screen reader experience
     */
    test('HeroSection primary CTA should have aria-label', () => {
      const { container } = render(<HeroSection />);

      // Find the primary CTA button (Button primitive with aria-label)
      const primaryCTA = container.querySelector('button.bg-primary');
      expect(primaryCTA).toBeInTheDocument();
      expect(primaryCTA).toHaveAttribute('aria-label');
    });

    test('FinalCTASection primary CTA should have aria-label', () => {
      const { container } = render(<FinalCTASection />);

      // Find the primary CTA button (Button primitive with aria-label on Link)
      const primaryLink = container.querySelector('a[href="/signup"]');
      expect(primaryLink).toBeInTheDocument();
      expect(primaryLink).toHaveAttribute('aria-label');
    });

    test('FinalCTASection secondary CTA should have aria-label', () => {
      const { container } = render(<FinalCTASection />);

      // Find the secondary CTA (mailto link)
      const secondaryCTA = container.querySelector('a[href^="mailto:"]');
      expect(secondaryCTA).toBeInTheDocument();
      expect(secondaryCTA).toHaveAttribute('aria-label');
    });

    test('LandingNav free trial CTA should have aria-label', () => {
      const { container } = render(<LandingNav />);

      const ctaButton = container.querySelector('a.btn-primary');
      expect(ctaButton).toBeInTheDocument();
      expect(ctaButton).toHaveAttribute('aria-label');
    });

    test('PricingSection CTA buttons should have aria-labels', () => {
      const { container } = render(<PricingSection />);

      // Find all CTA buttons in pricing cards
      const ctaButtons = container.querySelectorAll('a[href="/signup"]');
      expect(ctaButtons.length).toBeGreaterThan(0);

      ctaButtons.forEach((button) => {
        expect(button).toHaveAttribute('aria-label');
      });
    });
  });

  describe('Focus Visible for Keyboard Navigation', () => {
    /**
     * RED TEST - Interactive elements should have focus-visible styles
     * Tailwind class: focus-visible:ring-2 focus-visible:ring-offset-2
     */
    test('HeroSection CTA should have focus-visible styles', () => {
      const { container } = render(<HeroSection />);

      // Button primitive has focus-visible styles
      const primaryCTA = container.querySelector('button.bg-primary');
      expect(primaryCTA).toBeInTheDocument();

      // Check for focus-visible classes
      const className = primaryCTA?.className || '';
      expect(className).toMatch(/focus-visible:/);
    });

    test('LandingNav links should have focus-visible styles', () => {
      const { container } = render(<LandingNav />);

      // Navigation links
      const navLinks = container.querySelectorAll('nav a');
      expect(navLinks.length).toBeGreaterThan(0);

      // At least the CTA button should have focus-visible
      const ctaButton = container.querySelector('a.btn-primary');
      expect(ctaButton?.className).toMatch(/focus-visible:/);
    });

    test('FinalCTASection buttons should have focus-visible styles', () => {
      const { container } = render(<FinalCTASection />);

      // Button primitive has focus-visible styles
      const primaryCTA = container.querySelector('button.bg-primary');
      expect(primaryCTA).toBeInTheDocument();
      expect(primaryCTA?.className).toMatch(/focus-visible:/);
    });
  });

  describe('Color Contrast (WCAG AA ≥ 4.5:1)', () => {
    /**
     * Verify that components use design tokens with sufficient contrast:
     * - Deep Trust Blue (#2C3E50) on white/calm-grey: 10.69:1 ✓
     * - Accent (#1ABC9C) on white: 2.86:1 (fail for text, ok for large text)
     * - White on Accent: 2.86:1 (needs dark variant for small text)
     */

    test('Headings should use deep-trust-blue for high contrast', () => {
      const { container } = render(<HeroSection />);

      const heading = container.querySelector('h1');
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveClass('text-secondary');
    });

    test('SolutionSection headings should use deep-trust-blue', () => {
      const { container } = render(<SolutionSection />);

      const mainHeading = container.querySelector('h2');
      expect(mainHeading).toHaveClass('text-secondary');

      const cardHeadings = container.querySelectorAll('h3');
      cardHeadings.forEach((h3) => {
        expect(h3).toHaveClass('text-secondary');
      });
    });

    test('PricingSection headings should use deep-trust-blue', () => {
      const { container } = render(<PricingSection />);

      const mainHeading = container.querySelector('h2');
      expect(mainHeading).toHaveClass('text-secondary');
    });

    test('Body text should use gray-600 or darker for contrast', () => {
      const { container } = render(<HeroSection />);

      const paragraph = container.querySelector('p');
      expect(paragraph).toBeInTheDocument();

      // Should use gray-600 (which has sufficient contrast on light bg)
      expect(paragraph).toHaveClass('text-neutral-600');
    });
  });

  describe('Skip Navigation Link', () => {
    /**
     * RED TEST - Landing page should have skip-to-content link
     * for keyboard users to bypass navigation
     */
    test('should have skip navigation link as first focusable element', () => {
      // This test will need to be run on the full page component
      // For now, we'll verify the nav has proper structure
      const { container } = render(<LandingNav />);

      // Skip link should be visually hidden but accessible
      const skipLink = container.querySelector('a[href="#main-content"]');

      // This will FAIL initially - we need to implement skip link
      expect(skipLink).toBeInTheDocument();
    });
  });

  describe('Image Accessibility', () => {
    test('All images should have alt attributes', () => {
      const { container } = render(<HeroSection />);

      const images = container.querySelectorAll('img');
      images.forEach((img) => {
        expect(img).toHaveAttribute('alt');
        expect(img.getAttribute('alt')).not.toBe('');
      });
    });

    test('LandingNav logo should have meaningful alt text', () => {
      const { container } = render(<LandingNav />);

      const logo = container.querySelector('img');
      if (logo) {
        expect(logo).toHaveAttribute('alt');
        expect(logo.getAttribute('alt')).not.toBe('');
      }
    });

    test('Decorative icons should have aria-hidden or aria-label', () => {
      const { container } = render(<SolutionSection />);

      // SVG icons from lucide-react
      const svgIcons = container.querySelectorAll('svg');
      svgIcons.forEach((svg) => {
        // Should either have aria-hidden="true" or aria-label
        const hasAriaHidden = svg.getAttribute('aria-hidden') === 'true';
        const hasAriaLabel = svg.hasAttribute('aria-label');
        expect(hasAriaHidden || hasAriaLabel).toBe(true);
      });
    });
  });

  describe('Heading Hierarchy', () => {
    test('HeroSection should have h1 as the main heading', () => {
      const { container } = render(<HeroSection />);

      const h1 = container.querySelector('h1');
      expect(h1).toBeInTheDocument();
    });

    test('Section components should use h2 for section titles', () => {
      const solutionContainer = render(<SolutionSection />).container;
      const pricingContainer = render(<PricingSection />).container;
      const ctaContainer = render(<FinalCTASection />).container;

      expect(solutionContainer.querySelector('h2')).toBeInTheDocument();
      expect(pricingContainer.querySelector('h2')).toBeInTheDocument();
      expect(ctaContainer.querySelector('h2')).toBeInTheDocument();
    });

    test('Card titles should use h3 for proper hierarchy', () => {
      const { container } = render(<SolutionSection />);

      const h3Elements = container.querySelectorAll('h3');
      expect(h3Elements.length).toBeGreaterThan(0);
    });
  });
});
