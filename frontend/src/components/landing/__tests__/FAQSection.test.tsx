/**
 * Test for FAQSection Component
 * Plan 3.19.1 - FAQ (우려 해소)
 *
 * Requirements:
 * - Section title: "자주 묻는 질문"
 * - Accordion format (click to expand)
 * - 5 FAQ items:
 *   1. "AI가 생성한 초안은 법적 효력이 있나요?"
 *   2. "개인정보는 안전하게 보호되나요?"
 *   3. "기존 시스템과 연동 가능한가요?"
 *   4. "환불 정책은 어떻게 되나요?"
 *   5. "어떤 파일 형식을 지원하나요?"
 * - Answers: concise and clear (2-3 sentences)
 * - Expandable/collapsible behavior
 */

import { render, screen, fireEvent } from '@testing-library/react';
import FAQSection from '../FAQSection';

describe('FAQSection Component', () => {
  describe('Section Title', () => {
    it('should render the section title', () => {
      render(<FAQSection />);

      const title = screen.getByRole('heading', { name: /자주 묻는 질문/i });
      expect(title).toBeInTheDocument();
    });

    it('should style title with Deep Trust Blue', () => {
      render(<FAQSection />);

      const title = screen.getByRole('heading', { name: /자주 묻는 질문/i });
      expect(title).toHaveClass('text-deep-trust-blue');
    });

    it('should use appropriate heading level (h2)', () => {
      render(<FAQSection />);

      const title = screen.getByRole('heading', { name: /자주 묻는 질문/i });
      expect(title.tagName).toBe('H2');
    });
  });

  describe('FAQ Questions', () => {
    it('should render question about legal validity of AI drafts', () => {
      render(<FAQSection />);

      expect(screen.getByText(/AI가 생성한 초안은 법적 효력이 있나요\?/i)).toBeInTheDocument();
    });

    it('should render question about privacy protection', () => {
      render(<FAQSection />);

      expect(screen.getByText(/개인정보는 안전하게 보호되나요\?/i)).toBeInTheDocument();
    });

    it('should render question about system integration', () => {
      render(<FAQSection />);

      expect(screen.getByText(/기존 시스템과 연동 가능한가요\?/i)).toBeInTheDocument();
    });

    it('should render question about refund policy', () => {
      render(<FAQSection />);

      expect(screen.getByText(/환불 정책은 어떻게 되나요\?/i)).toBeInTheDocument();
    });

    it('should render question about supported file formats', () => {
      render(<FAQSection />);

      expect(screen.getByText(/어떤 파일 형식을 지원하나요\?/i)).toBeInTheDocument();
    });
  });

  describe('Accordion Behavior', () => {
    it('should have clickable FAQ items', () => {
      render(<FAQSection />);

      const firstQuestion = screen.getByText(/AI가 생성한 초안은 법적 효력이 있나요\?/i);
      const button = firstQuestion.closest('button');
      expect(button).toBeInTheDocument();
    });

    it('should initially hide answers', () => {
      const { container } = render(<FAQSection />);

      // Answers should be hidden initially (not visible or height 0)
      const section = container.querySelector('section');
      const hiddenContent = section?.querySelectorAll('.hidden, .max-h-0, .h-0');
      expect(hiddenContent?.length).toBeGreaterThanOrEqual(1);
    });

    it('should expand answer when question is clicked', () => {
      render(<FAQSection />);

      const firstQuestion = screen.getByText(/AI가 생성한 초안은 법적 효력이 있나요\?/i);
      const button = firstQuestion.closest('button');

      // Click to expand
      if (button) {
        fireEvent.click(button);
      }

      // Answer should now be visible
      expect(screen.getByText(/AI는 초안 작성을 보조하는 도구/i)).toBeInTheDocument();
    });

    it('should toggle answer visibility on multiple clicks', () => {
      const { container } = render(<FAQSection />);

      const firstQuestion = screen.getByText(/AI가 생성한 초안은 법적 효력이 있나요\?/i);
      const button = firstQuestion.closest('button');

      if (button) {
        // Click to expand
        fireEvent.click(button);

        // Answer should be visible
        const answer = screen.getByText(/AI는 초안 작성을 보조하는 도구/i);
        expect(answer).toBeInTheDocument();

        // Click to collapse
        fireEvent.click(button);

        // Answer should be hidden again (check parent has hiding class)
        const answerParent = answer.parentElement;
        expect(answerParent?.classList.contains('hidden') || answerParent?.classList.contains('max-h-0')).toBe(true);
      }
    });
  });

  describe('FAQ Answers', () => {
    it('should display answer about AI draft validity', () => {
      render(<FAQSection />);

      const question = screen.getByText(/AI가 생성한 초안은 법적 효력이 있나요\?/i);
      const button = question.closest('button');
      if (button) fireEvent.click(button);

      expect(screen.getByText(/AI는 초안 작성을 보조하는 도구/i)).toBeInTheDocument();
    });

    it('should display answer about privacy protection', () => {
      render(<FAQSection />);

      const question = screen.getByText(/개인정보는 안전하게 보호되나요\?/i);
      const button = question.closest('button');
      if (button) fireEvent.click(button);

      expect(screen.getByText(/AES-256 암호화|개인정보보호법|PIPA/i)).toBeInTheDocument();
    });
  });

  describe('Accordion Icons', () => {
    it('should render chevron icons for each FAQ item', () => {
      const { container } = render(<FAQSection />);

      // Should have chevron icons (5 FAQ items)
      const icons = container.querySelectorAll('svg');
      expect(icons.length).toBeGreaterThanOrEqual(5);
    });

    it('should rotate icon when expanded', () => {
      const { container } = render(<FAQSection />);

      const firstQuestion = screen.getByText(/AI가 생성한 초안은 법적 효력이 있나요\?/i);
      const button = firstQuestion.closest('button');

      if (button) {
        // Get icon before click
        const icon = button.querySelector('svg');
        const initialClasses = icon?.className;

        // Click to expand
        fireEvent.click(button);

        // Icon should rotate (have rotate-180 class or similar)
        const rotatedIcon = button.querySelector('svg');
        expect(rotatedIcon?.classList.contains('rotate-180') || rotatedIcon?.className !== initialClasses).toBe(true);
      }
    });
  });

  describe('Layout Structure', () => {
    it('should render as a semantic section element', () => {
      const { container } = render(<FAQSection />);

      const section = container.querySelector('section');
      expect(section).toBeInTheDocument();
    });

    it('should render FAQ items in a list-like structure', () => {
      const { container } = render(<FAQSection />);

      // Should have container for FAQ items
      const section = container.querySelector('section');
      const faqContainer = section?.querySelector('.space-y-4, .divide-y');
      expect(faqContainer).toBeInTheDocument();
    });

    it('should have max-width container', () => {
      const { container } = render(<FAQSection />);

      const maxWidthContainer = container.querySelector('.max-w-3xl, .max-w-4xl');
      expect(maxWidthContainer).toBeInTheDocument();
    });

    it('should center content horizontally', () => {
      const { container } = render(<FAQSection />);

      const centeredContainer = container.querySelector('.mx-auto');
      expect(centeredContainer).toBeInTheDocument();
    });
  });

  describe('Design System Compliance', () => {
    it('should follow 8pt grid spacing', () => {
      const { container } = render(<FAQSection />);

      const section = container.querySelector('section');
      // Padding should be multiples of 8px
      expect(section).toHaveClass('py-20');
      expect(section).toHaveClass('px-6');
    });

    it('should use white background color', () => {
      const { container } = render(<FAQSection />);

      const section = container.querySelector('section');
      expect(section).toHaveClass('bg-white');
    });

    it('should use Deep Trust Blue for questions', () => {
      const { container } = render(<FAQSection />);

      // Questions should use Deep Trust Blue
      const section = container.querySelector('section');
      const questionElements = section?.querySelectorAll('.text-deep-trust-blue');
      expect(questionElements?.length).toBeGreaterThanOrEqual(6); // Section title + 5 questions
    });

    it('should use gray text for answers', () => {
      render(<FAQSection />);

      // Expand first question to see answer
      const firstQuestion = screen.getByText(/AI가 생성한 초안은 법적 효력이 있나요\?/i);
      const button = firstQuestion.closest('button');
      if (button) fireEvent.click(button);

      const answer = screen.getByText(/AI는 초안 작성을 보조하는 도구/i);
      expect(answer).toHaveClass('text-gray-600');
    });
  });

  describe('Accessibility', () => {
    it('should have aria-label for section', () => {
      const { container } = render(<FAQSection />);

      const section = container.querySelector('section');
      expect(section).toHaveAttribute('aria-label', '자주 묻는 질문');
    });

    it('should have proper heading hierarchy', () => {
      render(<FAQSection />);

      const mainHeading = screen.getByRole('heading', { name: /자주 묻는 질문/i });
      expect(mainHeading.tagName).toBe('H2');
    });

    it('should have button role for clickable items', () => {
      render(<FAQSection />);

      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThanOrEqual(5);
    });

    it('should have aria-expanded attribute on buttons', () => {
      render(<FAQSection />);

      const firstQuestion = screen.getByText(/AI가 생성한 초안은 법적 효력이 있나요\?/i);
      const button = firstQuestion.closest('button');

      expect(button).toHaveAttribute('aria-expanded');
    });
  });

  describe('Visual Presentation', () => {
    it('should have borders between FAQ items', () => {
      const { container } = render(<FAQSection />);

      const section = container.querySelector('section');
      const borderedContainer = section?.querySelector('.divide-y, .border-b');
      expect(borderedContainer).toBeInTheDocument();
    });

    it('should have proper padding on FAQ items', () => {
      const { container } = render(<FAQSection />);

      const section = container.querySelector('section');
      const paddedItems = section?.querySelectorAll('.py-4, .py-6');
      expect(paddedItems?.length).toBeGreaterThanOrEqual(5);
    });
  });
});
