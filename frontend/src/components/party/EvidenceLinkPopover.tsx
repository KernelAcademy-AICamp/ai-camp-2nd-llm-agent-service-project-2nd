/**
 * EvidenceLinkPopover - Popover showing evidence linked to a party
 * User Story 4: Evidence-Party Linking
 */

'use client';

import { useState, useId } from 'react';
import type { EvidencePartyLink, PartyNode, LinkType } from '@/types/party';
import { LINK_TYPE_LABELS } from '@/types/party';

interface EvidenceLinkPopoverProps {
  party: PartyNode;
  links: EvidencePartyLink[];
  isLoading: boolean;
  onClose: () => void;
  onLinkEvidence: () => void;
  onRemoveLink: (linkId: string) => Promise<void>;
  onViewEvidence: (evidenceId: string) => void;
}

// Badge colors for link types - using semantic design tokens
const LINK_TYPE_COLORS: Record<LinkType, string> = {
  mentions: 'bg-info-light text-info',
  proves: 'bg-success-light text-success',
  involves: 'bg-warning-light text-warning',
  contradicts: 'bg-error-light text-error',
};

export function EvidenceLinkPopover({
  party,
  links,
  isLoading,
  onClose,
  onLinkEvidence,
  onRemoveLink,
  onViewEvidence,
}: EvidenceLinkPopoverProps) {
  const [removingId, setRemovingId] = useState<string | null>(null);
  const popoverId = useId();

  const handleRemove = async (linkId: string) => {
    setRemovingId(linkId);
    try {
      await onRemoveLink(linkId);
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div
      role="dialog"
      aria-labelledby={popoverId}
      className="absolute z-50 w-80 bg-white dark:bg-neutral-800 rounded-lg shadow-xl border border-neutral-200 dark:border-neutral-700"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-neutral-200 dark:border-neutral-700">
        <div>
          <h3 id={popoverId} className="font-medium text-neutral-900 dark:text-neutral-100">{party.name}</h3>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">연결된 증거</p>
        </div>
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

      {/* Content */}
      <div className="max-h-64 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-neutral-500 dark:text-neutral-400">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto mb-2" />
            불러오는 중...
          </div>
        ) : links.length === 0 ? (
          <div className="p-4 text-center text-neutral-500 dark:text-neutral-400">
            <p className="mb-2">연결된 증거가 없습니다</p>
          </div>
        ) : (
          <ul className="divide-y divide-neutral-200 dark:divide-neutral-700">
            {links.map((link) => (
              <li
                key={link.id}
                className="px-4 py-3 hover:bg-neutral-50 dark:hover:bg-neutral-700 flex items-start gap-3"
              >
                <div className="flex-1 min-w-0">
                  <button
                    onClick={() => onViewEvidence(link.evidence_id)}
                    className="text-sm font-medium text-info hover:underline truncate block w-full text-left"
                  >
                    증거 #{link.evidence_id.slice(0, 8)}
                  </button>
                  <span className={`inline-block mt-1 px-2 py-0.5 text-xs rounded-full ${LINK_TYPE_COLORS[link.link_type]}`}>
                    {LINK_TYPE_LABELS[link.link_type]}
                  </span>
                </div>
                <button
                  onClick={() => handleRemove(link.id)}
                  disabled={removingId === link.id}
                  aria-label="연결 해제"
                  className="text-neutral-400 hover:text-error disabled:opacity-50"
                >
                  {removingId === link.id ? (
                    <div className="w-4 h-4 animate-spin rounded-full border-2 border-neutral-300 border-t-neutral-600" />
                  ) : (
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 rounded-b-lg">
        <button
          onClick={onLinkEvidence}
          className="w-full px-4 py-2 text-sm font-medium text-info hover:bg-info-light rounded-lg transition-colors"
        >
          + 증거 연결하기
        </button>
      </div>
    </div>
  );
}
