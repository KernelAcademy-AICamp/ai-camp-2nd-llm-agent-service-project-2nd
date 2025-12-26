/**
 * Evidence Content Modal Component (원문 보기)
 * Extracted from EvidenceDataTable.tsx for better code organization
 * Uses Modal primitive for consistent accessibility and behavior
 *
 * Features:
 * - Display original evidence content
 * - Loading state while fetching
 * - Speaker mapping button integration (015-evidence-speaker-mapping)
 */

'use client';

import { FileText, Users } from 'lucide-react';
import { Modal } from '@/components/primitives/Modal/Modal';
import { Button } from '@/components/primitives/Button/Button';
import { Spinner } from '@/components/primitives/Spinner/Spinner';
import type { Evidence } from '@/types/evidence';

interface ContentModalProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: Evidence | null;
  content: string | null;
  isLoading: boolean;
  /** 015-evidence-speaker-mapping: 화자 매핑 버튼 표시 여부 */
  showSpeakerMappingButton?: boolean;
  /** 015-evidence-speaker-mapping: 화자 매핑 버튼 클릭 핸들러 */
  onOpenSpeakerMapping?: () => void;
}

export function ContentModal({
  isOpen,
  onClose,
  evidence,
  content,
  isLoading,
  showSpeakerMappingButton,
  onOpenSpeakerMapping,
}: ContentModalProps) {
  if (!evidence) return null;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="증거 원문"
      size="xl"
      footer={
        <div className="flex justify-between w-full">
          {/* Speaker mapping button */}
          <div>
            {showSpeakerMappingButton && content && (
              <Button
                variant="secondary"
                onClick={onOpenSpeakerMapping}
                aria-label="화자 매핑"
                className="text-info bg-info-light hover:bg-info-light/80"
              >
                <Users className="w-4 h-4 mr-2" />
                화자 매핑
              </Button>
            )}
          </div>
          <Button variant="secondary" onClick={onClose}>
            닫기
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* File info header */}
        <div className="flex items-center gap-2 pb-3 border-b border-neutral-200 dark:border-neutral-700">
          <FileText className="w-5 h-5 text-secondary" />
          <div>
            <p className="text-sm text-neutral-500 dark:text-neutral-400">파일명</p>
            <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100">
              {evidence.filename}
            </p>
          </div>
        </div>

        {/* Content area */}
        <div className="min-h-[200px]">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner size="md" className="text-neutral-400" />
              <span className="ml-2 text-neutral-500 dark:text-neutral-400">
                원문을 불러오는 중...
              </span>
            </div>
          ) : content ? (
            <pre className="text-sm text-neutral-700 dark:text-neutral-300 leading-relaxed whitespace-pre-wrap font-sans">
              {content}
            </pre>
          ) : (
            <div className="text-center py-12 text-neutral-500 dark:text-neutral-400">
              <FileText className="w-12 h-12 mx-auto mb-3 text-neutral-300 dark:text-neutral-600" />
              <p>원문이 아직 추출되지 않았습니다.</p>
              <p className="text-xs mt-1">AI 분석이 완료되면 원문을 볼 수 있습니다.</p>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}

export default ContentModal;
