/**
 * ConsultationModal - Independent Consultation Add/Edit Modal
 * Extracted from ConsultationHistoryTab for use anywhere in the app
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { X, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import type { Consultation, ConsultationType } from '@/types/consultation';
import { createConsultation, updateConsultation } from '@/lib/api/consultation';

interface ConsultationModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseId: string;
  consultation?: Consultation; // For editing
  onSuccess?: () => void;
}

export function ConsultationModal({
  isOpen,
  onClose,
  caseId,
  consultation,
  onSuccess,
}: ConsultationModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    date: '',
    time: '',
    type: 'phone' as ConsultationType,
    participants: '',
    summary: '',
    notes: '',
  });

  // Reset form when modal opens/closes or consultation changes
  useEffect(() => {
    if (isOpen) {
      if (consultation) {
        setFormData({
          date: consultation.date,
          time: consultation.time ? consultation.time.substring(0, 5) : '',
          type: consultation.type,
          participants: consultation.participants.join(', '),
          summary: consultation.summary,
          notes: consultation.notes || '',
        });
      } else {
        setFormData({
          date: '',
          time: '',
          type: 'phone',
          participants: '',
          summary: '',
          notes: '',
        });
      }
    }
  }, [isOpen, consultation]);

  const handleClose = useCallback(() => {
    setFormData({
      date: '',
      time: '',
      type: 'phone',
      participants: '',
      summary: '',
      notes: '',
    });
    onClose();
  }, [onClose]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.date || !formData.summary) {
      toast.error('날짜와 요약은 필수입니다.');
      return;
    }

    const participantsList = formData.participants
      .split(',')
      .map(p => p.trim())
      .filter(p => p.length > 0);

    setIsSubmitting(true);

    try {
      if (consultation) {
        // Update existing consultation
        const response = await updateConsultation(caseId, consultation.id, {
          date: formData.date,
          time: formData.time || undefined,
          type: formData.type,
          participants: participantsList,
          summary: formData.summary,
          notes: formData.notes || undefined,
        });

        if (response.data) {
          toast.success('상담내역이 수정되었습니다.');
          onSuccess?.();
          handleClose();
        } else if (response.error) {
          toast.error(response.error);
        }
      } else {
        // Create new consultation
        const response = await createConsultation(caseId, {
          date: formData.date,
          time: formData.time || undefined,
          type: formData.type,
          participants: participantsList,
          summary: formData.summary,
          notes: formData.notes || undefined,
        });

        if (response.data) {
          toast.success('상담내역이 추가되었습니다.');
          onSuccess?.();
          handleClose();
        } else if (response.error) {
          toast.error(response.error);
        }
      }
    } catch {
      toast.error('저장에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  }, [caseId, formData, consultation, onSuccess, handleClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-xl w-full max-w-lg mx-4">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-neutral-700">
          <h4 className="text-lg font-semibold text-[var(--color-text-primary)]">
            {consultation ? '상담내역 수정' : '상담 추가'}
          </h4>
          <button
            onClick={handleClose}
            className="p-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Date and Time */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1">
                날짜 <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={formData.date}
                onChange={(e) => setFormData(prev => ({ ...prev, date: e.target.value }))}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1">
                시간
              </label>
              <input
                type="time"
                value={formData.time}
                onChange={(e) => setFormData(prev => ({ ...prev, time: e.target.value }))}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
              />
            </div>
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1">
              상담 유형
            </label>
            <select
              value={formData.type}
              onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value as ConsultationType }))}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            >
              <option value="phone">전화 상담</option>
              <option value="in_person">대면 상담</option>
              <option value="online">화상 상담</option>
            </select>
          </div>

          {/* Participants */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1">
              참석자 (쉼표로 구분)
            </label>
            <input
              type="text"
              value={formData.participants}
              onChange={(e) => setFormData(prev => ({ ...prev, participants: e.target.value }))}
              placeholder="홍길동, 김변호사"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
            />
          </div>

          {/* Summary */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1">
              요약 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.summary}
              onChange={(e) => setFormData(prev => ({ ...prev, summary: e.target.value }))}
              placeholder="상담 내용 요약을 입력하세요"
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] resize-none"
              required
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1">
              메모
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="추가 메모 (선택)"
              rows={2}
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] resize-none"
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-100 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] transition-colors disabled:opacity-50 flex items-center"
            >
              {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {consultation ? '수정' : '추가'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ConsultationModal;
