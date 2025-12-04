'use client';

/**
 * PersonDetailModal Component
 * Modal for displaying person details when clicking a node
 */

import { X, User, Users } from 'lucide-react';
import { Button } from '@/components/primitives';
import { PersonNode, ROLE_LABELS } from '@/types/relationship';

interface PersonDetailModalProps {
  person: PersonNode;
  isOpen: boolean;
  onClose: () => void;
}

const SIDE_LABELS: Record<string, string> = {
  plaintiff_side: '원고 측',
  defendant_side: '피고 측',
  neutral: '중립',
  unknown: '미상',
};

export default function PersonDetailModal({
  person,
  isOpen,
  onClose,
}: PersonDetailModalProps) {
  if (!isOpen) return null;

  const roleLabel = ROLE_LABELS[person.role] || '미상';
  const sideLabel = SIDE_LABELS[person.side] || '미상';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="person-modal-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal Content */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        {/* Header */}
        <div
          className="px-6 py-4 flex items-center justify-between"
          style={{ backgroundColor: person.color }}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2
                id="person-modal-title"
                className="text-lg font-bold text-white"
              >
                {person.name}
              </h2>
              <p className="text-sm text-white/80">{roleLabel}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-full transition-colors"
            aria-label="닫기"
          >
            <X className="w-5 h-5 text-white" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">
          {/* Role Info */}
          <div className="flex items-center gap-3 p-3 bg-neutral-50 rounded-lg">
            <Users className="w-5 h-5 text-neutral-500" />
            <div>
              <p className="text-sm text-neutral-500">소속</p>
              <p className="font-medium text-neutral-900">{sideLabel}</p>
            </div>
          </div>

          {/* Role Badge */}
          <div>
            <p className="text-sm text-neutral-500 mb-2">역할</p>
            <span
              className="inline-block px-3 py-1.5 rounded-full text-sm font-medium text-white"
              style={{ backgroundColor: person.color }}
            >
              {roleLabel}
            </span>
          </div>

          {/* Info Message */}
          <div className="text-sm text-neutral-500 bg-neutral-50 rounded-lg p-3">
            <p>
              이 인물은 업로드된 증거 자료에서 AI가 자동으로 추출한 정보입니다.
              실제 관계와 다를 수 있으니 확인이 필요합니다.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t bg-neutral-50 flex justify-end">
          <Button variant="outline" onClick={onClose}>
            닫기
          </Button>
        </div>
      </div>
    </div>
  );
}
