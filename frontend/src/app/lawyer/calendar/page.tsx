/**
 * Lawyer Calendar Page
 * 003-role-based-ui Feature - US7 (T139)
 *
 * Full calendar view with:
 * - Month/Week/Day views
 * - Event management (create, edit, delete)
 * - Event type filtering
 * - Case-linked events
 */

'use client';

import React, { useState, useCallback } from 'react';
import { useCalendar } from '@/hooks/useCalendar';
import Calendar, { CalendarViewType } from '@/components/shared/Calendar';
import EventForm from '@/components/shared/EventForm';
import {
  CalendarEvent,
  CalendarEventCreate,
  CalendarEventUpdate,
  CalendarEventType,
  EVENT_TYPE_COLORS,
  EVENT_TYPE_LABELS,
} from '@/types/calendar';

// Modal component
function Modal({
  isOpen,
  onClose,
  title,
  children,
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-black bg-opacity-25"
          onClick={onClose}
          aria-hidden="true"
        />

        {/* Modal panel */}
        <div className="relative bg-white rounded-xl shadow-xl max-w-lg w-full p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-500"
              aria-label="닫기"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
}

// Event type filter button
function EventTypeFilter({
  type,
  isActive,
  onClick,
}: {
  type: CalendarEventType | 'all';
  isActive: boolean;
  onClick: () => void;
}) {
  const color = type === 'all' ? '#374151' : EVENT_TYPE_COLORS[type];
  const label = type === 'all' ? '전체' : EVENT_TYPE_LABELS[type];

  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
        isActive
          ? 'bg-gray-900 text-white'
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
    >
      {type !== 'all' && (
        <span
          className="w-2.5 h-2.5 rounded-full"
          style={{ backgroundColor: color }}
        />
      )}
      {label}
    </button>
  );
}

// Event detail panel
function EventDetailPanel({
  event,
  onEdit,
  onClose,
}: {
  event: CalendarEvent;
  onEdit: () => void;
  onClose: () => void;
}) {
  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3">
        <span
          className="w-4 h-4 rounded-full mt-1 flex-shrink-0"
          style={{ backgroundColor: event.color || EVENT_TYPE_COLORS[event.event_type] }}
        />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{event.title}</h3>
          <p className="text-sm text-gray-500">{EVENT_TYPE_LABELS[event.event_type]}</p>
        </div>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex items-start gap-3">
          <svg className="w-5 h-5 text-gray-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-gray-900">{formatDateTime(event.start_time)}</p>
            {event.end_time && (
              <p className="text-gray-500">~ {formatDateTime(event.end_time)}</p>
            )}
          </div>
        </div>

        {event.location && (
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-gray-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <p className="text-gray-900">{event.location}</p>
          </div>
        )}

        {event.case_title && (
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-gray-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
            <p className="text-gray-900">{event.case_title}</p>
          </div>
        )}

        {event.description && (
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-gray-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
            </svg>
            <p className="text-gray-700">{event.description}</p>
          </div>
        )}
      </div>

      <div className="flex justify-end gap-2 pt-4 border-t">
        <button
          onClick={onClose}
          className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          닫기
        </button>
        <button
          onClick={onEdit}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          편집
        </button>
      </div>
    </div>
  );
}

