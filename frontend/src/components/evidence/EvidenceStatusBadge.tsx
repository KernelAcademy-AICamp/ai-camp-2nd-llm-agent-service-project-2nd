/**
 * Reusable Evidence Status Badge Component
 * Pure presentational component - no business logic
 */

import { CheckCircle2, Clock, AlertCircle, Loader2 } from 'lucide-react';
import { EvidenceStatus } from '@/types/evidence';

interface EvidenceStatusBadgeProps {
  status: EvidenceStatus;
}

export function EvidenceStatusBadge({ status }: EvidenceStatusBadgeProps) {
  const statusConfig: Record<
    EvidenceStatus,
    { icon: React.ReactNode; label: string; className: string }
  > = {
    uploading: {
      icon: <Loader2 className="w-3 h-3 mr-1 animate-spin" />,
      label: '업로드 중',
      className: 'text-blue-600 bg-blue-50',
    },
    completed: {
      icon: <CheckCircle2 className="w-3 h-3 mr-1" />,
      label: '완료',
      className: 'text-success-green bg-green-50',
    },
    processing: {
      icon: <Loader2 className="w-3 h-3 mr-1 animate-spin" />,
      label: '분석 중',
      className: 'text-accent bg-teal-50',
    },
    queued: {
      icon: <Clock className="w-3 h-3 mr-1" />,
      label: '대기 중',
      className: 'text-gray-500 bg-gray-100',
    },
    review_needed: {
      icon: <AlertCircle className="w-3 h-3 mr-1" />,
      label: '검토 필요',
      className: 'text-orange-600 bg-orange-50',
    },
    failed: {
      icon: <AlertCircle className="w-3 h-3 mr-1" />,
      label: '실패',
      className: 'text-semantic-error bg-red-50',
    },
  };

  const config = statusConfig[status];

  return (
    <span
      className={`flex items-center text-xs font-medium px-2 py-1 rounded-full ${config.className}`}
    >
      {config.icon}
      {config.label}
    </span>
  );
}
