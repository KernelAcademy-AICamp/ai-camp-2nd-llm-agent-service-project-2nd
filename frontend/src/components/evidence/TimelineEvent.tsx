/**
 * TimelineEvent Component
 * Displays individual evidence item on timeline
 *
 * Feature: 002-evidence-timeline
 */

'use client';

import { TimelineEvent as TimelineEventType, TimelineEventType as EventType } from '@/types/timeline';
import { cn } from '@/lib/utils';

interface TimelineEventProps {
    event: TimelineEventType;
    onClick?: (event: TimelineEventType) => void;
}

/**
 * Get icon for event type
 */
function getEventTypeIcon(type: EventType): string {
    const icons: Record<EventType, string> = {
        message: '💬',
        document: '📄',
        image: '🖼️',
        audio: '🎵',
        video: '🎬',
        incident: '⚠️',
    };
    return icons[type] || '📄';
}

/**
 * Get label for event type in Korean
 */
function getEventTypeLabel(type: EventType): string {
    const labels: Record<EventType, string> = {
        message: '메시지',
        document: '문서',
        image: '이미지',
        audio: '오디오',
        video: '비디오',
        incident: '사건',
    };
    return labels[type] || '기타';
}

export function TimelineEvent({ event, onClick }: TimelineEventProps) {
    const handleClick = () => {
        if (onClick) {
            onClick(event);
        }
    };

    return (
        <div
            className={cn(
                'relative pl-8 pb-8 border-l-2 border-gray-200 last:pb-0',
                event.isKeyEvidence && 'border-l-amber-400'
            )}
            onClick={handleClick}
            role={onClick ? 'button' : undefined}
            tabIndex={onClick ? 0 : undefined}
            onKeyDown={(e) => {
                if (onClick && (e.key === 'Enter' || e.key === ' ')) {
                    e.preventDefault();
                    handleClick();
                }
            }}
        >
            {/* Timeline dot */}
            <div
                className={cn(
                    'absolute left-[-9px] top-0 w-4 h-4 rounded-full border-2 border-white',
                    event.isKeyEvidence
                        ? 'bg-amber-400 ring-2 ring-amber-200'
                        : 'bg-gray-400'
                )}
            />

            {/* Event card */}
            <div
                className={cn(
                    'bg-white rounded-lg border p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer',
                    event.isKeyEvidence && 'border-amber-300 bg-amber-50'
                )}
            >
                {/* Header */}
                <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                        <span className="text-lg" role="img" aria-label={getEventTypeLabel(event.eventType)}>
                            {getEventTypeIcon(event.eventType)}
                        </span>
                        <span className="text-sm font-medium text-gray-700">
                            {getEventTypeLabel(event.eventType)}
                        </span>
                        {event.isKeyEvidence && (
                            <span className="px-2 py-0.5 text-xs font-semibold bg-amber-100 text-amber-800 rounded-full">
                                핵심 증거
                            </span>
                        )}
                    </div>
                    <div className="text-right text-sm text-gray-500">
                        <div>{event.date}</div>
                        {event.time && <div className="text-xs">{event.time}</div>}
                    </div>
                </div>

                {/* Speaker badge */}
                {event.speaker && (
                    <div className="mb-2">
                        <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                            {event.speaker}
                        </span>
                    </div>
                )}

                {/* Description */}
                <p className="text-gray-800 mb-2">{event.description}</p>

                {/* Content preview */}
                {event.contentPreview && (
                    <p className="text-sm text-gray-600 italic border-l-2 border-gray-200 pl-2 mb-2">
                        &quot;{event.contentPreview}&quot;
                    </p>
                )}

                {/* Labels */}
                {event.labels.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-2">
                        {event.labels.map((label, index) => (
                            <span
                                key={index}
                                className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
                            >
                                {label}
                            </span>
                        ))}
                    </div>
                )}

                {/* Footer */}
                <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
                    <span className="truncate max-w-[200px]" title={event.sourceFile}>
                        {event.sourceFile}
                    </span>
                    <span className="flex items-center gap-1">
                        중요도:
                        {Array.from({ length: 5 }, (_, i) => (
                            <span
                                key={i}
                                className={cn(
                                    'w-2 h-2 rounded-full',
                                    i < event.significance ? 'bg-amber-400' : 'bg-gray-200'
                                )}
                            />
                        ))}
                    </span>
                </div>
            </div>
        </div>
    );
}