export default function LawyerCalendarPage() {
  const {
    events,
    isLoading,
    error,
    createEvent,
    updateEvent,
    deleteEvent,
    goToMonth,
  } = useCalendar();

  // Modal states
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);

  // Filter state
  const [activeFilter, setActiveFilter] = useState<CalendarEventType | 'all'>('all');
  const [currentView, setCurrentView] = useState<CalendarViewType>('month');

  // Form loading state
  const [isFormLoading, setIsFormLoading] = useState(false);

  // Filter events by type
  const filteredEvents = activeFilter === 'all'
    ? events
    : events.filter((e) => e.event_type === activeFilter);

  // Handle event click
  const handleEventClick = useCallback((event: CalendarEvent) => {
    setSelectedEvent(event);
  }, []);

  // Handle date select (for creating new event)
  const handleDateSelect = useCallback((date: Date) => {
    setSelectedDate(date);
    setIsCreateModalOpen(true);
  }, []);

  // Handle create event
  const handleCreateEvent = useCallback(async (data: CalendarEventCreate | CalendarEventUpdate) => {
    setIsFormLoading(true);
    try {
      await createEvent(data as CalendarEventCreate);
      setIsCreateModalOpen(false);
      setSelectedDate(null);
    } finally {
      setIsFormLoading(false);
    }
  }, [createEvent]);

  // Handle update event
  const handleUpdateEvent = useCallback(async (data: CalendarEventCreate | CalendarEventUpdate) => {
    if (!selectedEvent) return;
    setIsFormLoading(true);
    try {
      await updateEvent(selectedEvent.id, data as CalendarEventUpdate);
      setIsEditModalOpen(false);
      setSelectedEvent(null);
    } finally {
      setIsFormLoading(false);
    }
  }, [selectedEvent, updateEvent]);

  // Handle delete event
  const handleDeleteEvent = useCallback(async () => {
    if (!selectedEvent) return;
    setIsFormLoading(true);
    try {
      await deleteEvent(selectedEvent.id);
      setIsEditModalOpen(false);
      setSelectedEvent(null);
    } finally {
      setIsFormLoading(false);
    }
  }, [selectedEvent, deleteEvent]);

  // Handle view change
  const handleViewChange = useCallback((view: CalendarViewType) => {
    setCurrentView(view);
  }, []);

  // Handle navigation
  const handleNavigate = useCallback((date: Date) => {
    goToMonth(date);
  }, [goToMonth]);

  // Open edit modal
  const openEditModal = useCallback(() => {
    setIsEditModalOpen(true);
  }, []);

  // Close event detail
  const closeEventDetail = useCallback(() => {
    setSelectedEvent(null);
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">일정 관리</h1>
          <p className="text-gray-500 mt-1">케이스 관련 일정을 관리하세요.</p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          새 일정
        </button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2">
        <EventTypeFilter
          type="all"
          isActive={activeFilter === 'all'}
          onClick={() => setActiveFilter('all')}
        />
        {(['court', 'meeting', 'deadline', 'internal', 'other'] as CalendarEventType[]).map((type) => (
          <EventTypeFilter
            key={type}
            type={type}
            isActive={activeFilter === type}
            onClick={() => setActiveFilter(type)}
          />
        ))}
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          일정을 불러오는 중 오류가 발생했습니다: {error.message}
        </div>
      )}

      {/* Calendar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <Calendar
          events={filteredEvents}
          view={currentView}
          loading={isLoading}
          onEventClick={handleEventClick}
          onDateSelect={handleDateSelect}
          onViewChange={handleViewChange}
          onNavigate={handleNavigate}
        />
      </div>

      {/* Event Legend */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">범례</h3>
        <div className="flex flex-wrap gap-4">
          {(['court', 'meeting', 'deadline', 'internal', 'other'] as CalendarEventType[]).map((type) => (
            <div key={type} className="flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: EVENT_TYPE_COLORS[type] }}
              />
              <span className="text-sm text-gray-600">{EVENT_TYPE_LABELS[type]}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Create Event Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          setSelectedDate(null);
        }}
        title="새 일정 추가"
      >
        <EventForm
          defaultDate={selectedDate || undefined}
          onSubmit={handleCreateEvent}
          onCancel={() => {
            setIsCreateModalOpen(false);
            setSelectedDate(null);
          }}
          isLoading={isFormLoading}
        />
      </Modal>

      {/* Event Detail Modal */}
      <Modal
        isOpen={!!selectedEvent && !isEditModalOpen}
        onClose={closeEventDetail}
        title="일정 상세"
      >
        {selectedEvent && (
          <EventDetailPanel
            event={selectedEvent}
            onEdit={openEditModal}
            onClose={closeEventDetail}
          />
        )}
      </Modal>

      {/* Edit Event Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
        }}
        title="일정 편집"
      >
        {selectedEvent && (
          <EventForm
            event={selectedEvent}
            onSubmit={handleUpdateEvent}
            onCancel={() => setIsEditModalOpen(false)}
            onDelete={handleDeleteEvent}
            isLoading={isFormLoading}
          />
        )}
      </Modal>
    </div>
  );
}
