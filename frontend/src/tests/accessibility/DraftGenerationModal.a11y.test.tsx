/**
 * DraftGenerationModal Accessibility Tests
 * TDD Red → Green cycle for button accessibility (plan.md Section 7)
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import DraftGenerationModal from '@/components/draft/DraftGenerationModal';
import { Evidence } from '@/types/evidence';

const mockEvidence: Evidence[] = [
  {
    id: '1',
    caseId: 'case-1',
    type: 'text',
    filename: 'chat_log.txt',
    uploadDate: '2024-01-15',
    status: 'completed',
    size: 1024,
    summary: '테스트 요약',
  },
  {
    id: '2',
    caseId: 'case-1',
    type: 'image',
    filename: 'evidence.jpg',
    uploadDate: '2024-01-16',
    status: 'processing',
    size: 2048,
  },
];

describe('DraftGenerationModal Accessibility', () => {
  const defaultProps = {
    isOpen: true,
    onClose: jest.fn(),
    onGenerate: jest.fn(),
    evidenceList: mockEvidence,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Button type="button" attribute', () => {
    it('close button (X icon) should have type="button"', () => {
      render(<DraftGenerationModal {...defaultProps} />);

      const closeButton = screen.getByRole('button', { name: '닫기' });
      expect(closeButton).toHaveAttribute('type', 'button');
    });

    it('select all button should have type="button"', () => {
      render(<DraftGenerationModal {...defaultProps} />);

      const selectAllButton = screen.getByRole('button', { name: /전체 선택|전체 해제/i });
      expect(selectAllButton).toHaveAttribute('type', 'button');
    });

    it('cancel button should have type="button"', () => {
      render(<DraftGenerationModal {...defaultProps} />);

      const cancelButton = screen.getByRole('button', { name: '취소' });
      expect(cancelButton).toHaveAttribute('type', 'button');
    });

    it('generate button should have type="button"', () => {
      render(<DraftGenerationModal {...defaultProps} />);

      const generateButton = screen.getByRole('button', { name: /초안 생성/i });
      expect(generateButton).toHaveAttribute('type', 'button');
    });

    it('all buttons in modal should have type="button"', () => {
      render(<DraftGenerationModal {...defaultProps} />);

      const allButtons = screen.getAllByRole('button');
      allButtons.forEach((button) => {
        expect(button).toHaveAttribute('type', 'button');
      });
    });
  });

  describe('aria-label accessibility', () => {
    it('close button should have aria-label="닫기"', () => {
      render(<DraftGenerationModal {...defaultProps} />);

      const closeButton = screen.getByRole('button', { name: '닫기' });
      expect(closeButton).toHaveAttribute('aria-label', '닫기');
    });
  });

  describe('Modal rendering', () => {
    it('should not render when isOpen is false', () => {
      render(<DraftGenerationModal {...defaultProps} isOpen={false} />);

      expect(screen.queryByText('Draft 생성 옵션')).not.toBeInTheDocument();
    });

    it('should render modal title when isOpen is true', () => {
      render(<DraftGenerationModal {...defaultProps} />);

      expect(screen.getByText('Draft 생성 옵션')).toBeInTheDocument();
    });
  });
});
