'use client';

import React, { useState, useMemo } from 'react';
import {
  TimelineResult,
  TimelineEvent,
  groupEventsByMonth,
  TimelineMonthGroup,
} from '@/types/timeline';
import TimelineEventCard from './TimelineEventCard';
import { ChevronDown, ChevronRight, Calendar, Filter, RefreshCw } from 'lucide-react';

interface TimelineViewProps {
  timeline: TimelineResult;
  isLoading?: boolean;
  onEventClick?: (event: TimelineEvent) => void;
  onEventPin?: (event: TimelineEvent) => void;
  onRefresh?: () => void;
}

export default function TimelineView({
  timeline,
  isLoading = false,
  onEventClick,
  onEventPin,
  onRefresh,
}: TimelineViewProps) {
  const [expandedMonths, setExpandedMonths] = useState<Set<string>>(new Set());
  const [filter, setFilter] = useState<'all' | 'key' | 'pinned'>('all');
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  // 월별 그룹화
  const monthGroups = useMemo(() => {
    let events = timeline.events;

    // 필터 적용
    if (filter === 'key') {
      events = events.filter((e) => e.is_key_evidence);
    } else if (filter === 'pinned') {
      events = events.filter((e) => e.is_pinned);
    }

    return groupEventsByMonth(events);
  }, [timeline.events, filter]);

  // 초기에 모든 월 펼치기
  React.useEffect(() => {
    const allMonths = new Set<string>(monthGroups.map((g) => g.month));
    setExpandedMonths(allMonths);
  }, [monthGroups]);

  const toggleMonth = (month: string) => {
    setExpandedMonths((prev) => {
      const next = new Set(prev);
      if (next.has(month)) {
        next.delete(month);
      } else {
        next.add(month);
      }
      return next;
    });
  };

  const handleEventClick = (event: TimelineEvent) => {
    setSelectedEventId(event.event_id);
    onEventClick?.(event);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (timeline.events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500">
        <Calendar className="w-12 h-12 mb-4 opacity-50" />
        <p>타임라인 이벤트가 없습니다.</p>
        <p className="text-sm">증거를 업로드하면 타임라인이 생성됩니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            타임라인
          </h3>
          <span className="text-sm text-gray-500">
            {timeline.total_events}개 이벤트
            {timeline.key_events_count > 0 && (
              <span className="ml-2 text-red-500">
                ({timeline.key_events_count}개 핵심)
              </span>
            )}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* 필터 */}
          <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 text-sm rounded ${
                filter === 'all'
                  ? 'bg-white dark:bg-gray-700 shadow'
                  : 'hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              전체
            </button>
            <button
              onClick={() => setFilter('key')}
              className={`px-3 py-1 text-sm rounded ${
                filter === 'key'
                  ? 'bg-white dark:bg-gray-700 shadow'
                  : 'hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              핵심
            </button>
            <button
              onClick={() => setFilter('pinned')}
              className={`px-3 py-1 text-sm rounded ${
                filter === 'pinned'
                  ? 'bg-white dark:bg-gray-700 shadow'
                  : 'hover:bg-gray-200 dark:hover:bg-gray-700'
              }`}
            >
              핀 고정
            </button>
          </div>

          {/* 새로고침 */}
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded"
              title="새로고침"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* 날짜 범위 */}
      {timeline.date_range.start && timeline.date_range.end && (
        <div className="text-sm text-gray-500 flex items-center gap-2">
          <span>{timeline.date_range.start}</span>
          <span>~</span>
          <span>{timeline.date_range.end}</span>
        </div>
      )}

      {/* 월별 그룹 */}
      <div className="space-y-4">
        {monthGroups.map((group) => (
          <div key={group.month} className="border rounded-lg dark:border-gray-700">
            {/* 월 헤더 */}
            <button
              onClick={() => toggleMonth(group.month)}
              className="w-full flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-t-lg"
            >
              <div className="flex items-center gap-2">
                {expandedMonths.has(group.month) ? (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronRight className="w-5 h-5 text-gray-500" />
                )}
                <span className="font-medium">{group.label}</span>
                <span className="text-sm text-gray-500">
                  ({group.eventCount}개)
                </span>
              </div>
            </button>

            {/* 이벤트 목록 */}
            {expandedMonths.has(group.month) && (
              <div className="p-3 pt-0 space-y-3">
                {group.events.map((event) => (
                  <div key={event.event_id} className="flex gap-3">
                    {/* 날짜 마커 */}
                    <div className="flex flex-col items-center">
                      <div className="text-xs text-gray-500 whitespace-nowrap">
                        {event.date.split('-')[2]}일
                      </div>
                      <div className="w-px h-full bg-gray-200 dark:bg-gray-700 mt-1" />
                    </div>

                    {/* 이벤트 카드 */}
                    <div className="flex-1">
                      <TimelineEventCard
                        event={event}
                        isSelected={selectedEventId === event.event_id}
                        onClick={handleEventClick}
                        onPin={onEventPin}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 라벨 통계 */}
      {Object.keys(timeline.events_by_label).length > 0 && (
        <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
            <Filter className="w-4 h-4" />
            라벨별 분포
          </h4>
          <div className="flex flex-wrap gap-2">
            {Object.entries(timeline.events_by_label).map(([label, count]) => (
              <span
                key={label}
                className="text-xs px-2 py-1 bg-white dark:bg-gray-700 rounded border dark:border-gray-600"
              >
                {label}: {count}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
