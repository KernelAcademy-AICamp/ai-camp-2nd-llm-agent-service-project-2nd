/**
 * Timeline Component
 * Displays evidence items on a chronological timeline
 *
 * Enhanced for Feature: 002-evidence-timeline
 * Supports both legacy Evidence[] and new TimelineEvent[] formats
 */

import { Evidence } from '@/types/evidence';
import { TimelineEvent as TimelineEventType } from '@/types/timeline';
import { Clock, FileText, Image, Mic, Video, File, ArrowUp, ArrowDown, Loader2 } from 'lucide-react';
import TimelineEventComponent from './TimelineEvent';

const dateFormatter = new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
});

// Legacy props (backward compatibility)
interface LegacyTimelineProps {
    items: Evidence[];
    events?: never;
    onSelect: (id: string) => void;
    sortOrder?: 'asc' | 'desc';
    isLoading?: boolean;
    showSignificance?: boolean;
}

// New props with TimelineEvent[]
interface NewTimelineProps {
    items?: never;
    events: TimelineEventType[];
    onSelect: (id: string) => void;
    sortOrder?: 'asc' | 'desc';
    isLoading?: boolean;
    showSignificance?: boolean;
}

type TimelineProps = LegacyTimelineProps | NewTimelineProps;

/**
 * Get type icon for legacy Evidence format
 */
function getTypeIcon(type: string) {
    const iconClass = 'w-4 h-4';
    switch (type) {
        case 'text':
            return <FileText className={iconClass} />;
        case 'image':
            return <Image className={iconClass} />;
        case 'audio':
            return <Mic className={iconClass} />;
        case 'video':
            return <Video className={iconClass} />;
        default:
            return <File className={iconClass} />;
    }
}

/**
 * Empty state component
 */
function EmptyState() {
    return (
        <div className="text-center py-10 text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="text-lg font-medium mb-1">표시할 타임라인이 없습니다</p>
            <p className="text-sm">증거를 업로드하면 타임라인에 표시됩니다.</p>
        </div>
    );
}

/**
 * Loading state component
 */
function LoadingState() {
    return (
        <div className="flex items-center justify-center py-10">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400 mr-2" />
            <span className="text-gray-500">타임라인을 불러오는 중...</span>
        </div>
    );
}

/**
 * Legacy timeline item renderer (for Evidence[] format)
 */
function LegacyTimelineItem({
    item,
    onSelect,
}: {
    item: Evidence;
    onSelect: (id: string) => void;
}) {
    return (
        <div className="relative pl-8 group">
            {/* Dot on the line */}
            <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-white border-2 border-gray-300 group-hover:border-accent transition-colors" />

            <div
                onClick={() => onSelect(item.id)}
                className="cursor-pointer hover:bg-gray-50 p-3 rounded-lg transition-colors -mt-2"
            >
                <div className="flex items-center text-sm text-gray-500 mb-1">
                    <Clock className="w-3 h-3 mr-1" />
                    <time>{dateFormatter.format(new Date(item.uploadDate))}</time>
                </div>

                <h4 className="text-base font-medium text-gray-900 mb-1">
                    {item.summary || item.filename}
                </h4>

                <div className="flex items-center text-xs text-gray-400">
                    <span className="mr-2 flex items-center">
                        {getTypeIcon(item.type)}
                        <span className="ml-1 capitalize">{item.type}</span>
                    </span>
                </div>
            </div>
        </div>
    );
}

/**
 * Group events by date for better visual organization
 */
function groupEventsByDate(events: TimelineEventType[]): Map<string, TimelineEventType[]> {
    const groups = new Map<string, TimelineEventType[]>();

    for (const event of events) {
        const dateKey = event.date;
        if (!groups.has(dateKey)) {
            groups.set(dateKey, []);
        }
        groups.get(dateKey)!.push(event);
    }

    return groups;
}

export default function Timeline(props: TimelineProps) {
    const { onSelect, sortOrder = 'asc', isLoading = false, showSignificance = true } = props;

    // Loading state
    if (isLoading) {
        return <LoadingState />;
    }

    // Check if using new TimelineEvent format
    const isNewFormat = 'events' in props && props.events !== undefined;

    if (isNewFormat) {
        // New format: TimelineEvent[]
        const events = props.events!;

        if (events.length === 0) {
            return <EmptyState />;
        }

        // Sort events - they should already be sorted from API, but ensure consistency
        const sortedEvents = [...events].sort((a, b) => {
            // Put unknown dates at the end
            if (a.date === '날짜 미상' && b.date !== '날짜 미상') return 1;
            if (b.date === '날짜 미상' && a.date !== '날짜 미상') return -1;
            if (a.date === '날짜 미상' && b.date === '날짜 미상') {
                return a.eventId.localeCompare(b.eventId);
            }

            const dateCompare = a.date.localeCompare(b.date);
            if (dateCompare !== 0) {
                return sortOrder === 'asc' ? dateCompare : -dateCompare;
            }

            // Secondary sort by time
            const timeA = a.time || '00:00';
            const timeB = b.time || '00:00';
            const timeCompare = timeA.localeCompare(timeB);
            return sortOrder === 'asc' ? timeCompare : -timeCompare;
        });

        // Group events by date for date headers
        const groupedEvents = groupEventsByDate(sortedEvents);
        const dateKeys = Array.from(groupedEvents.keys());

        return (
            <div className="relative">
                {/* Sort indicator */}
                <div className="flex items-center justify-end mb-2 text-xs text-gray-500">
                    {sortOrder === 'asc' ? (
                        <>
                            <ArrowUp className="w-3 h-3 mr-1" />
                            오래된 순
                        </>
                    ) : (
                        <>
                            <ArrowDown className="w-3 h-3 mr-1" />
                            최신 순
                        </>
                    )}
                </div>

                {/* Timeline */}
                <div className="relative border-l-2 border-gray-200 ml-3 space-y-6 py-4">
                    {dateKeys.map((dateKey) => {
                        const dateEvents = groupedEvents.get(dateKey)!;
                        const isUnknownDate = dateKey === '날짜 미상';

                        return (
                            <div key={dateKey}>
                                {/* Date header */}
                                <div className="relative -left-[10px] mb-4">
                                    <span
                                        className={`inline-block px-2 py-1 text-xs font-medium rounded ${
                                            isUnknownDate
                                                ? 'bg-gray-100 text-gray-500'
                                                : 'bg-blue-100 text-blue-800'
                                        }`}
                                    >
                                        {isUnknownDate ? '날짜 미상' : dateKey}
                                    </span>
                                </div>

                                {/* Events for this date */}
                                <div className="space-y-4">
                                    {dateEvents.map((event) => (
                                        <TimelineEventComponent
                                            key={event.eventId}
                                            event={event}
                                            onSelect={onSelect}
                                            showSignificance={showSignificance}
                                        />
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    }

    // Legacy format: Evidence[]
    const items = props.items!;

    if (items.length === 0) {
        return <EmptyState />;
    }

    // Sort by date
    const sortedItems = [...items].sort((a, b) => {
        const dateA = new Date(a.uploadDate).getTime();
        const dateB = new Date(b.uploadDate).getTime();
        return sortOrder === 'asc' ? dateA - dateB : dateB - dateA;
    });

    return (
        <div className="relative border-l-2 border-gray-200 ml-3 space-y-8 py-4">
            {sortedItems.map((item) => (
                <LegacyTimelineItem key={item.id} item={item} onSelect={onSelect} />
            ))}
        </div>
    );
}
