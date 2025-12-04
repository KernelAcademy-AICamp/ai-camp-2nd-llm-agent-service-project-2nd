/**
 * Integration tests for InvoiceList Component
 * Task T142 - 003-role-based-ui Feature - US8
 *
 * Tests for frontend/src/components/lawyer/InvoiceList.tsx:
 * - Invoice list rendering with data
 * - Empty state display
 * - Filter functionality
 * - Summary cards display
 * - Pagination controls
 * - Edit and delete actions
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import InvoiceList from '@/components/lawyer/InvoiceList';
import type { Invoice } from '@/types/billing';

const mockInvoices: Invoice[] = [
  {
    id: 'inv_001',
    case_id: 'case_001',
    client_id: 'client_001',
    amount: '500000',
    status: 'pending',
    case_title: '김○○ 이혼 소송',
    client_name: '김철수',
    created_at: '2024-01-15T10:00:00Z',
    due_date: '2024-02-15T10:00:00Z',
  },
  {
    id: 'inv_002',
    case_id: 'case_002',
    client_id: 'client_002',
    amount: '1000000',
    status: 'paid',
    case_title: '이○○ 재산분할',
    client_name: '이영희',
    created_at: '2024-01-10T10:00:00Z',
    paid_at: '2024-01-20T15:30:00Z',
  },
  {
    id: 'inv_003',
    case_id: 'case_003',
    client_id: 'client_003',
    amount: '300000',
    status: 'overdue',
    case_title: '박○○ 양육권 분쟁',
    client_name: '박민수',
    created_at: '2024-01-01T10:00:00Z',
    due_date: '2024-01-10T10:00:00Z',
  },
];

describe('InvoiceList Component', () => {
  const defaultProps = {
    invoices: mockInvoices,
    total: 3,
    totalPending: '500000',
    totalPaid: '1000000',
  };

  describe('Basic Rendering', () => {
    test('should render invoice list with data', () => {
      render(<InvoiceList {...defaultProps} />);

      expect(screen.getByText('김○○ 이혼 소송')).toBeInTheDocument();
      expect(screen.getByText('이○○ 재산분할')).toBeInTheDocument();
      expect(screen.getByText('박○○ 양육권 분쟁')).toBeInTheDocument();
    });

    test('should render client names', () => {
      render(<InvoiceList {...defaultProps} />);

      expect(screen.getByText('김철수')).toBeInTheDocument();
      expect(screen.getByText('이영희')).toBeInTheDocument();
      expect(screen.getByText('박민수')).toBeInTheDocument();
    });

    test('should render invoice amounts', () => {
      render(<InvoiceList {...defaultProps} />);

      // Check for formatted currency values (may appear in summary and table)
      expect(screen.getAllByText(/₩500,000/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/₩1,000,000/).length).toBeGreaterThan(0);
      expect(screen.getByText(/₩300,000/)).toBeInTheDocument();
    });

    test('should display loading state', () => {
      render(<InvoiceList {...defaultProps} loading={true} />);

      // Should show loading spinner
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });
  });

  describe('Empty State', () => {
    test('should show empty message when no invoices', () => {
      render(
        <InvoiceList
          invoices={[]}
          total={0}
          totalPending="0"
          totalPaid="0"
        />
      );

      expect(screen.getByText('청구서가 없습니다.')).toBeInTheDocument();
    });
  });

  describe('Summary Cards', () => {
    test('should display total invoices count', () => {
      render(<InvoiceList {...defaultProps} />);

      expect(screen.getByText('총 청구서')).toBeInTheDocument();
      expect(screen.getByText('3건')).toBeInTheDocument();
    });

    test('should display pending total amount', () => {
      render(<InvoiceList {...defaultProps} />);

      expect(screen.getByText('대기중 금액')).toBeInTheDocument();
      // Amount appears in both summary card and table
      expect(screen.getAllByText(/₩500,000/).length).toBeGreaterThan(0);
    });

    test('should display paid total amount', () => {
      render(<InvoiceList {...defaultProps} />);

      expect(screen.getByText('결제 완료')).toBeInTheDocument();
      // Amount appears in both summary card and table
      expect(screen.getAllByText(/₩1,000,000/).length).toBeGreaterThan(0);
    });
  });

  describe('Status Badges', () => {
    test('should display pending status badge', () => {
      render(<InvoiceList {...defaultProps} />);

      // "대기중" appears in both filter button and status badge
      expect(screen.getAllByText('대기중').length).toBeGreaterThanOrEqual(2);
    });

    test('should display paid status badge', () => {
      render(<InvoiceList {...defaultProps} />);

      // "결제완료" appears in both filter button and status badge
      expect(screen.getAllByText('결제완료').length).toBeGreaterThanOrEqual(2);
    });

    test('should display overdue status badge', () => {
      render(<InvoiceList {...defaultProps} />);

      // "연체" appears in both filter button and status badge
      expect(screen.getAllByText('연체').length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Filter Functionality', () => {
    test('should render filter buttons', () => {
      render(<InvoiceList {...defaultProps} />);

      expect(screen.getByRole('button', { name: '전체' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '대기중' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '결제완료' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '연체' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '취소' })).toBeInTheDocument();
    });

    test('should call onFilterChange when filter clicked', () => {
      const onFilterChange = jest.fn();
      render(<InvoiceList {...defaultProps} onFilterChange={onFilterChange} />);

      fireEvent.click(screen.getByRole('button', { name: '대기중' }));
      expect(onFilterChange).toHaveBeenCalledWith('pending');
    });

    test('should call onFilterChange with null for "all" filter', () => {
      const onFilterChange = jest.fn();
      render(<InvoiceList {...defaultProps} onFilterChange={onFilterChange} />);

      fireEvent.click(screen.getByRole('button', { name: '전체' }));
      expect(onFilterChange).toHaveBeenCalledWith(null);
    });
  });

  describe('Action Buttons', () => {
    test('should show edit button for each invoice', () => {
      const onEdit = jest.fn();
      render(<InvoiceList {...defaultProps} onEdit={onEdit} />);

      const editButtons = screen.getAllByRole('button', { name: '수정' });
      expect(editButtons.length).toBe(3);
    });

    test('should call onEdit when edit button clicked', () => {
      const onEdit = jest.fn();
      render(<InvoiceList {...defaultProps} onEdit={onEdit} />);

      const editButtons = screen.getAllByRole('button', { name: '수정' });
      fireEvent.click(editButtons[0]);
      expect(onEdit).toHaveBeenCalledWith(mockInvoices[0]);
    });

    test('should only show delete button for pending invoices', () => {
      const onDelete = jest.fn();
      render(<InvoiceList {...defaultProps} onDelete={onDelete} />);

      // Only 1 pending invoice should have delete button
      const deleteButtons = screen.getAllByRole('button', { name: '삭제' });
      expect(deleteButtons.length).toBe(1);
    });

    test('should call onDelete when delete button clicked', () => {
      const onDelete = jest.fn();
      render(<InvoiceList {...defaultProps} onDelete={onDelete} />);

      const deleteButton = screen.getByRole('button', { name: '삭제' });
      fireEvent.click(deleteButton);
      expect(onDelete).toHaveBeenCalledWith(mockInvoices[0]); // First invoice is pending
    });
  });

  describe('Pagination', () => {
    test('should show pagination when multiple pages exist', () => {
      render(
        <InvoiceList
          {...defaultProps}
          total={50}
          currentPage={1}
          pageSize={20}
        />
      );

      expect(screen.getByRole('button', { name: '이전' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: '다음' })).toBeInTheDocument();
    });

    test('should call onPageChange when next clicked', () => {
      const onPageChange = jest.fn();
      render(
        <InvoiceList
          {...defaultProps}
          total={50}
          currentPage={1}
          pageSize={20}
          onPageChange={onPageChange}
        />
      );

      fireEvent.click(screen.getByRole('button', { name: '다음' }));
      expect(onPageChange).toHaveBeenCalledWith(2);
    });

    test('should call onPageChange when previous clicked', () => {
      const onPageChange = jest.fn();
      render(
        <InvoiceList
          {...defaultProps}
          total={50}
          currentPage={2}
          pageSize={20}
          onPageChange={onPageChange}
        />
      );

      fireEvent.click(screen.getByRole('button', { name: '이전' }));
      expect(onPageChange).toHaveBeenCalledWith(1);
    });

    test('should disable previous button on first page', () => {
      render(
        <InvoiceList
          {...defaultProps}
          total={50}
          currentPage={1}
          pageSize={20}
        />
      );

      const prevButton = screen.getByRole('button', { name: '이전' });
      expect(prevButton).toBeDisabled();
    });

    test('should disable next button on last page', () => {
      render(
        <InvoiceList
          {...defaultProps}
          total={50}
          currentPage={3}
          pageSize={20}
        />
      );

      const nextButton = screen.getByRole('button', { name: '다음' });
      expect(nextButton).toBeDisabled();
    });

    test('should not show pagination when only one page', () => {
      render(
        <InvoiceList
          {...defaultProps}
          total={3}
          currentPage={1}
          pageSize={20}
        />
      );

      expect(screen.queryByRole('button', { name: '이전' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: '다음' })).not.toBeInTheDocument();
    });
  });

  describe('Table Headers', () => {
    test('should render all table headers', () => {
      render(<InvoiceList {...defaultProps} />);

      expect(screen.getByText('사건')).toBeInTheDocument();
      expect(screen.getByText('의뢰인')).toBeInTheDocument();
      expect(screen.getByText('금액')).toBeInTheDocument();
      expect(screen.getByText('상태')).toBeInTheDocument();
      expect(screen.getByText('발행일')).toBeInTheDocument();
      expect(screen.getByText('결제 기한')).toBeInTheDocument();
      expect(screen.getByText('액션')).toBeInTheDocument();
    });
  });

  describe('Date Formatting', () => {
    test('should format dates in Korean locale', () => {
      render(<InvoiceList {...defaultProps} />);

      // Dates should be formatted in Korean (multiple dates appear in table)
      // The exact format depends on locale settings
      expect(screen.getAllByText(/2024/).length).toBeGreaterThan(0);
    });

    test('should show dash for missing due date', () => {
      const invoicesWithoutDueDate: Invoice[] = [
        {
          ...mockInvoices[0],
          due_date: undefined,
        },
      ];

      render(
        <InvoiceList
          invoices={invoicesWithoutDueDate}
          total={1}
          totalPending="500000"
          totalPaid="0"
        />
      );

      // Should have a dash for missing due date
      const dashes = screen.getAllByText('-');
      expect(dashes.length).toBeGreaterThan(0);
    });
  });

  describe('Custom Styling', () => {
    test('should apply custom className', () => {
      const { container } = render(
        <InvoiceList {...defaultProps} className="custom-class" />
      );

      expect(container.firstChild).toHaveClass('custom-class');
    });
  });
});
