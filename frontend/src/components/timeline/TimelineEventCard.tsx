'use client';

import React from 'react';
import {
  TimelineEvent,
  TimelineEventType,
  getEventTypeIcon,
  getEventTypeLabel,
  getSignificanceColor
} from '@/types/timeline';
import { MessageSquare, FileText, Image, Mic, Video, AlertTriangle, Pin } from 'lucide-react';

interface TimelineEventCardProps {
  event: TimelineEvent;
  isSelected?: boolean;
  onClick?: (event: TimelineEvent) => void;
  onPin?: (event: TimelineEvent) => void;
}

const eventTypeIcons: Record<TimelineEventType, React.ReactNode> = {
  [TimelineEventType.MESSAGE]: <MessageSquare className="w-4 h-4" />,
  [TimelineEventType.DOCUMENT]: <FileText className="w-4 h-4" />,
  [TimelineEventType.IMAGE]: <Image className="w-4 h-4" />,
  [TimelineEventType.AUDIO]: <Mic className="w-4 h-4" />,
  [TimelineEventType.VIDEO]: <Video className="w-4 h-4" />,
  [TimelineEventType.INCIDENT]: <AlertTriangle className="w-4 h-4" />,
};

export default function TimelineEventCard({
  event,
  isSelected = false,
  onClick,
  onPin,
}: TimelineEventCardProps) {
  const significanceColor = getSignificanceColor(event.significance);

  return (
    <div
      className={`
        relative p-4 rounded-lg border transition-all cursor-pointer
        ${isSelected
          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
        }
        ${event.is_key_evidence ? 'ring-2 ring-red-200 dark:ring-red-800' : ''}
      `}
      onClick={() => onClick?.(event)}
    >
      {/* 핀 표시 */}
      {event.is_pinned && (
        <div className="absolute -top-2 -right-2 bg-yellow-400 rounded-full p-1">
          <Pin className="w-3 h-3 text-white" />
        </div>
      )}

      {/* 헤더 */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {/* 시간 */}
          <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {event.time}
          </span>

          {/* 이벤트 타입 아이콘 */}
          <span className="text-gray-500" title={getEventTypeLabel(event.event_type)}>
            {eventTypeIcons[event.event_type]}
          </span>

          {/* 화자 */}
          {event.speaker && (
            <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
              {event.speaker}
            </span>
          )}
        </div>

        {/* 중요도 */}
        <div className="flex items-center gap-1">
          {event.is_key_evidence && (
            <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 rounded">
              핵심 증거
            </span>
          )}
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: significanceColor }}
            title={`중요도: ${event.significance}/5`}
          />
        </div>
      </div>

      {/* 내용 */}
      <p className="text-sm text-gray-800 dark:text-gray-200 mb-2 line-clamp-2">
        {event.description}
      </p>

      {/* 라벨 */}
      {event.labels.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-2">
          {event.labels.map((label, idx) => (
            <span
              key={idx}
              className="text-xs px-2 py-0.5 bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 rounded"
            >
              {label}
            </span>
          ))}
        </div>
      )}

      {/* 출처 */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-500">
        <span className="truncate max-w-[200px]" title={event.source_file}>
          📎 {event.source_file}
        </span>

        {onPin && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onPin(event);
            }}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
            title={event.is_pinned ? '핀 해제' : '핀 고정'}
          >
            <Pin className={`w-3 h-3 ${event.is_pinned ? 'text-yellow-500' : ''}`} />
          </button>
        )}
      </div>
    </div>
  );
}
