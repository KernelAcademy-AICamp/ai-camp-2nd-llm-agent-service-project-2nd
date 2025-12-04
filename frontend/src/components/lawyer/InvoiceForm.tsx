/**
 * InvoiceForm Component
 * 003-role-based-ui Feature - US8 (T150)
 *
 * Component for creating and editing invoices.
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import type { Invoice, InvoiceCreateRequest, InvoiceStatus } from '@/types/billing';

interface InvoiceFormProps {
  invoice?: Invoice | null;
  cases?: Array<{ id: string; title: string; client_id?: string; client_name?: string }>;
  onSubmit: (data: InvoiceCreateRequest | { amount?: string; description?: string; status?: InvoiceStatus; due_date?: string }) => Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
  className?: string;
}

interface FormData {
  case_id: string;
  client_id: string;
  amount: string;
  description: string;
  due_date: string;
  status: InvoiceStatus;
}

interface FormErrors {
  case_id?: string;
  client_id?: string;
  amount?: string;
}

export default function InvoiceForm({
  invoice,
  cases = [],
  onSubmit,
  onCancel,
  loading = false,
  className = '',
}: InvoiceFormProps) {
  const isEdit = !!invoice;

  const [formData, setFormData] = useState<FormData>({
    case_id: invoice?.case_id || '',
    client_id: invoice?.client_id || '',
    amount: invoice?.amount || '',
    description: invoice?.description || '',
    due_date: invoice?.due_date ? invoice.due_date.split('T')[0] : '',
    status: invoice?.status || 'pending',
  });
  const [errors, setErrors] = useState<FormErrors>({});

  // Update client_id when case_id changes
  useEffect(() => {
    if (!isEdit && formData.case_id) {
      const selectedCase = cases.find((c) => c.id === formData.case_id);
      if (selectedCase?.client_id) {
        setFormData((prev) => ({ ...prev, client_id: selectedCase.client_id || '' }));
      }
    }
  }, [formData.case_id, cases, isEdit]);

  const handleInputChange = useCallback(
    (field: keyof FormData) =>
      (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
        setFormData((prev) => ({
          ...prev,
          [field]: e.target.value,
        }));
        // Clear error when user starts typing
        if (errors[field as keyof FormErrors]) {
          setErrors((prev) => ({
            ...prev,
            [field]: undefined,
          }));
        }
      },
    [errors]
  );

  const validate = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    if (!isEdit && !formData.case_id) {
      newErrors.case_id = '사건을 선택해 주세요.';
    }

    if (!isEdit && !formData.client_id) {
      newErrors.client_id = '의뢰인을 선택해 주세요.';
    }

    if (!formData.amount.trim()) {
      newErrors.amount = '금액을 입력해 주세요.';
    } else if (!/^\d+$/.test(formData.amount.trim())) {
      newErrors.amount = '금액은 숫자만 입력해 주세요.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData, isEdit]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!validate()) {
        return;
      }

      if (isEdit) {
        await onSubmit({
          amount: formData.amount.trim(),
          description: formData.description.trim() || undefined,
          status: formData.status,
          due_date: formData.due_date || undefined,
        });
      } else {
        await onSubmit({
          case_id: formData.case_id,
          client_id: formData.client_id,
          amount: formData.amount.trim(),
          description: formData.description.trim() || undefined,
          due_date: formData.due_date || undefined,
        });
      }
    },
    [formData, validate, onSubmit, isEdit]
  );

  const selectedCase = cases.find((c) => c.id === formData.case_id);

  return (
    <form onSubmit={handleSubmit} className={`bg-white rounded-lg ${className}`}>
      <div className="p-6 space-y-6">
        {/* Case Selection */}
        {!isEdit && (
          <div>
            <label
              htmlFor="invoice-case"
              className="block text-sm font-medium text-[var(--color-text-primary)] mb-2"
            >
              사건 <span className="text-[var(--color-error)]">*</span>
            </label>
            <select
              id="invoice-case"
              value={formData.case_id}
              onChange={handleInputChange('case_id')}
              className={`w-full px-4 py-3 border rounded-lg
                focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent
                ${errors.case_id ? 'border-[var(--color-error)]' : 'border-[var(--color-border)]'}`}
            >
              <option value="">사건 선택</option>
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.title}
                </option>
              ))}
            </select>
            {errors.case_id && (
              <p className="mt-1 text-sm text-[var(--color-error)]">{errors.case_id}</p>
            )}
          </div>
        )}

        {/* Client Info (read-only) */}
        {!isEdit && selectedCase && (
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">
              의뢰인
            </label>
            <div className="px-4 py-3 bg-[var(--color-bg-secondary)] border border-[var(--color-border)] rounded-lg">
              {selectedCase.client_name || '의뢰인 정보 없음'}
            </div>
            <input type="hidden" value={formData.client_id} />
          </div>
        )}

        {/* Amount */}
        <div>
          <label
            htmlFor="invoice-amount"
            className="block text-sm font-medium text-[var(--color-text-primary)] mb-2"
          >
            금액 (원) <span className="text-[var(--color-error)]">*</span>
          </label>
          <div className="relative">
            <input
              id="invoice-amount"
              type="text"
              value={formData.amount}
              onChange={handleInputChange('amount')}
              placeholder="500000"
              className={`w-full px-4 py-3 border rounded-lg pr-12
                focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent
                ${errors.amount ? 'border-[var(--color-error)]' : 'border-[var(--color-border)]'}`}
            />
            <span className="absolute right-4 top-1/2 -translate-y-1/2 text-[var(--color-text-secondary)]">
              원
            </span>
          </div>
          {errors.amount && (
            <p className="mt-1 text-sm text-[var(--color-error)]">{errors.amount}</p>
          )}
        </div>

        {/* Description */}
        <div>
          <label
            htmlFor="invoice-description"
            className="block text-sm font-medium text-[var(--color-text-primary)] mb-2"
          >
            설명
          </label>
          <textarea
            id="invoice-description"
            value={formData.description}
            onChange={handleInputChange('description')}
            placeholder="청구서에 대한 설명을 입력하세요..."
            rows={3}
            className="w-full px-4 py-3 border border-[var(--color-border)] rounded-lg resize-none
              focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
          />
        </div>

        {/* Due Date */}
        <div>
          <label
            htmlFor="invoice-due-date"
            className="block text-sm font-medium text-[var(--color-text-primary)] mb-2"
          >
            결제 기한
          </label>
          <input
            id="invoice-due-date"
            type="date"
            value={formData.due_date}
            onChange={handleInputChange('due_date')}
            className="w-full px-4 py-3 border border-[var(--color-border)] rounded-lg
              focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
          />
        </div>

        {/* Status (edit mode only) */}
        {isEdit && (
          <div>
            <label
              htmlFor="invoice-status"
              className="block text-sm font-medium text-[var(--color-text-primary)] mb-2"
            >
              상태
            </label>
            <select
              id="invoice-status"
              value={formData.status}
              onChange={handleInputChange('status')}
              className="w-full px-4 py-3 border border-[var(--color-border)] rounded-lg
                focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
            >
              <option value="pending">대기중</option>
              <option value="paid">결제완료</option>
              <option value="overdue">연체</option>
              <option value="cancelled">취소</option>
            </select>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="px-6 py-4 border-t border-[var(--color-border)] flex justify-end gap-3">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-3 border border-[var(--color-border)] rounded-lg
              text-[var(--color-text-primary)] hover:bg-[var(--color-bg-secondary)]
              min-h-[44px]"
          >
            취소
          </button>
        )}
        <button
          type="submit"
          disabled={loading}
          className="px-6 py-3 bg-[var(--color-primary)] text-white rounded-lg
            font-medium hover:bg-[var(--color-primary-hover)]
            disabled:opacity-50 disabled:cursor-not-allowed
            min-h-[44px]"
        >
          {loading ? '처리 중...' : isEdit ? '수정' : '청구서 발행'}
        </button>
      </div>
    </form>
  );
}
