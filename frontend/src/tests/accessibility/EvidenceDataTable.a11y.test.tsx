/**
 * EvidenceDataTable Accessibility Tests
 * TDD Red → Green cycle for button accessibility (plan.md Section 7)
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { EvidenceDataTable } from '@/components/evidence/EvidenceDataTable';
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

describe('EvidenceDataTable Accessibility', () => {
  describe('Sort button type="button" attribute', () => {
    it('filename sort button should have type="button"', () => {
      render(<EvidenceDataTable items={mockEvidence} />);

      const filenameHeader = screen.getByRole('button', { name: /파일명/i });
      expect(filenameHeader).toHaveAttribute('type', 'button');
    });

    it('upload date sort button should have type="button"', () => {
      render(<EvidenceDataTable items={mockEvidence} />);

      const dateHeader = screen.getByRole('button', { name: /업로드 날짜/i });
      expect(dateHeader).toHaveAttribute('type', 'button');
    });
  });

  describe('Action button accessibility', () => {
    it('action buttons should have type="button"', () => {
      render(<EvidenceDataTable items={mockEvidence} />);

      // Each row should have an action button with proper type
      const actionButtons = screen.getAllByRole('button', { name: /추가 작업/i });
      actionButtons.forEach((button) => {
        expect(button).toHaveAttribute('type', 'button');
      });
    });

    it('action buttons should have descriptive aria-label with filename', () => {
      render(<EvidenceDataTable items={mockEvidence} />);

      // Check that aria-labels include the filename for context
      expect(screen.getByRole('button', { name: 'chat_log.txt 추가 작업' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'evidence.jpg 추가 작업' })).toBeInTheDocument();
    });
  });

  describe('All interactive buttons compliance', () => {
    it('all buttons in the table should have type="button"', () => {
      render(<EvidenceDataTable items={mockEvidence} />);

      const allButtons = screen.getAllByRole('button');
      allButtons.forEach((button) => {
        expect(button).toHaveAttribute('type', 'button');
      });
    });
  });

  describe('Table structure accessibility', () => {
    it('table headers should have scope="col"', () => {
      render(<EvidenceDataTable items={mockEvidence} />);

      const headers = screen.getAllByRole('columnheader');
      headers.forEach((header) => {
        expect(header).toHaveAttribute('scope', 'col');
      });
    });

    it('actions column should have sr-only text for screen readers', () => {
      render(<EvidenceDataTable items={mockEvidence} />);

      expect(screen.getByText('Actions')).toHaveClass('sr-only');
    });
  });
});
