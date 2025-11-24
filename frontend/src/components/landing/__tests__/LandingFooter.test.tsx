/**
 * Test for LandingFooter Component
 * Plan 3.19.1 - Footer
 *
 * Requirements:
 * - 3-column layout:
 *   - Left: Company info (logo, address, contact)
 *   - Center: Links (제품/가격/블로그/고객사례/채용)
 *   - Right: Legal notices (이용약관/개인정보처리방침/쿠키정책)
 * - Bottom: Copyright and social media icons
 */

import { render, screen } from '@testing-library/react';
import LandingFooter from '../LandingFooter';

describe('LandingFooter Component', () => {
  describe('Company Information Column', () => {
    it('should render company logo', () => {
      render(<LandingFooter />);

      // Should have logo or company name (multiple instances)
      const companyNames = screen.getAllByText(/LEH|Legal Evidence Hub/i);
      expect(companyNames.length).toBeGreaterThanOrEqual(1);
    });

    it('should render company address', () => {
      render(<LandingFooter />);

      // Should have address information
      expect(screen.getByText(/서울|주소/i)).toBeInTheDocument();
    });

    it('should render contact information', () => {
      render(<LandingFooter />);

      // Should have email or phone contact
      const contactInfo = screen.getAllByText(/contact|support|@|02-|010-/i);
      expect(contactInfo.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Links Column', () => {
    it('should render product link', () => {
      render(<LandingFooter />);

      expect(screen.getByText(/제품/i)).toBeInTheDocument();
    });

    it('should render pricing link', () => {
      render(<LandingFooter />);

      expect(screen.getByText(/가격/i)).toBeInTheDocument();
    });

    it('should render blog link', () => {
      render(<LandingFooter />);

      expect(screen.getByText(/블로그/i)).toBeInTheDocument();
    });

    it('should render customer cases link', () => {
      render(<LandingFooter />);

      expect(screen.getByText(/고객사례/i)).toBeInTheDocument();
    });

    it('should render careers link', () => {
      render(<LandingFooter />);

      expect(screen.getByText(/채용/i)).toBeInTheDocument();
    });
  });

  describe('Legal Notices Column', () => {
    it('should render terms of service link', () => {
      render(<LandingFooter />);

      expect(screen.getByText(/이용약관/i)).toBeInTheDocument();
    });

    it('should render privacy policy link', () => {
      render(<LandingFooter />);

      expect(screen.getByText(/개인정보처리방침/i)).toBeInTheDocument();
    });

    it('should render cookie policy link', () => {
      render(<LandingFooter />);

      expect(screen.getByText(/쿠키정책/i)).toBeInTheDocument();
    });
  });

  describe('Copyright and Social Media', () => {
    it('should render copyright notice', () => {
      render(<LandingFooter />);

      // Should have copyright symbol and year
      expect(screen.getByText(/©|Copyright|2025/i)).toBeInTheDocument();
    });

    it('should render social media icons', () => {
      const { container } = render(<LandingFooter />);

      // Should have social media icon links
      const socialIcons = container.querySelectorAll('svg');
      expect(socialIcons.length).toBeGreaterThanOrEqual(2); // At least 2 social icons
    });

    it('should link to social media profiles', () => {
      const { container } = render(<LandingFooter />);

      // Social links should point to external profiles
      const links = container.querySelectorAll('a[href*="twitter"], a[href*="linkedin"], a[href*="github"]');
      expect(links.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Layout Structure', () => {
    it('should render as a semantic footer element', () => {
      const { container } = render(<LandingFooter />);

      const footer = container.querySelector('footer');
      expect(footer).toBeInTheDocument();
    });

    it('should have grid layout for columns', () => {
      const { container } = render(<LandingFooter />);

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
    });

    it('should use 3-column layout on desktop', () => {
      const { container } = render(<LandingFooter />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('should use responsive grid columns', () => {
      const { container } = render(<LandingFooter />);

      const grid = container.querySelector('.grid');
      // 1 column on mobile, 3 on desktop
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });

    it('should have max-width container', () => {
      const { container } = render(<LandingFooter />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toBeInTheDocument();
    });

    it('should center content horizontally', () => {
      const { container } = render(<LandingFooter />);

      const maxWidthContainer = container.querySelector('.max-w-7xl');
      expect(maxWidthContainer).toHaveClass('mx-auto');
    });
  });

  describe('Column Headers', () => {
    it('should have header for company info section', () => {
      render(<LandingFooter />);

      // Should have "Legal Evidence Hub" heading
      const heading = screen.getByRole('heading', { name: /Legal Evidence Hub/i });
      expect(heading).toBeInTheDocument();
    });

    it('should have header for links section', () => {
      render(<LandingFooter />);

      // Should have "링크" heading
      const heading = screen.getByRole('heading', { name: /링크/i });
      expect(heading).toBeInTheDocument();
    });

    it('should have header for legal section', () => {
      render(<LandingFooter />);

      // Should have "법적 고지" heading
      const heading = screen.getByRole('heading', { name: /법적 고지/i });
      expect(heading).toBeInTheDocument();
    });
  });

  describe('Design System Compliance', () => {
    it('should follow 8pt grid spacing', () => {
      const { container } = render(<LandingFooter />);

      const footer = container.querySelector('footer');
      // Padding should be multiples of 8px
      expect(footer).toHaveClass('py-12');
      expect(footer).toHaveClass('px-6');
    });

    it('should use dark background color', () => {
      const { container } = render(<LandingFooter />);

      const footer = container.querySelector('footer');
      // Footer should have dark background (bg-gray-900 or bg-deep-trust-blue)
      expect(footer).toHaveClass('bg-gray-900');
    });

    it('should use light text on dark background', () => {
      const { container } = render(<LandingFooter />);

      const footer = container.querySelector('footer');
      // Text should be light colored
      const lightText = footer?.querySelectorAll('.text-gray-300, .text-white');
      expect(lightText?.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('Accessibility', () => {
    it('should have semantic footer element', () => {
      const { container } = render(<LandingFooter />);

      const footer = container.querySelector('footer');
      expect(footer?.tagName).toBe('FOOTER');
    });

    it('should have accessible link text', () => {
      render(<LandingFooter />);

      // All links should have meaningful text or aria-label
      const links = screen.getAllByRole('link');
      links.forEach((link) => {
        const hasText = link.textContent && link.textContent.trim().length > 0;
        const hasAriaLabel = link.getAttribute('aria-label');
        expect(hasText || hasAriaLabel).toBeTruthy();
      });
    });

    it('should have aria-labels for social media icons', () => {
      const { container } = render(<LandingFooter />);

      // Social media links should have aria-labels
      const socialLinks = container.querySelectorAll('a[href*="twitter"], a[href*="linkedin"], a[href*="github"]');
      socialLinks.forEach((link) => {
        expect(link).toHaveAttribute('aria-label');
      });
    });
  });

  describe('Visual Presentation', () => {
    it('should have divider between main content and copyright', () => {
      const { container } = render(<LandingFooter />);

      // Should have border or divider
      const footer = container.querySelector('footer');
      const divider = footer?.querySelector('.border-t, .divide-y');
      expect(divider).toBeInTheDocument();
    });

    it('should center-align copyright text', () => {
      const { container } = render(<LandingFooter />);

      // Copyright section should be centered
      const copyrightSection = container.querySelector('.text-center');
      expect(copyrightSection).toBeInTheDocument();
    });

    it('should have consistent spacing within columns', () => {
      const { container } = render(<LandingFooter />);

      const footer = container.querySelector('footer');
      const spacedColumns = footer?.querySelectorAll('.space-y-4');
      expect(spacedColumns?.length).toBeGreaterThanOrEqual(3);
    });
  });

  describe('Responsive Behavior', () => {
    it('should stack columns vertically on mobile', () => {
      const { container } = render(<LandingFooter />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
    });

    it('should display 3 columns on desktop', () => {
      const { container } = render(<LandingFooter />);

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('lg:grid-cols-3');
    });
  });
});
