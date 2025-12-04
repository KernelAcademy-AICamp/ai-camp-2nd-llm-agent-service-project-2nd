/**
 * Integration tests for InvoiceForm Component
 * Task T142 - 003-role-based-ui Feature - US8
 *
 * Tests for frontend/src/components/lawyer/InvoiceForm.tsx:
 * - Form rendering with initial values
 * - Create mode vs Edit mode
 * - Validation
 * - Form submission
 * - Case selection updates client info
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import InvoiceForm from '@/components/lawyer/InvoiceForm';
import type { Invoice } from '@/types/billing';

const mockCases = [
  { id: 'case_001', title: '김○○ 이혼 소송', client_id: 'client_001', client_name: '김철수' },
  { id: 'case_002', title: '이○○ 재산분할', client_id: 'client_002', client_name: '이영희' },
  { id: 'case_003', title: '박○○ 양육권 분쟁', client_id: 'client_003', client_name: '박민수' },
];

const mockInvoice: Invoice = {
  id: 'inv_001',
  case_id: 'case_001',
  client_id: 'client_001',
  amount: '500000',
  status: 'pending',
  description: '착수금',
  due_date: '2024-02-15T00:00:00Z',
  case_title: '김○○ 이혼 소송',
  client_name: '김철수',
  created_at: '2024-01-15T10:00:00Z',
};

describe('InvoiceForm Component', () => {
  describe('Create Mode', () => {
    test('should render form with empty fields', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      expect(screen.getByLabelText(/사건/)).toBeInTheDocument();
      expect(screen.getByLabelText(/금액/)).toBeInTheDocument();
      expect(screen.getByLabelText(/설명/)).toBeInTheDocument();
      expect(screen.getByLabelText(/결제 기한/)).toBeInTheDocument();
    });

    test('should show case selection dropdown', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      const caseSelect = screen.getByLabelText(/사건/);
      expect(caseSelect).toBeInTheDocument();
      expect(screen.getByText('사건 선택')).toBeInTheDocument();
    });

    test('should render all cases in dropdown', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      expect(screen.getByText('김○○ 이혼 소송')).toBeInTheDocument();
      expect(screen.getByText('이○○ 재산분할')).toBeInTheDocument();
      expect(screen.getByText('박○○ 양육권 분쟁')).toBeInTheDocument();
    });

    test('should show client name when case is selected', async () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      const caseSelect = screen.getByLabelText(/사건/);
      fireEvent.change(caseSelect, { target: { value: 'case_001' } });

      await waitFor(() => {
        expect(screen.getByText('김철수')).toBeInTheDocument();
      });
    });

    test('should have submit button with "청구서 발행" text', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      expect(screen.getByRole('button', { name: '청구서 발행' })).toBeInTheDocument();
    });
  });

  describe('Edit Mode', () => {
    test('should render form with existing values', () => {
      render(
        <InvoiceForm
          invoice={mockInvoice}
          onSubmit={jest.fn()}
        />
      );

      const amountInput = screen.getByLabelText(/금액/);
      expect(amountInput).toHaveValue('500000');
    });

    test('should not show case selection in edit mode', () => {
      render(
        <InvoiceForm
          invoice={mockInvoice}
          onSubmit={jest.fn()}
        />
      );

      expect(screen.queryByLabelText(/사건/)).not.toBeInTheDocument();
    });

    test('should show status selection in edit mode', () => {
      render(
        <InvoiceForm
          invoice={mockInvoice}
          onSubmit={jest.fn()}
        />
      );

      expect(screen.getByLabelText(/상태/)).toBeInTheDocument();
    });

    test('should have submit button with "수정" text', () => {
      render(
        <InvoiceForm
          invoice={mockInvoice}
          onSubmit={jest.fn()}
        />
      );

      expect(screen.getByRole('button', { name: '수정' })).toBeInTheDocument();
    });

    test('should render status options in edit mode', () => {
      render(
        <InvoiceForm
          invoice={mockInvoice}
          onSubmit={jest.fn()}
        />
      );

      expect(screen.getByText('대기중')).toBeInTheDocument();
      expect(screen.getByText('결제완료')).toBeInTheDocument();
      expect(screen.getByText('연체')).toBeInTheDocument();
      expect(screen.getByText('취소')).toBeInTheDocument();
    });
  });

  describe('Validation', () => {
    test('should show error when case not selected', async () => {
      const onSubmit = jest.fn();
      render(<InvoiceForm cases={mockCases} onSubmit={onSubmit} />);

      const amountInput = screen.getByLabelText(/금액/);
      fireEvent.change(amountInput, { target: { value: '500000' } });

      const submitButton = screen.getByRole('button', { name: '청구서 발행' });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('사건을 선택해 주세요.')).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    test('should show error when amount is empty', async () => {
      const onSubmit = jest.fn();
      render(<InvoiceForm cases={mockCases} onSubmit={onSubmit} />);

      const caseSelect = screen.getByLabelText(/사건/);
      fireEvent.change(caseSelect, { target: { value: 'case_001' } });

      const submitButton = screen.getByRole('button', { name: '청구서 발행' });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('금액을 입력해 주세요.')).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    test('should show error when amount is not a number', async () => {
      const onSubmit = jest.fn();
      render(<InvoiceForm cases={mockCases} onSubmit={onSubmit} />);

      const caseSelect = screen.getByLabelText(/사건/);
      fireEvent.change(caseSelect, { target: { value: 'case_001' } });

      const amountInput = screen.getByLabelText(/금액/);
      fireEvent.change(amountInput, { target: { value: 'abc' } });

      const submitButton = screen.getByRole('button', { name: '청구서 발행' });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('금액은 숫자만 입력해 주세요.')).toBeInTheDocument();
      });

      expect(onSubmit).not.toHaveBeenCalled();
    });

    test('should clear error when user starts typing', async () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      // Trigger validation error
      const submitButton = screen.getByRole('button', { name: '청구서 발행' });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText('금액을 입력해 주세요.')).toBeInTheDocument();
      });

      // Start typing to clear error
      const amountInput = screen.getByLabelText(/금액/);
      fireEvent.change(amountInput, { target: { value: '5' } });

      await waitFor(() => {
        expect(screen.queryByText('금액을 입력해 주세요.')).not.toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    test('should call onSubmit with form data in create mode', async () => {
      const onSubmit = jest.fn().mockResolvedValue(undefined);
      render(<InvoiceForm cases={mockCases} onSubmit={onSubmit} />);

      const caseSelect = screen.getByLabelText(/사건/);
      fireEvent.change(caseSelect, { target: { value: 'case_001' } });

      const amountInput = screen.getByLabelText(/금액/);
      fireEvent.change(amountInput, { target: { value: '500000' } });

      const descriptionInput = screen.getByLabelText(/설명/);
      fireEvent.change(descriptionInput, { target: { value: '착수금 청구' } });

      const submitButton = screen.getByRole('button', { name: '청구서 발행' });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith({
          case_id: 'case_001',
          client_id: 'client_001',
          amount: '500000',
          description: '착수금 청구',
          due_date: undefined,
        });
      });
    });

    test('should call onSubmit with form data in edit mode', async () => {
      const onSubmit = jest.fn().mockResolvedValue(undefined);
      render(
        <InvoiceForm
          invoice={mockInvoice}
          onSubmit={onSubmit}
        />
      );

      const amountInput = screen.getByLabelText(/금액/);
      fireEvent.change(amountInput, { target: { value: '600000' } });

      const submitButton = screen.getByRole('button', { name: '수정' });
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({
          amount: '600000',
          status: 'pending',
        }));
      });
    });

    test('should disable submit button while loading', () => {
      render(
        <InvoiceForm
          cases={mockCases}
          onSubmit={jest.fn()}
          loading={true}
        />
      );

      const submitButton = screen.getByRole('button', { name: '처리 중...' });
      expect(submitButton).toBeDisabled();
    });
  });

  describe('Cancel Button', () => {
    test('should render cancel button when onCancel is provided', () => {
      const onCancel = jest.fn();
      render(
        <InvoiceForm
          cases={mockCases}
          onSubmit={jest.fn()}
          onCancel={onCancel}
        />
      );

      expect(screen.getByRole('button', { name: '취소' })).toBeInTheDocument();
    });

    test('should call onCancel when cancel button clicked', () => {
      const onCancel = jest.fn();
      render(
        <InvoiceForm
          cases={mockCases}
          onSubmit={jest.fn()}
          onCancel={onCancel}
        />
      );

      fireEvent.click(screen.getByRole('button', { name: '취소' }));
      expect(onCancel).toHaveBeenCalled();
    });

    test('should not render cancel button when onCancel is not provided', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      expect(screen.queryByRole('button', { name: '취소' })).not.toBeInTheDocument();
    });
  });

  describe('Due Date Input', () => {
    test('should render due date input', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      expect(screen.getByLabelText(/결제 기한/)).toBeInTheDocument();
    });

    test('should accept date input', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      const dueDateInput = screen.getByLabelText(/결제 기한/);
      fireEvent.change(dueDateInput, { target: { value: '2024-03-01' } });

      expect(dueDateInput).toHaveValue('2024-03-01');
    });

    test('should pre-fill due date in edit mode', () => {
      render(
        <InvoiceForm
          invoice={mockInvoice}
          onSubmit={jest.fn()}
        />
      );

      const dueDateInput = screen.getByLabelText(/결제 기한/);
      expect(dueDateInput).toHaveValue('2024-02-15');
    });
  });

  describe('Description Input', () => {
    test('should render description textarea', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      expect(screen.getByLabelText(/설명/)).toBeInTheDocument();
    });

    test('should accept description input', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      const descriptionInput = screen.getByLabelText(/설명/);
      fireEvent.change(descriptionInput, { target: { value: '착수금 청구입니다.' } });

      expect(descriptionInput).toHaveValue('착수금 청구입니다.');
    });

    test('should pre-fill description in edit mode', () => {
      render(
        <InvoiceForm
          invoice={mockInvoice}
          onSubmit={jest.fn()}
        />
      );

      const descriptionInput = screen.getByLabelText(/설명/);
      expect(descriptionInput).toHaveValue('착수금');
    });
  });

  describe('Amount Input', () => {
    test('should show won symbol', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      expect(screen.getByText('원')).toBeInTheDocument();
    });

    test('should show placeholder for amount', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      const amountInput = screen.getByLabelText(/금액/);
      expect(amountInput).toHaveAttribute('placeholder', '500000');
    });
  });

  describe('Custom Styling', () => {
    test('should apply custom className', () => {
      const { container } = render(
        <InvoiceForm
          cases={mockCases}
          onSubmit={jest.fn()}
          className="custom-form-class"
        />
      );

      expect(container.querySelector('form')).toHaveClass('custom-form-class');
    });
  });

  describe('Required Field Indicators', () => {
    test('should show required indicator for case field', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      // Check for asterisk in label - use labelText query
      const caseLabel = screen.getByLabelText(/사건/).closest('div')?.querySelector('label');
      expect(caseLabel?.textContent).toContain('*');
    });

    test('should show required indicator for amount field', () => {
      render(<InvoiceForm cases={mockCases} onSubmit={jest.fn()} />);

      // Check for asterisk in label - use ID to find label
      const amountInput = screen.getByLabelText(/금액/);
      const labelId = amountInput.getAttribute('id');
      const label = document.querySelector(`label[for="${labelId}"]`);
      expect(label?.textContent).toContain('*');
    });
  });
});
