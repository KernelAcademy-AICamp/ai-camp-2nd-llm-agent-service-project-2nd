/**
 * TimelineEvent Component
 * Displays a single event on the timeline with type icons, date/time, speaker badge, and summary
 *
 * Feature: 002-evidence-timeline
 */

import { Clock, FileText, Image, Mic, Video, File, MessageSquare, AlertTriangle, Star } from 'lucide-react';
import { TimelineEvent as TimelineEventType, TimelineEventType as EventType } from '@/types/timeline';
import { cn } from '@/lib/utils';

interface TimelineEventProps {
    event: TimelineEventType;
    onSelect: (evidenceId: string) => void;
    showSignificance?: boolean;
}

/**
 * Get icon for event type
 */
function getTypeIcon(type: EventType) {
    const iconClass = 'w-4 h-4';
    switch (type) {
        case 'message':
            return <MessageSquare className={iconClass} />;
        case 'document':
            return <FileText className={iconClass} />;
        case 'image':
            return <Image className={iconClass} />;
        case 'audio':
            return <Mic className={iconClass} />;
        case 'video':
            return <Video className={iconClass} />;
        case 'incident':
            return <AlertTriangle className={iconClass} />;
        default:
            return <File className={iconClass} />;
    }
}

/**
 * Get display name for event type (Korean)
 */
function getTypeLabel(type: EventType): string {
    switch (type) {
        case 'message':
            return '메시지';
        case 'document':
            return '문서';
        case 'image':
            return '이미지';
        case 'audio':
            return '음성';
        case 'video':
            return '영상';
        case 'incident':
            return '사건';
        default:
            return '기타';
    }
}

/**
 * Get speaker badge color
 */
function getSpeakerColor(speaker?: string): string {
    switch (speaker) {
        case '원고':
            return 'bg-blue-100 text-blue-800';
        case '피고':
            return 'bg-red-100 text-red-800';
        case '제3자':
            return 'bg-gray-100 text-gray-800';
        default:
            return 'bg-gray-50 text-gray-500';
    }
}

/**
 * Get significance color for marker
 */
function getSignificanceColor(significance: number, isKeyEvidence: boolean): string {
    if (isKeyEvidence) {
        return 'border-amber-500 bg-amber-50';
    }
    if (significance >= 4) {
        return 'border-red-500 bg-red-50';
    }
    if (significance >= 3) {
        return 'border-orange-400 bg-orange-50';
    }
    return 'border-gray-300 bg-white';
}

export default function TimelineEvent({
    event,
    onSelect,
    showSignificance = true,
}: TimelineEventProps) {
    const markerColor = getSignificanceColor(event.significance, event.isKeyEvidence);

    return (
        <div className="relative pl-8 group">
            {/* Timeline marker */}
            <div
                className={cn(
                    'absolute -left-[9px] top-1 w-4 h-4 rounded-full border-2 transition-all',
                    markerColor,
                    'group-hover:scale-110 group-hover:shadow-md'
                )}
            >
                {event.isKeyEvidence && (
                    <Star className="w-2 h-2 absolute top-0.5 left-0.5 text-amber-600 fill-amber-500" />
                )}
            </div>

            {/* Event content */}
            <div
                onClick={() => onSelect(event.evidenceId)}
                className={cn(
                    'cursor-pointer p-3 rounded-lg transition-colors -mt-2',
                    'hover:bg-gray-50',
                    event.isKeyEvidence && 'bg-amber-50/50 hover:bg-amber-50'
                )}
            >
                {/* Date and time */}
                <div className="flex items-center text-sm text-gray-500 mb-1">
                    <Clock className="w-3 h-3 mr-1" />
                    <time>
                        {event.date}
                        {event.time && ` ${event.time}`}
                    </time>

                    {/* Key evidence badge */}
                    {event.isKeyEvidence && (
                        <span className="ml-2 px-1.5 py-0.5 text-xs font-medium bg-amber-100 text-amber-800 rounded">
                            핵심
                        </span>
                    )}
                </div>

                {/* Description/Summary */}
                <h4 className="text-base font-medium text-gray-900 mb-1 line-clamp-2">
                    {event.description}
                </h4>

                {/* Meta info row */}
                <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400">
                    {/* Type icon and label */}
                    <span className="flex items-center">
                        {getTypeIcon(event.eventType)}
                        <span className="ml-1">{getTypeLabel(event.eventType)}</span>
                    </span>

                    {/* Speaker badge */}
                    {event.speaker && (
                        <span
                            className={cn(
                                'px-1.5 py-0.5 rounded text-xs font-medium',
                                getSpeakerColor(event.speaker)
                            )}
                        >
                            {event.speaker}
                        </span>
                    )}

                    {/* Significance indicator */}
                    {showSignificance && event.significance > 1 && (
                        <span className="flex items-center text-gray-500">
                            <span className="mr-0.5">중요도:</span>
                            {[...Array(event.significance)].map((_, i) => (
                                <span
                                    key={i}
                                    className={cn(
                                        'w-1.5 h-1.5 rounded-full ml-0.5',
                                        i < event.significance
                                            ? 'bg-amber-400'
                                            : 'bg-gray-200'
                                    )}
                                />
                            ))}
                        </span>
                    )}

                    {/* Source file */}
                    <span className="text-gray-400 truncate max-w-[150px]" title={event.sourceFile}>
                        {event.sourceFile}
                    </span>
                </div>

                {/* Labels */}
                {event.labels.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                        {event.labels.slice(0, 3).map((label) => (
                            <span
                                key={label}
                                className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                            >
                                {label}
                            </span>
                        ))}
                        {event.labels.length > 3 && (
                            <span className="px-1.5 py-0.5 text-xs text-gray-400">
                                +{event.labels.length - 3}
                            </span>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
