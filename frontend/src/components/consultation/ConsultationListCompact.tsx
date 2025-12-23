/**
 * ConsultationListCompact Component
 * Compact consultation list for DataPanel sidebar
 * LDS2 Compact density applied
 */

'use client';

import { Phone, Video, Users, Calendar } from 'lucide-react';
import type { Consultation, ConsultationType } from '@/types/consultation';

const CONSULTATION_TYPE_ICONS: Record<ConsultationType, typeof Phone> = {
  phone: Phone,
  in_person: Users,
  online: Video,
};

const CONSULTATION_TYPE_COLORS: Record<ConsultationType, string> = {
  phone: 'text-blue-500',
  in_person: 'text-green-500',
  online: 'text-purple-500',
};

interface ConsultationListCompactProps {
  consultations: Consultation[];
  onItemClick?: (consultation: Consultation) => void;
  maxItems?: number;
}

export function ConsultationListCompact({
  consultations,
  onItemClick,
  maxItems = 5,
}: ConsultationListCompactProps) {
  const displayItems = consultations.slice(0, maxItems);

  if (displayItems.length === 0) {
    return (
      <div className="text-xs text-[var(--color-text-secondary)] py-2">
        상담내역이 없습니다.
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {displayItems.map((consultation) => {
        const Icon = CONSULTATION_TYPE_ICONS[consultation.type];
        const iconColor = CONSULTATION_TYPE_COLORS[consultation.type];

        return (
          <div
            key={consultation.id}
            onClick={() => onItemClick?.(consultation)}
            className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-100 dark:hover:bg-neutral-700 cursor-pointer transition-colors"
          >
            <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${iconColor}`} />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-[var(--color-text-primary)] truncate">
                {consultation.summary.length > 30
                  ? `${consultation.summary.substring(0, 30)}...`
                  : consultation.summary}
              </p>
              <div className="flex items-center gap-1 text-[10px] text-[var(--color-text-secondary)]">
                <Calendar className="w-2.5 h-2.5" />
                <span>{consultation.date}</span>
                {consultation.participants.length > 0 && (
                  <span className="truncate">
                    · {consultation.participants[0]}
                    {consultation.participants.length > 1 && ` 외 ${consultation.participants.length - 1}명`}
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
      {consultations.length > maxItems && (
        <p className="text-[10px] text-[var(--color-text-secondary)] text-center py-1">
          +{consultations.length - maxItems}건 더보기
        </p>
      )}
    </div>
  );
}

export default ConsultationListCompact;
