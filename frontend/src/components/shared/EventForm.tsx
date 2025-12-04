/**
 * EventForm Component
 * 003-role-based-ui Feature - US7 (T138)
 *
 * A form component for creating/editing calendar events with:
 * - Event type selection with color preview
 * - Date/time pickers
 * - Case linking (optional)
 * - Reminder configuration
 */

'use client';

import React, { useState, useEffect, FormEvent } from 'react';
import {
  CalendarEvent,
  CalendarEventCreate,
  CalendarEventUpdate,
  CalendarEventType,
  EVENT_TYPE_COLORS,
  EVENT_TYPE_LABELS,
} from '@/types/calendar';

export interface EventFormProps {
  event?: CalendarEvent;
  defaultDate?: Date;
  cases?: Array<{ id: string; title: string }>;
  onSubmit: (data: CalendarEventCreate | CalendarEventUpdate) => Promise<void>;
  onCancel: () => void;
  onDelete?: () => Promise<void>;
  isLoading?: boolean;
}

const EVENT_TYPES: CalendarEventType[] = ['court', 'meeting', 'deadline', 'internal', 'other'];

const REMINDER_OPTIONS = [
  { value: 0, label: '없음' },
  { value: 15, label: '15분 전' },
  { value: 30, label: '30분 전' },
  { value: 60, label: '1시간 전' },
  { value: 120, label: '2시간 전' },
  { value: 1440, label: '1일 전' },
];

// Format date for datetime-local input
function formatDateTimeLocal(date: Date | string): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  const offset = d.getTimezoneOffset();
  const localDate = new Date(d.getTime() - offset * 60 * 1000);
  return localDate.toISOString().slice(0, 16);
}

