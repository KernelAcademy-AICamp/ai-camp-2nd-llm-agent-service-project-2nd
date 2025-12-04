/**
 * Timeline Component
 * Main container for evidence timeline display
 *
 * Feature: 002-evidence-timeline
 */

'use client';

import { useRouter } from 'next/navigation';
import { TimelineEvent as TimelineEventType, TimelineResult } from '@/types/timeline';
import { TimelineEvent } from './TimelineEvent';
import { cn } from '@/lib/utils';

interface TimelineProps {
    data: TimelineResult | null;
    events: TimelineEventType[];
    isLoading: boolean;
    error: string | null;
    sortOrder?: 'asc' | 'desc';
    onSortChange?: (order: 'asc' | 'desc') => void;
    onLoadMore?: () => void;
    hasMore?: boolean;
    caseId: string;
}

export function Timeline({
    data,
    events,
    isLoading,
    error,
    sortOrder = 'asc',
    onSortChange,
    onLoadMore,
    hasMore,
    caseId,
}: TimelineProps) {
    const router = useRouter();

    const handleEventClick = (event: TimelineEventType) => {
        // Navigate to evidence detail page
        router.push(`/cases/${caseId}/evidence/${event.evidenceId}`);
    };

    // Loading state
    if (isLoading && events.length === 0) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
                <span className="ml-3 text-gray-600">타임라인 로딩 중...</span>
            </div>
        );
    }

    // Error state
    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                <p className="font-medium">오류가 발생했습니다</p>
                <p className="text-sm mt-1">{error}</p>
            </div>
        );
    }

    // Empty state
    if (events.length === 0) {
        return (
            <div className="text-center py-12 bg-gray-50 rounded-lg">
                <div className="text-4xl mb-4">📭</div>
                <h3 className="text-lg font-medium text-gray-700 mb-2">
                    표시할 증거가 없습니다
                </h3>
                <p className="text-gray-500">
                    이 케이스에 증거를 업로드하면 타임라인에 표시됩니다.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Header with stats and sort */}
            <div className="flex items-center justify-between bg-white rounded-lg border p-4">
                <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span>
                        전체 <strong className="text-gray-900">{data?.totalCount || 0}</strong>건
                    </span>
                    {data && data.filteredCount < data.totalCount && (
                        <span>
                            필터 적용: <strong className="text-blue-600">{data.filteredCount}</strong>건
                        </span>
                    )}
                    {data && data.keyEventsCount > 0 && (
                        <span>
                            핵심 증거: <strong className="text-amber-600">{data.keyEventsCount}</strong>건
                        </span>
                    )}
                </div>

                {/* Sort toggle */}
                {onSortChange && (
                    <button
                        onClick={() => onSortChange(sortOrder === 'asc' ? 'desc' : 'asc')}
                        className="flex items-center gap-1 px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                    >
                        {sortOrder === 'asc' ? '⬆️ 오래된 순' : '⬇️ 최신 순'}
                    </button>
                )}
            </div>

            {/* Date range info */}
            {data?.dateRange?.start && data?.dateRange?.end && (
                <div className="text-sm text-gray-500 px-1">
                    기간: {data.dateRange.start} ~ {data.dateRange.end}
                </div>
            )}

            {/* Timeline events */}
            <div className="pl-2">
                {events.map((event) => (
                    <TimelineEvent
                        key={event.eventId}
                        event={event}
                        onClick={handleEventClick}
                    />
                ))}
            </div>

            {/* Load more button */}
            {hasMore && (
                <div className="text-center pt-4">
                    <button
                        onClick={onLoadMore}
                        disabled={isLoading}
                        className={cn(
                            'px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors',
                            isLoading && 'opacity-50 cursor-not-allowed'
                        )}
                    >
                        {isLoading ? '로딩 중...' : '더 보기'}
                    </button>
                </div>
            )}

            {/* Loading indicator for load more */}
            {isLoading && events.length > 0 && (
                <div className="flex items-center justify-center py-4">
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
                    <span className="ml-2 text-sm text-gray-500">추가 로딩 중...</span>
                </div>
            )}
        </div>
    );
}
