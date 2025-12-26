/**
 * PartyModal - Modal for adding/editing party nodes
 * User Story 1: Party Relationship Graph
 */

'use client';

import { useState, useEffect, useId } from 'react';
import type {
  PartyNode,
  PartyType,
  PartyNodeCreate,
  PartyNodeUpdate,
} from '@/types/party';
import { PARTY_TYPE_LABELS } from '@/types/party';

interface PartyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: PartyNodeCreate | PartyNodeUpdate) => Promise<void>;
  party?: PartyNode | null; // null for new party, object for edit
  defaultPosition?: { x: number; y: number };
}

const PARTY_TYPES: PartyType[] = [
  'plaintiff',
  'defendant',
  'third_party',
  'child',
  'family',
];

export function PartyModal({
  isOpen,
  onClose,
  onSave,
  party,
  defaultPosition = { x: 250, y: 250 },
}: PartyModalProps) {
  const isEditMode = !!party;

  const [formData, setFormData] = useState<{
    type: PartyType;
    name: string;
    alias: string;
    birth_year: string;
    occupation: string;
  }>({
    type: 'plaintiff',
    name: '',
    alias: '',
    birth_year: '',
    occupation: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const titleId = useId();

  // Reset form when modal opens/closes or party changes
  useEffect(() => {
    if (isOpen) {
      if (party) {
        setFormData({
          type: party.type,
          name: party.name,
          alias: party.alias || '',
          birth_year: party.birth_year?.toString() || '',
          occupation: party.occupation || '',
        });
      } else {
        setFormData({
          type: 'plaintiff',
          name: '',
          alias: '',
          birth_year: '',
          occupation: '',
        });
      }
      setError(null);
    }
  }, [isOpen, party]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.name.trim()) {
      setError('이름을 입력해주세요.');
      return;
    }

    setIsSubmitting(true);

    try {
      const birthYear = formData.birth_year
        ? parseInt(formData.birth_year, 10)
        : undefined;

      if (isEditMode) {
        // Edit mode - only send changed fields
        const updateData: PartyNodeUpdate = {
          name: formData.name.trim(),
          alias: formData.alias.trim() || undefined,
          birth_year: birthYear,
          occupation: formData.occupation.trim() || undefined,
        };
        await onSave(updateData);
      } else {
        // Create mode
        const createData: PartyNodeCreate = {
          type: formData.type,
          name: formData.name.trim(),
          alias: formData.alias.trim() || undefined,
          birth_year: birthYear,
          occupation: formData.occupation.trim() || undefined,
          position: defaultPosition,
        };
        await onSave(createData);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '저장에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative bg-white dark:bg-neutral-800 rounded-lg shadow-xl w-full max-w-md mx-4"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200 dark:border-neutral-700">
          <h2 id={titleId} className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            {isEditMode ? '당사자 수정' : '당사자 추가'}
          </h2>
          <button
            onClick={onClose}
            aria-label="닫기"
            className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div className="px-6 py-4 space-y-4">
            {/* Error message */}
            {error && (
              <div className="p-3 text-sm text-red-600 bg-red-50 rounded-lg">
                {error}
              </div>
            )}

            {/* Type (only for create mode) */}
            {!isEditMode && (
              <div>
                <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                  유형 <span className="text-error">*</span>
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {PARTY_TYPES.map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setFormData({ ...formData, type })}
                      className={`
                        px-3 py-2 text-sm rounded-lg border transition-colors
                        ${formData.type === type
                          ? 'border-info bg-info-light text-info'
                          : 'border-neutral-200 hover:border-neutral-300 dark:border-neutral-600 dark:hover:border-neutral-500'
                        }
                      `}
                    >
                      {PARTY_TYPE_LABELS[type]}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Name */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                이름 <span className="text-error">*</span>
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary dark:bg-neutral-800 dark:border-neutral-600 dark:text-white"
                placeholder="실명 또는 가명"
                autoFocus
              />
            </div>

            {/* Alias */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                소장용 가명
              </label>
              <input
                type="text"
                value={formData.alias}
                onChange={(e) => setFormData({ ...formData, alias: e.target.value })}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary dark:bg-neutral-800 dark:border-neutral-600 dark:text-white"
                placeholder="예: 김○○"
              />
            </div>

            {/* Birth year */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                출생년도
              </label>
              <input
                type="number"
                value={formData.birth_year}
                onChange={(e) => setFormData({ ...formData, birth_year: e.target.value })}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary dark:bg-neutral-800 dark:border-neutral-600 dark:text-white"
                placeholder="예: 1985"
                min={1900}
                max={new Date().getFullYear()}
              />
            </div>

            {/* Occupation */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                직업
              </label>
              <input
                type="text"
                value={formData.occupation}
                onChange={(e) => setFormData({ ...formData, occupation: e.target.value })}
                className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary dark:bg-neutral-800 dark:border-neutral-600 dark:text-white"
                placeholder="예: 회사원"
              />
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 px-6 py-4 border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 rounded-b-lg">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-lg"
              disabled={isSubmitting}
            >
              취소
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-lg disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? '저장 중...' : isEditMode ? '수정' : '추가'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