export default function EventForm({
  event,
  defaultDate,
  cases = [],
  onSubmit,
  onCancel,
  onDelete,
  isLoading = false,
}: EventFormProps) {
  const isEditing = !!event;

  // Form state
  const [title, setTitle] = useState(event?.title || '');
  const [eventType, setEventType] = useState<CalendarEventType>(event?.event_type || 'meeting');
  const [startTime, setStartTime] = useState(
    event?.start_time
      ? formatDateTimeLocal(event.start_time)
      : defaultDate
      ? formatDateTimeLocal(defaultDate)
      : formatDateTimeLocal(new Date())
  );
  const [endTime, setEndTime] = useState(
    event?.end_time ? formatDateTimeLocal(event.end_time) : ''
  );
  const [description, setDescription] = useState(event?.description || '');
  const [location, setLocation] = useState(event?.location || '');
  const [caseId, setCaseId] = useState(event?.case_id || '');
  const [reminderMinutes, setReminderMinutes] = useState(event?.reminder_minutes || 30);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Reset form when event changes
  useEffect(() => {
    if (event) {
      setTitle(event.title);
      setEventType(event.event_type);
      setStartTime(formatDateTimeLocal(event.start_time));
      setEndTime(event.end_time ? formatDateTimeLocal(event.end_time) : '');
      setDescription(event.description || '');
      setLocation(event.location || '');
      setCaseId(event.case_id || '');
      setReminderMinutes(event.reminder_minutes || 30);
    }
  }, [event]);

  // Validate form
  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!title.trim()) {
      newErrors.title = '제목을 입력해주세요';
    }

    if (!startTime) {
      newErrors.startTime = '시작 시간을 입력해주세요';
    }

    if (endTime && new Date(endTime) <= new Date(startTime)) {
      newErrors.endTime = '종료 시간은 시작 시간 이후여야 합니다';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle form submit
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitError(null);

    if (!validate()) {
      return;
    }

    const data: CalendarEventCreate | CalendarEventUpdate = {
      title: title.trim(),
      event_type: eventType,
      start_time: new Date(startTime).toISOString(),
      ...(endTime && { end_time: new Date(endTime).toISOString() }),
      ...(description && { description: description.trim() }),
      ...(location && { location: location.trim() }),
      ...(caseId && { case_id: caseId }),
      reminder_minutes: reminderMinutes,
    };

    try {
      await onSubmit(data);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : '저장에 실패했습니다');
    }
  };

  // Handle delete
  const handleDelete = async () => {
    if (!onDelete) return;

    if (!window.confirm('정말 이 일정을 삭제하시겠습니까?')) {
      return;
    }

    try {
      await onDelete();
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : '삭제에 실패했습니다');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4" data-testid="event-form">
      {/* Submit error */}
      {submitError && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {submitError}
        </div>
      )}

      {/* Title */}
      <div>
        <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
          제목 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          id="title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.title ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="일정 제목을 입력하세요"
          disabled={isLoading}
        />
        {errors.title && (
          <p className="mt-1 text-sm text-red-500">{errors.title}</p>
        )}
      </div>

      {/* Event Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          일정 유형
        </label>
        <div className="flex flex-wrap gap-2">
          {EVENT_TYPES.map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => setEventType(type)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium flex items-center gap-2 transition-colors ${
                eventType === type
                  ? 'ring-2 ring-offset-2 ring-blue-500'
                  : 'opacity-70 hover:opacity-100'
              }`}
              style={{
                backgroundColor: EVENT_TYPE_COLORS[type],
                color: 'white',
              }}
              disabled={isLoading}
            >
              <span
                className="w-2 h-2 rounded-full bg-white"
                style={{ opacity: eventType === type ? 1 : 0 }}
              />
              {EVENT_TYPE_LABELS[type]}
            </button>
          ))}
        </div>
      </div>

      {/* Start Time */}
      <div>
        <label htmlFor="startTime" className="block text-sm font-medium text-gray-700 mb-1">
          시작 시간 <span className="text-red-500">*</span>
        </label>
        <input
          type="datetime-local"
          id="startTime"
          value={startTime}
          onChange={(e) => setStartTime(e.target.value)}
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.startTime ? 'border-red-500' : 'border-gray-300'
          }`}
          disabled={isLoading}
        />
        {errors.startTime && (
          <p className="mt-1 text-sm text-red-500">{errors.startTime}</p>
        )}
      </div>

      {/* End Time */}
      <div>
        <label htmlFor="endTime" className="block text-sm font-medium text-gray-700 mb-1">
          종료 시간
        </label>
        <input
          type="datetime-local"
          id="endTime"
          value={endTime}
          onChange={(e) => setEndTime(e.target.value)}
          className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
            errors.endTime ? 'border-red-500' : 'border-gray-300'
          }`}
          disabled={isLoading}
        />
        {errors.endTime && (
          <p className="mt-1 text-sm text-red-500">{errors.endTime}</p>
        )}
      </div>

      {/* Location */}
      <div>
        <label htmlFor="location" className="block text-sm font-medium text-gray-700 mb-1">
          장소
        </label>
        <input
          type="text"
          id="location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="예: 서울가정법원 301호"
          disabled={isLoading}
        />
      </div>

      {/* Case Link */}
      {cases.length > 0 && (
        <div>
          <label htmlFor="caseId" className="block text-sm font-medium text-gray-700 mb-1">
            연결 사건
          </label>
          <select
            id="caseId"
            value={caseId}
            onChange={(e) => setCaseId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading}
          >
            <option value="">사건 선택 안함</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.title}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Reminder */}
      <div>
        <label htmlFor="reminder" className="block text-sm font-medium text-gray-700 mb-1">
          알림
        </label>
        <select
          id="reminder"
          value={reminderMinutes}
          onChange={(e) => setReminderMinutes(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          disabled={isLoading}
        >
          {REMINDER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          메모
        </label>
        <textarea
          id="description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          placeholder="추가 메모를 입력하세요"
          disabled={isLoading}
        />
      </div>

      {/* Form Actions */}
      <div className="flex items-center justify-between pt-4 border-t">
        {isEditing && onDelete ? (
          <button
            type="button"
            onClick={handleDelete}
            className="px-4 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
            disabled={isLoading}
          >
            삭제
          </button>
        ) : (
          <div />
        )}

        <div className="flex gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            disabled={isLoading}
          >
            취소
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? '저장 중...' : isEditing ? '수정' : '저장'}
          </button>
        </div>
      </div>
    </form>
  );
}
