/**
 * AI Summary Modal Component
 * Extracted from EvidenceDataTable.tsx for better code organization
 * Uses Modal primitive for consistent accessibility and behavior
 */

'use client';

import { Sparkles } from 'lucide-react';
import { Modal } from '@/components/primitives/Modal/Modal';
import { Button } from '@/components/primitives/Button/Button';
import type { Evidence } from '@/types/evidence';

interface AISummaryModalProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: Evidence | null;
}

export function AISummaryModal({ isOpen, onClose, evidence }: AISummaryModalProps) {
  if (!evidence) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="AI 요약"
      size="lg"
      footer={
        <Button variant="secondary" onClick={onClose}>
          닫기
        </Button>
      }
    >
      <div className="space-y-4">
        {/* File info */}
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <span className="text-sm font-medium text-neutral-500 dark:text-neutral-400">파일명</span>
          </div>
          <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
            {evidence.filename}
          </p>
        </div>

        {/* Summary content */}
        <div className="bg-neutral-50 dark:bg-neutral-700 rounded-lg p-4">
          <p className="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed whitespace-pre-wrap">
            {evidence.summary || '요약이 아직 생성되지 않았습니다.'}
          </p>
        </div>
      </div>
    </Modal>
  );
}

export default AISummaryModal;
