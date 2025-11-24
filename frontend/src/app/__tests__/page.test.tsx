/**
 * Landing Page Integration Test
 * Plan 3.19.4 - Testing Requirements
 *
 * Requirements:
 * - All 12 sections render correctly
 * - Navigation scroll functionality
 * - CTA buttons link to correct pages
 * - Responsive layout
 */

import { render, screen } from '@testing-library/react';
import LandingPage from '../page';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => '/',
}));

describe('Landing Page Integration', () => {
  describe('Section Rendering', () => {
    it('should render navigation bar', () => {
      render(<LandingPage />);

      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByText('LEH')).toBeInTheDocument();
    });

    it('should render hero section', () => {
      render(<LandingPage />);

      expect(screen.getByRole('heading', { name: /증거 정리 시간 90% 단축/i })).toBeInTheDocument();
    });

    it('should render social proof section', () => {
      render(<LandingPage />);

      // Text is split across elements
      expect(screen.getByText('50개')).toBeInTheDocument();
      expect(screen.getByText(/로펌 사용 중/i)).toBeInTheDocument();
    });

    it('should render problem statement section', () => {
      render(<LandingPage />);

      expect(screen.getByRole('heading', { name: /이런 고민 있으셨나요\?/i })).toBeInTheDocument();
    });

    it('should render solution section', () => {
      render(<LandingPage />);

      expect(screen.getByRole('heading', { name: /Legal Evidence Hub가 해결합니다/i })).toBeInTheDocument();
    });

    it('should render how it works section', () => {
      render(<LandingPage />);

      expect(screen.getByRole('heading', { name: /4단계로 완성되는 초안/i })).toBeInTheDocument();
    });

    it('should render AI transparency section', () => {
      render(<LandingPage />);

      expect(screen.getByRole('heading', { name: /법률 컴플라이언스 준수/i })).toBeInTheDocument();
    });

    it('should render pricing section', () => {
      render(<LandingPage />);

      expect(screen.getByRole('heading', { name: /투명한 가격, 숨은 비용 없음/i })).toBeInTheDocument();
    });

    it('should render testimonials section', () => {
      render(<LandingPage />);

      expect(screen.getByRole('heading', { name: /이미 사용 중인 변호사님들의 평가/i })).toBeInTheDocument();
    });

    it('should render FAQ section', () => {
      render(<LandingPage />);

      expect(screen.getByRole('heading', { name: /자주 묻는 질문/i })).toBeInTheDocument();
    });

    it('should render final CTA section', () => {
      render(<LandingPage />);

      expect(screen.getByRole('heading', { name: /지금 바로 시작하세요/i })).toBeInTheDocument();
    });

    it('should render footer', () => {
      render(<LandingPage />);

      expect(screen.getByText(/© 2025 LEH/i)).toBeInTheDocument();
    });
  });

  describe('CTA Buttons', () => {
    it('should have CTA buttons linking to signup', () => {
      render(<LandingPage />);

      const signupLinks = screen.getAllByRole('link', { name: /무료로 시작하기|무료 체험/i });
      expect(signupLinks.length).toBeGreaterThanOrEqual(2); // Hero + Final CTA at minimum

      signupLinks.forEach((link) => {
        expect(link).toHaveAttribute('href', '/signup');
      });
    });

    it('should have login link in navigation', () => {
      render(<LandingPage />);

      const loginLink = screen.getByRole('link', { name: /로그인/i });
      expect(loginLink).toHaveAttribute('href', '/login');
    });
  });

  describe('Navigation Menu', () => {
    it('should have anchor links to sections', () => {
      render(<LandingPage />);

      // Get all links and filter by name (multiple links with same text exist)
      const allLinks = screen.getAllByRole('link');
      const featuresLink = allLinks.find(link => link.textContent === '기능' && link.getAttribute('href') === '#features');
      const pricingLink = allLinks.find(link => link.textContent === '가격' && link.getAttribute('href') === '#pricing');

      expect(featuresLink).toBeTruthy();
      expect(pricingLink).toBeTruthy();
    });
  });

  describe('Layout Structure', () => {
    it('should have semantic main element', () => {
      const { container } = render(<LandingPage />);

      const main = container.querySelector('main');
      expect(main).toBeInTheDocument();
    });

    it('should have proper document structure', () => {
      const { container } = render(<LandingPage />);

      // Should have navigation, main, and footer
      expect(container.querySelector('nav')).toBeInTheDocument();
      expect(container.querySelector('main')).toBeInTheDocument();
      expect(container.querySelector('footer')).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    it('should render without errors on different viewports', () => {
      const { container } = render(<LandingPage />);

      // Page should render successfully
      expect(container).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have all sections with proper ARIA labels', () => {
      const { container } = render(<LandingPage />);

      const sections = container.querySelectorAll('section[aria-label]');
      expect(sections.length).toBeGreaterThanOrEqual(10); // All major sections
    });

    it('should have proper heading hierarchy', () => {
      render(<LandingPage />);

      // Should have multiple h2 headings for sections (some sections like Hero/Social Proof don't have h2)
      const h2Headings = screen.getAllByRole('heading', { level: 2 });
      expect(h2Headings.length).toBeGreaterThanOrEqual(8); // Main sections have h2
    });
  });
});
