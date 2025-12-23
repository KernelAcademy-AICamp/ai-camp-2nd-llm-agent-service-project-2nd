'use client';

/**
 * EvidenceListCompact - Compact Evidence List with Legal Numbering
 * 014-ui-settings-completion Feature
 *
 * Displays evidence in compact format with:
 * - Legal numbering (갑제1호증, 을제1호증, 병제1호증)
 * - Timestamp display
 * - Status indicator
 */

import { FileText, Image, Music, Video, FileType, Clock, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { Evidence, EvidenceType, EvidenceStatus } from '@/types/evidence';

// Legal party types for evidence numbering
export type EvidenceParty = 'plaintiff' | 'defendant' | 'third_party';

// Extended evidence with legal numbering
export interface LegalEvidence extends Evidence {
  legalNumber?: string;      // "갑제1호증"
  submittedBy?: EvidenceParty;
  evidenceTimestamp?: string; // 증거 발생 시점
}

interface EvidenceListCompactProps {
  items: LegalEvidence[];
  onItemClick?: (evidence: LegalEvidence) => void;
  emptyMessage?: string;
}

// Get legal prefix based on party
function getLegalPrefix(party: EvidenceParty | undefined): string {
  switch (party) {
    case 'plaintiff':
      return '갑';
    case 'defendant':
      return '을';
    case 'third_party':
      return '병';
    default:
      return '갑'; // Default to plaintiff
  }
}

// Generate legal number based on party and sequence
export function generateLegalNumber(party: EvidenceParty, sequence: number): string {
  const prefix = getLegalPrefix(party);
  return `${prefix}제${sequence}호증`;
}

// Get file type icon
function getTypeIcon(type: EvidenceType) {
  switch (type) {
    case 'image':
      return <Image className="w-3.5 h-3.5" />;
    case 'audio':
      return <Music className="w-3.5 h-3.5" />;
    case 'video':
      return <Video className="w-3.5 h-3.5" />;
    case 'pdf':
      return <FileType className="w-3.5 h-3.5" />;
    case 'text':
    default:
      return <FileText className="w-3.5 h-3.5" />;
  }
}

// Get status indicator
function getStatusIndicator(status: EvidenceStatus) {
  switch (status) {
    case 'completed':
      return <CheckCircle className="w-3.5 h-3.5 text-green-500" />;
    case 'processing':
    case 'queued':
      return <Loader2 className="w-3.5 h-3.5 text-blue-500 animate-spin" />;
    case 'failed':
      return <AlertCircle className="w-3.5 h-3.5 text-red-500" />;
    default:
      return <Clock className="w-3.5 h-3.5 text-gray-400" />;
  }
}

// Format timestamp for display
function formatTimestamp(timestamp: string | undefined): string {
  if (!timestamp) return '-';
  try {
    const date = new Date(timestamp);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  } catch {
    return '-';
  }
}

export function EvidenceListCompact({
  items,
  onItemClick,
  emptyMessage = '등록된 증거가 없습니다.',
}: EvidenceListCompactProps) {
  if (items.length === 0) {
    return (
      <div className="py-3 text-center text-xs text-[var(--color-text-secondary)]">
        {emptyMessage}
      </div>
    );
  }

  return (
    <ul className="space-y-px">
      {items.map((item, index) => {
        // Generate legal number if not provided
        const legalNumber = item.legalNumber || generateLegalNumber(item.submittedBy || 'plaintiff', index + 1);

        return (
          <li key={item.id}>
            <button
              onClick={() => onItemClick?.(item)}
              className="w-full flex items-center gap-1.5 px-2 py-1.5 rounded text-left transition-colors duration-100 group
                hover:bg-gray-100 dark:hover:bg-neutral-700
                active:bg-gray-200 dark:active:bg-neutral-600
                focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)] focus:ring-inset"
            >
              {/* Status Indicator */}
              <span className="flex-shrink-0">
                {getStatusIndicator(item.status)}
              </span>

              {/* Legal Number */}
              <span className="flex-shrink-0 text-[10px] font-mono font-medium text-[var(--color-primary)]">
                {legalNumber}
              </span>

              {/* File Type Icon */}
              <span className="flex-shrink-0 text-[var(--color-text-secondary)]">
                {getTypeIcon(item.type)}
              </span>

              {/* Filename (truncated with ellipsis) */}
              <span className="flex-1 text-xs text-[var(--color-text-primary)] truncate">
                {item.filename}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}

export default EvidenceListCompact;
