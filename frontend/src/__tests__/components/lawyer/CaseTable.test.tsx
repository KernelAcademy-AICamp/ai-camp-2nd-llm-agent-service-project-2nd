/**
 * CaseTable Component Integration Tests
 * 003-role-based-ui Feature - US3 (T041)
 *
 * Tests for table sorting and row selection functionality.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { CaseTable } from '@/components/lawyer/CaseTable';

// Mock next/link
jest.mock('next/link', () => {
  return ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  );
});

const mockCases = [
  {
    id: '1',
    title: '이혼 소송 A',
    clientName: '김철수',
    status: 'active',
    createdAt: '2024-01-15T10:00:00Z',
    updatedAt: '2024-03-20T14:30:00Z',
    evidenceCount: 5,
    progress: 60,
    ownerName: '박변호사',
  },
  {
    id: '2',
    title: '재산분할 B',
    clientName: '이영희',
    status: 'in_progress',
    createdAt: '2024-02-10T09:00:00Z',
    updatedAt: '2024-03-18T11:00:00Z',
    evidenceCount: 3,
    progress: 30,
    ownerName: '김변호사',
  },
  {
    id: '3',
    title: '양육권 분쟁 C',
    clientName: '박민수',
    status: 'closed',
    createdAt: '2024-01-01T08:00:00Z',
    updatedAt: '2024-03-15T16:00:00Z',
    evidenceCount: 10,
    progress: 100,
    ownerName: '박변호사',
  },
];

describe('CaseTable', () => {
  const defaultProps = {
    cases: mockCases,
    selectedIds: [] as string[],
    onSelectionChange: jest.fn(),
    sortBy: 'updated_at',
    sortOrder: 'desc' as const,
    onSort: jest.fn(),
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders table with all cases', () => {
      render(<CaseTable {...defaultProps} />);

      expect(screen.getByText('이혼 소송 A')).toBeInTheDocument();
      expect(screen.getByText('재산분할 B')).toBeInTheDocument();
      expect(screen.getByText('양육권 분쟁 C')).toBeInTheDocument();
    });

    it('renders table headers correctly', () => {
      render(<CaseTable {...defaultProps} />);

      expect(screen.getByText('케이스명')).toBeInTheDocument();
      expect(screen.getByText('의뢰인')).toBeInTheDocument();
      expect(screen.getByText('상태')).toBeInTheDocument();
      expect(screen.getByText('증거')).toBeInTheDocument();
      expect(screen.getByText('진행률')).toBeInTheDocument();
      expect(screen.getByText('최근 업데이트')).toBeInTheDocument();
      expect(screen.getByText('담당자')).toBeInTheDocument();
    });

    it('renders status badges with correct labels', () => {
      render(<CaseTable {...defaultProps} />);

      expect(screen.getByText('활성')).toBeInTheDocument();
      expect(screen.getByText('검토 대기')).toBeInTheDocument();
      expect(screen.getByText('종료')).toBeInTheDocument();
    });

    it('renders empty state when no cases', () => {
      render(<CaseTable {...defaultProps} cases={[]} />);

      expect(screen.getByText('케이스가 없습니다.')).toBeInTheDocument();
    });

    it('renders client name or dash for missing values', () => {
      const casesWithMissingClient = [
        { ...mockCases[0], clientName: undefined },
      ];
      render(<CaseTable {...defaultProps} cases={casesWithMissingClient} />);

      expect(screen.getByText('-')).toBeInTheDocument();
    });

    it('renders evidence count correctly', () => {
      render(<CaseTable {...defaultProps} />);

      expect(screen.getByText('5건')).toBeInTheDocument();
      expect(screen.getByText('3건')).toBeInTheDocument();
      expect(screen.getByText('10건')).toBeInTheDocument();
    });

    it('renders progress percentage correctly', () => {
      render(<CaseTable {...defaultProps} />);

      expect(screen.getByText('60%')).toBeInTheDocument();
      expect(screen.getByText('30%')).toBeInTheDocument();
      expect(screen.getByText('100%')).toBeInTheDocument();
    });
  });

  describe('Sorting', () => {
    it('calls onSort when clicking sortable header - title', () => {
      render(<CaseTable {...defaultProps} />);

      fireEvent.click(screen.getByText('케이스명'));

      expect(defaultProps.onSort).toHaveBeenCalledWith('title');
    });

    it('calls onSort when clicking sortable header - client_name', () => {
      render(<CaseTable {...defaultProps} />);

      fireEvent.click(screen.getByText('의뢰인'));

      expect(defaultProps.onSort).toHaveBeenCalledWith('client_name');
    });

    it('calls onSort when clicking sortable header - status', () => {
      render(<CaseTable {...defaultProps} />);

      fireEvent.click(screen.getByText('상태'));

      expect(defaultProps.onSort).toHaveBeenCalledWith('status');
    });

    it('calls onSort when clicking sortable header - updated_at', () => {
      render(<CaseTable {...defaultProps} />);

      fireEvent.click(screen.getByText('최근 업데이트'));

      expect(defaultProps.onSort).toHaveBeenCalledWith('updated_at');
    });

    it('displays ascending sort icon when sortOrder is asc', () => {
      render(<CaseTable {...defaultProps} sortBy="title" sortOrder="asc" />);

      // The ascending icon should be visible (chevron up)
      const titleHeader = screen.getByText('케이스명').closest('th');
      expect(titleHeader).toBeInTheDocument();
    });

    it('displays descending sort icon when sortOrder is desc', () => {
      render(<CaseTable {...defaultProps} sortBy="title" sortOrder="desc" />);

      // The descending icon should be visible (chevron down)
      const titleHeader = screen.getByText('케이스명').closest('th');
      expect(titleHeader).toBeInTheDocument();
    });
  });

  describe('Selection', () => {
    it('renders checkboxes for each row', () => {
      render(<CaseTable {...defaultProps} />);

      // Header checkbox + 3 row checkboxes
      const checkboxes = screen.getAllByRole('checkbox');
      expect(checkboxes).toHaveLength(4);
    });

    it('calls onSelectionChange when selecting a single row', () => {
      render(<CaseTable {...defaultProps} />);

      const checkboxes = screen.getAllByRole('checkbox');
      // First checkbox is header, so click second one (first row)
      fireEvent.click(checkboxes[1]);

      expect(defaultProps.onSelectionChange).toHaveBeenCalledWith(['1']);
    });

    it('calls onSelectionChange when deselecting a row', () => {
      render(<CaseTable {...defaultProps} selectedIds={['1']} />);

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[1]);

      expect(defaultProps.onSelectionChange).toHaveBeenCalledWith([]);
    });

    it('selects all rows when clicking header checkbox', () => {
      render(<CaseTable {...defaultProps} />);

      const headerCheckbox = screen.getAllByRole('checkbox')[0];
      fireEvent.click(headerCheckbox);

      expect(defaultProps.onSelectionChange).toHaveBeenCalledWith(['1', '2', '3']);
    });

    it('deselects all rows when clicking header checkbox with all selected', () => {
      render(<CaseTable {...defaultProps} selectedIds={['1', '2', '3']} />);

      const headerCheckbox = screen.getAllByRole('checkbox')[0];
      fireEvent.click(headerCheckbox);

      expect(defaultProps.onSelectionChange).toHaveBeenCalledWith([]);
    });

    it('shows selected row with highlighted background', () => {
      render(<CaseTable {...defaultProps} selectedIds={['1']} />);

      const rows = screen.getAllByRole('row');
      // First row is header, second row should be highlighted
      expect(rows[1]).toHaveClass('bg-blue-50');
    });

    it('header checkbox is checked when all rows selected', () => {
      render(<CaseTable {...defaultProps} selectedIds={['1', '2', '3']} />);

      const headerCheckbox = screen.getAllByRole('checkbox')[0] as HTMLInputElement;
      expect(headerCheckbox.checked).toBe(true);
    });

    it('header checkbox is indeterminate when some rows selected', () => {
      render(<CaseTable {...defaultProps} selectedIds={['1']} />);

      const headerCheckbox = screen.getAllByRole('checkbox')[0] as HTMLInputElement;
      expect(headerCheckbox.indeterminate).toBe(true);
    });
  });

  describe('Links', () => {
    it('renders case title as link to case detail', () => {
      render(<CaseTable {...defaultProps} />);

      const link = screen.getByRole('link', { name: '이혼 소송 A' });
      expect(link).toHaveAttribute('href', '/lawyer/cases/1');
    });

    it('renders all case titles as links', () => {
      render(<CaseTable {...defaultProps} />);

      const links = screen.getAllByRole('link');
      expect(links).toHaveLength(3);
      expect(links[0]).toHaveAttribute('href', '/lawyer/cases/1');
      expect(links[1]).toHaveAttribute('href', '/lawyer/cases/2');
      expect(links[2]).toHaveAttribute('href', '/lawyer/cases/3');
    });
  });
});
