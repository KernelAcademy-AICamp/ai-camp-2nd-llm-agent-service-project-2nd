/**
 * Calendar Component
 * 003-role-based-ui Feature - US7 (T137)
 *
 * A calendar component built on react-big-calendar with:
 * - Month/Week/Day views
 * - Korean locale support
 * - Event type color coding
 * - Event click handling
 * - Date navigation
 */

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Calendar as BigCalendar, dateFnsLocalizer, View, Views } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay, setDefaultOptions } from 'date-fns';
import { ko } from 'date-fns/locale';
import 'react-big-calendar/lib/css/react-big-calendar.css';

import { CalendarEvent, EVENT_TYPE_COLORS, CalendarEventType } from '@/types/calendar';

// Set Korean as default locale
setDefaultOptions({ locale: ko });

// Configure date-fns localizer for react-big-calendar
const locales = {
  ko: ko,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date(), { weekStartsOn: 0 }),
  getDay,
  locales,
});

// Korean translations for toolbar
const messages = {
  today: '오늘',
  previous: '이전',
  next: '다음',
  month: '월',
  week: '주',
  day: '일',
  agenda: '목록',
  date: '날짜',
  time: '시간',
  event: '일정',
  noEventsInRange: '이 기간에 일정이 없습니다.',
  showMore: (total: number) => `+${total} 더보기`,
};

export type CalendarViewType = 'month' | 'week' | 'day' | 'agenda';

export interface CalendarProps {
  events: CalendarEvent[];
  view?: CalendarViewType;
  defaultDate?: Date;
  loading?: boolean;
  onEventClick?: (event: CalendarEvent) => void;
  onDateSelect?: (date: Date) => void;
  onViewChange?: (view: CalendarViewType) => void;
  onNavigate?: (date: Date) => void;
  className?: string;
}

interface BigCalendarEvent {
  id: string;
  title: string;
  start: Date;
  end: Date;
  allDay?: boolean;
  resource?: CalendarEvent;
}

// Convert CalendarEvent to BigCalendar event format
function convertToBigCalendarEvent(event: CalendarEvent): BigCalendarEvent {
  return {
    id: event.id,
    title: event.title,
    start: new Date(event.start_time),
    end: event.end_time ? new Date(event.end_time) : new Date(event.start_time),
    allDay: false,
    resource: event,
  };
}

// Event tooltip component
interface EventTooltipProps {
  event: CalendarEvent;
}

function EventTooltip({ event }: EventTooltipProps) {
  return (
    <div className="bg-white shadow-lg rounded-lg p-3 text-sm max-w-xs z-50">
      <div className="font-semibold">{event.title}</div>
      {event.case_title && (
        <div className="text-gray-600 mt-1">사건: {event.case_title}</div>
      )}
      {event.location && (
        <div className="text-gray-600 mt-1">장소: {event.location}</div>
      )}
      {event.description && (
        <div className="text-gray-500 mt-1 text-xs">{event.description}</div>
      )}
    </div>
  );
}

// Loading skeleton
function CalendarSkeleton() {
  return (
    <div className="animate-pulse" data-testid="calendar-skeleton">
      <div className="h-10 bg-gray-200 rounded mb-4" />
      <div className="grid grid-cols-7 gap-1">
        {Array.from({ length: 35 }).map((_, i) => (
          <div key={i} className="h-24 bg-gray-100 rounded" />
        ))}
      </div>
    </div>
  );
}

