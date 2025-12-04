/**
 * ReportEditor Component
 * 003-role-based-ui Feature - US5 (T101)
 *
 * Component for creating and submitting investigation reports.
 * Includes summary, findings, conclusion sections and attachment support.
 */

'use client';

import { useState, useCallback, useRef } from 'react';
import { submitReport, type ReportRequest } from '@/lib/api/detective-portal';

interface ReportEditorProps {
  caseId: string;
  caseTitle?: string;
  onReportSubmitted?: (reportId: string) => void;
  onError?: (error: string) => void;
  className?: string;
}

interface FormData {
  summary: string;
  findings: string;
  conclusion: string;
  attachments: string[];
}

interface FormErrors {
  summary?: string;
  findings?: string;
  conclusion?: string;
}

export default function ReportEditor({
  caseId,
  caseTitle,
  onReportSubmitted,
  onError,
  className = '',
}: ReportEditorProps) {
  const [formData, setFormData] = useState<FormData>({
    summary: '',
    findings: '',
    conclusion: '',
    attachments: [],
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showPreview, setShowPreview] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleInputChange = useCallback(
    (field: keyof FormData) => (e: React.ChangeEvent<HTMLTextAreaElement>) => {
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

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      const newAttachments = Array.from(files).map((file) => file.name);
      setFormData((prev) => ({
        ...prev,
        attachments: [...prev.attachments, ...newAttachments],
      }));
    }
  }, []);

  const handleRemoveAttachment = useCallback((index: number) => {
    setFormData((prev) => ({
      ...prev,
      attachments: prev.attachments.filter((_, i) => i !== index),
    }));
  }, []);

  const validate = useCallback((): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.summary.trim()) {
      newErrors.summary = '조사 요약을 입력해 주세요.';
    } else if (formData.summary.trim().length < 20) {
      newErrors.summary = '조사 요약은 20자 이상 입력해 주세요.';
    }

    if (!formData.findings.trim()) {
      newErrors.findings = '주요 발견사항을 입력해 주세요.';
    } else if (formData.findings.trim().length < 30) {
      newErrors.findings = '주요 발견사항은 30자 이상 입력해 주세요.';
    }

    if (!formData.conclusion.trim()) {
      newErrors.conclusion = '결론을 입력해 주세요.';
    } else if (formData.conclusion.trim().length < 20) {
      newErrors.conclusion = '결론은 20자 이상 입력해 주세요.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  const handleSubmit = useCallback(async () => {
    if (!validate()) {
      return;
    }

    setIsSubmitting(true);
    setSuccess(false);

    try {
      const requestData: ReportRequest = {
        summary: formData.summary.trim(),
        findings: formData.findings.trim(),
        conclusion: formData.conclusion.trim(),
        attachments: formData.attachments.length > 0 ? formData.attachments : undefined,
      };

      const { data, error } = await submitReport(caseId, requestData);

      if (error) {
        onError?.(error);
        return;
      }

      if (data?.success) {
        setSuccess(true);
        onReportSubmitted?.(data.report_id);
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [caseId, formData, validate, onReportSubmitted, onError]);

  const handlePreview = useCallback(() => {
    setShowPreview((prev) => !prev);
  }, []);

  return (
    <div className={`bg-[var(--color-bg-secondary)] rounded-lg ${className}`}>
      {/* Header */}
      <div className="p-6 border-b border-[var(--color-border)]">
        <h2 className="text-xl font-semibold">조사 보고서 작성</h2>
        {caseTitle && (
          <p className="text-[var(--color-text-secondary)] mt-1">
            사건: {caseTitle}
          </p>
        )}
      </div>

      {/* Form */}
      <div className="p-6 space-y-6">
        {/* Summary */}
        <div>
          <label
            htmlFor="report-summary"
            className="block text-sm font-medium text-[var(--color-text-primary)] mb-2"
          >
            조사 요약 <span className="text-[var(--color-error)]">*</span>
          </label>
          <textarea
            id="report-summary"
            value={formData.summary}
            onChange={handleInputChange('summary')}
            placeholder="조사의 전반적인 내용을 요약해 주세요..."
            rows={4}
            className={`w-full px-4 py-3 border rounded-lg resize-none
              focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent
              ${errors.summary ? 'border-[var(--color-error)]' : 'border-[var(--color-border)]'}`}
          />
          <div className="flex justify-between mt-1">
            {errors.summary ? (
              <p className="text-sm text-[var(--color-error)]">{errors.summary}</p>
            ) : (
              <span />
            )}
            <span className="text-sm text-[var(--color-text-secondary)]">
              {formData.summary.length}자
            </span>
          </div>
        </div>

        {/* Findings */}
        <div>
          <label
            htmlFor="report-findings"
            className="block text-sm font-medium text-[var(--color-text-primary)] mb-2"
          >
            주요 발견사항 <span className="text-[var(--color-error)]">*</span>
          </label>
          <textarea
            id="report-findings"
            value={formData.findings}
            onChange={handleInputChange('findings')}
            placeholder="조사 중 발견한 주요 사실들을 기술해 주세요..."
            rows={6}
            className={`w-full px-4 py-3 border rounded-lg resize-none
              focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent
              ${errors.findings ? 'border-[var(--color-error)]' : 'border-[var(--color-border)]'}`}
          />
          <div className="flex justify-between mt-1">
            {errors.findings ? (
              <p className="text-sm text-[var(--color-error)]">{errors.findings}</p>
            ) : (
              <span />
            )}
            <span className="text-sm text-[var(--color-text-secondary)]">
              {formData.findings.length}자
            </span>
          </div>
        </div>

        {/* Conclusion */}
        <div>
          <label
            htmlFor="report-conclusion"
            className="block text-sm font-medium text-[var(--color-text-primary)] mb-2"
          >
            결론 <span className="text-[var(--color-error)]">*</span>
          </label>
          <textarea
            id="report-conclusion"
            value={formData.conclusion}
            onChange={handleInputChange('conclusion')}
            placeholder="조사 결과에 대한 최종 결론을 작성해 주세요..."
            rows={4}
            className={`w-full px-4 py-3 border rounded-lg resize-none
              focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent
              ${errors.conclusion ? 'border-[var(--color-error)]' : 'border-[var(--color-border)]'}`}
          />
          <div className="flex justify-between mt-1">
            {errors.conclusion ? (
              <p className="text-sm text-[var(--color-error)]">{errors.conclusion}</p>
            ) : (
              <span />
            )}
            <span className="text-sm text-[var(--color-text-secondary)]">
              {formData.conclusion.length}자
            </span>
          </div>
        </div>

        {/* Attachments */}
        <div>
          <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">
            첨부 파일
          </label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
            onChange={handleFileSelect}
            className="hidden"
            id="attachment-input"
            multiple
          />
          <label
            htmlFor="attachment-input"
            className="flex items-center justify-center w-full py-4 border-2 border-dashed
              border-[var(--color-border)] rounded-lg cursor-pointer
              hover:border-[var(--color-primary)] transition-colors"
          >
            <div className="flex items-center gap-2 text-[var(--color-text-secondary)]">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
              </svg>
              <span>파일 첨부하기</span>
            </div>
          </label>

          {formData.attachments.length > 0 && (
            <ul className="mt-3 space-y-2">
              {formData.attachments.map((attachment, index) => (
                <li
                  key={index}
                  className="flex items-center justify-between p-3 bg-white rounded-lg border border-[var(--color-border)]"
                >
                  <div className="flex items-center gap-2 truncate">
                    <svg className="w-5 h-5 text-[var(--color-text-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span className="truncate">{attachment}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRemoveAttachment(index)}
                    className="p-1 text-[var(--color-error)] hover:bg-red-50 rounded"
                    aria-label="첨부파일 제거"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Preview Toggle */}
        <button
          type="button"
          onClick={handlePreview}
          className="text-[var(--color-primary)] hover:underline text-sm"
        >
          {showPreview ? '미리보기 닫기' : '미리보기'}
        </button>

        {/* Preview Section */}
        {showPreview && (
          <div className="p-4 bg-white border border-[var(--color-border)] rounded-lg">
            <h4 className="font-semibold mb-4">보고서 미리보기</h4>
            <div className="space-y-4 text-sm">
              <div>
                <h5 className="font-medium text-[var(--color-text-secondary)]">조사 요약</h5>
                <p className="mt-1 whitespace-pre-wrap">{formData.summary || '(내용 없음)'}</p>
              </div>
              <div>
                <h5 className="font-medium text-[var(--color-text-secondary)]">주요 발견사항</h5>
                <p className="mt-1 whitespace-pre-wrap">{formData.findings || '(내용 없음)'}</p>
              </div>
              <div>
                <h5 className="font-medium text-[var(--color-text-secondary)]">결론</h5>
                <p className="mt-1 whitespace-pre-wrap">{formData.conclusion || '(내용 없음)'}</p>
              </div>
              {formData.attachments.length > 0 && (
                <div>
                  <h5 className="font-medium text-[var(--color-text-secondary)]">첨부 파일</h5>
                  <ul className="mt-1 list-disc list-inside">
                    {formData.attachments.map((att, i) => (
                      <li key={i}>{att}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Footer Actions */}
      <div className="p-6 border-t border-[var(--color-border)] flex justify-end gap-3">
        <button
          type="button"
          className="px-6 py-3 border border-[var(--color-border)] rounded-lg
            text-[var(--color-text-primary)] hover:bg-[var(--color-bg-secondary)]
            min-h-[44px]"
        >
          임시 저장
        </button>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="px-6 py-3 bg-[var(--color-primary)] text-white rounded-lg
            font-medium hover:bg-[var(--color-primary-hover)]
            disabled:opacity-50 disabled:cursor-not-allowed
            min-h-[44px]"
        >
          {isSubmitting ? '제출 중...' : '보고서 제출'}
        </button>
      </div>

      {/* Success Message */}
      {success && (
        <div className="mx-6 mb-6 p-4 bg-green-50 text-green-700 rounded-lg">
          보고서가 성공적으로 제출되었습니다.
        </div>
      )}
    </div>
  );
}