export default function Calendar({
  events,
  view = 'month',
  defaultDate,
  loading = false,
  onEventClick,
  onDateSelect,
  onViewChange,
  onNavigate,
  className = '',
}: CalendarProps) {
  const [currentView, setCurrentView] = useState<View>(view as View);
  const [currentDate, setCurrentDate] = useState<Date>(defaultDate || new Date());
  const [hoveredEvent, setHoveredEvent] = useState<CalendarEvent | null>(null);

  // Convert events to BigCalendar format
  const bigCalendarEvents = useMemo(
    () => events.map(convertToBigCalendarEvent),
    [events]
  );

  // Handle event click
  const handleSelectEvent = useCallback(
    (event: BigCalendarEvent) => {
      if (onEventClick && event.resource) {
        onEventClick(event.resource);
      }
    },
    [onEventClick]
  );

  // Handle date/slot select
  const handleSelectSlot = useCallback(
    ({ start }: { start: Date }) => {
      if (onDateSelect) {
        onDateSelect(start);
      }
    },
    [onDateSelect]
  );

  // Handle view change
  const handleViewChange = useCallback(
    (newView: View) => {
      setCurrentView(newView);
      if (onViewChange) {
        onViewChange(newView as CalendarViewType);
      }
    },
    [onViewChange]
  );

  // Handle date navigation
  const handleNavigate = useCallback(
    (date: Date) => {
      setCurrentDate(date);
      if (onNavigate) {
        onNavigate(date);
      }
    },
    [onNavigate]
  );

  // Custom event styling based on event type
  const eventStyleGetter = useCallback((event: BigCalendarEvent) => {
    const calendarEvent = event.resource;
    const color = calendarEvent?.color ||
      EVENT_TYPE_COLORS[calendarEvent?.event_type as CalendarEventType] ||
      EVENT_TYPE_COLORS.other;

    return {
      style: {
        backgroundColor: color,
        borderRadius: '4px',
        opacity: 0.9,
        color: 'white',
        border: 'none',
        display: 'block',
        fontSize: '12px',
        padding: '2px 4px',
      },
    };
  }, []);

  // Custom event component with hover tooltip
  const EventComponent = useCallback(
    ({ event }: { event: BigCalendarEvent }) => {
      const calendarEvent = event.resource;

      return (
        <div
          className="relative cursor-pointer"
          onMouseEnter={() => calendarEvent && setHoveredEvent(calendarEvent)}
          onMouseLeave={() => setHoveredEvent(null)}
        >
          <span className="truncate block">{event.title}</span>
        </div>
      );
    },
    []
  );

  // Custom toolbar component
  const ToolbarComponent = useCallback(
    ({ label, onNavigate: navFn, onView }: {
      label: string;
      onNavigate: (action: 'PREV' | 'NEXT' | 'TODAY') => void;
      onView: (view: View) => void;
    }) => (
      <div className="rbc-toolbar flex items-center justify-between mb-4 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navFn('TODAY')}
            className="px-3 py-1.5 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm font-medium"
            aria-label="오늘"
          >
            오늘
          </button>
          <button
            type="button"
            onClick={() => navFn('PREV')}
            className="p-1.5 bg-gray-100 rounded hover:bg-gray-200"
            aria-label="이전"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <button
            type="button"
            onClick={() => navFn('NEXT')}
            className="p-1.5 bg-gray-100 rounded hover:bg-gray-200"
            aria-label="다음"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <span className="text-lg font-semibold">{label}</span>

        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={() => onView(Views.MONTH)}
            className={`px-3 py-1.5 rounded text-sm font-medium ${
              currentView === Views.MONTH
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
            aria-label="월"
          >
            월
          </button>
          <button
            type="button"
            onClick={() => onView(Views.WEEK)}
            className={`px-3 py-1.5 rounded text-sm font-medium ${
              currentView === Views.WEEK
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
            aria-label="주"
          >
            주
          </button>
          <button
            type="button"
            onClick={() => onView(Views.DAY)}
            className={`px-3 py-1.5 rounded text-sm font-medium ${
              currentView === Views.DAY
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
            aria-label="일"
          >
            일
          </button>
        </div>
      </div>
    ),
    [currentView]
  );

  if (loading) {
    return <CalendarSkeleton />;
  }

  return (
    <div
      className={`relative ${className}`}
      data-testid="calendar"
      role="application"
      aria-label="calendar"
      tabIndex={0}
      onKeyDown={(e) => {
        // Basic keyboard navigation
        if (e.key === 'ArrowLeft') {
          handleNavigate(new Date(currentDate.setDate(currentDate.getDate() - 1)));
        } else if (e.key === 'ArrowRight') {
          handleNavigate(new Date(currentDate.setDate(currentDate.getDate() + 1)));
        } else if (e.key === 'ArrowUp') {
          handleNavigate(new Date(currentDate.setDate(currentDate.getDate() - 7)));
        } else if (e.key === 'ArrowDown') {
          handleNavigate(new Date(currentDate.setDate(currentDate.getDate() + 7)));
        }
      }}
    >
      <BigCalendar
        localizer={localizer}
        events={bigCalendarEvents}
        view={currentView}
        date={currentDate}
        onNavigate={handleNavigate}
        onView={handleViewChange}
        onSelectEvent={handleSelectEvent}
        onSelectSlot={handleSelectSlot}
        selectable
        popup
        messages={messages}
        eventPropGetter={eventStyleGetter}
        components={{
          event: EventComponent,
          toolbar: ToolbarComponent,
        }}
        style={{ height: 600 }}
        culture="ko"
        formats={{
          monthHeaderFormat: (date: Date) => format(date, 'yyyy년 M월', { locale: ko }),
          weekdayFormat: (date: Date) => format(date, 'EEE', { locale: ko }),
          dayHeaderFormat: (date: Date) => format(date, 'M월 d일 EEEE', { locale: ko }),
          dayRangeHeaderFormat: ({ start, end }: { start: Date; end: Date }) =>
            `${format(start, 'M월 d일', { locale: ko })} - ${format(end, 'M월 d일', { locale: ko })}`,
        }}
      />

      {/* Event hover tooltip */}
      {hoveredEvent && (
        <div className="absolute z-50 pointer-events-none" style={{ top: '50%', left: '50%' }}>
          <EventTooltip event={hoveredEvent} />
        </div>
      )}
    </div>
  );
}
