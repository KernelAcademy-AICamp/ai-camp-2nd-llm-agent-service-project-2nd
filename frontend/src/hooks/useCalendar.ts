/**
 * Calendar Hooks
 * 003-role-based-ui Feature - US7 (T140)
 *
 * Custom hooks for calendar data fetching and management using SWR.
 * Provides CRUD operations and event type color management.
 */

'use client';

import { useState, useCallback, useMemo } from 'react';
import useSWR, { useSWRConfig } from 'swr';
import {
  CalendarEvent,
  CalendarEventCreate,
  CalendarEventUpdate,
  CalendarEventsResponse,
  UpcomingEventsResponse,
  RemindersResponse,
  CalendarEventType,
  EVENT_TYPE_COLORS,
} from '@/types/calendar';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// SWR fetcher function
const fetcher = async (url: string) => {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || 'Failed to fetch');
  }

  return response.json();
};

// Add color property to events based on event_type
function addColorToEvents(events: CalendarEvent[]): CalendarEvent[] {
  return events.map((event) => ({
    ...event,
    color: EVENT_TYPE_COLORS[event.event_type as CalendarEventType] || EVENT_TYPE_COLORS.other,
  }));
}

export interface UseCalendarOptions {
  startDate?: Date;
  endDate?: Date;
}

export interface UseCalendarReturn {
  events: CalendarEvent[];
  total: number;
  isLoading: boolean;
  error: Error | undefined;
  startDate: Date | undefined;
  endDate: Date | undefined;
  setDateRange: (start: Date, end: Date) => void;
  goToMonth: (date: Date) => void;
  createEvent: (data: CalendarEventCreate) => Promise<CalendarEvent>;
  updateEvent: (id: string, data: CalendarEventUpdate) => Promise<CalendarEvent>;
  deleteEvent: (id: string) => Promise<void>;
  getEventColor: (eventType: string) => string;
  mutate: () => void;
}

/**
 * Main calendar hook for fetching and managing events
 */
export function useCalendar(options: UseCalendarOptions = {}): UseCalendarReturn {
  const { mutate: globalMutate } = useSWRConfig();
  const [startDate, setStartDate] = useState<Date | undefined>(options.startDate);
  const [endDate, setEndDate] = useState<Date | undefined>(options.endDate);

  // Build URL with date range parameters
  const url = useMemo(() => {
    const params = new URLSearchParams();
    if (startDate) {
      params.append('start_date', startDate.toISOString().split('.')[0]);
    }
    if (endDate) {
      params.append('end_date', endDate.toISOString().split('.')[0]);
    }
    const queryString = params.toString();
    return queryString ? `/calendar/events?${queryString}` : '/calendar/events';
  }, [startDate, endDate]);

  const { data, error, isLoading, mutate } = useSWR<CalendarEventsResponse>(
    url,
    fetcher,
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  );

  // Add colors to events
  const eventsWithColors = useMemo(() => {
    if (!data?.events) return [];
    return addColorToEvents(data.events);
  }, [data?.events]);

  // Set date range
  const setDateRange = useCallback((start: Date, end: Date) => {
    setStartDate(start);
    setEndDate(end);
  }, []);

  // Navigate to month (set date range to full month)
  const goToMonth = useCallback((date: Date) => {
    const start = new Date(date.getFullYear(), date.getMonth(), 1);
    const end = new Date(date.getFullYear(), date.getMonth() + 1, 0);
    setDateRange(start, end);
  }, [setDateRange]);

  // Get color for event type
  const getEventColor = useCallback((eventType: string): string => {
    return EVENT_TYPE_COLORS[eventType as CalendarEventType] || EVENT_TYPE_COLORS.other;
  }, []);

  // Create event
  const createEvent = useCallback(async (eventData: CalendarEventCreate): Promise<CalendarEvent> => {
    const response = await fetch(`${API_BASE_URL}/calendar/events`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(eventData),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to create event' }));
      throw new Error(error.detail || 'Failed to create event');
    }

    const newEvent = await response.json();
    mutate(); // Revalidate the events list
    return newEvent;
  }, [mutate]);

  // Update event
  const updateEvent = useCallback(async (id: string, eventData: CalendarEventUpdate): Promise<CalendarEvent> => {
    const response = await fetch(`${API_BASE_URL}/calendar/events/${id}`, {
      method: 'PUT',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(eventData),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to update event' }));
      throw new Error(error.detail || 'Failed to update event');
    }

    const updatedEvent = await response.json();
    mutate(); // Revalidate the events list
    return updatedEvent;
  }, [mutate]);

  // Delete event
  const deleteEvent = useCallback(async (id: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/calendar/events/${id}`, {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Failed to delete event' }));
      throw new Error(error.detail || 'Failed to delete event');
    }

    mutate(); // Revalidate the events list
  }, [mutate]);

  return {
    events: eventsWithColors,
    total: data?.total ?? 0,
    isLoading,
    error,
    startDate,
    endDate,
    setDateRange,
    goToMonth,
    createEvent,
    updateEvent,
    deleteEvent,
    getEventColor,
    mutate,
  };
}

export interface UseUpcomingEventsReturn {
  events: CalendarEvent[];
  isLoading: boolean;
  error: Error | undefined;
}

/**
 * Hook for fetching upcoming events (next N days)
 */
export function useUpcomingEvents(days: number = 7): UseUpcomingEventsReturn {
  const url = `/calendar/upcoming?days=${days}`;

  const { data, error, isLoading } = useSWR<UpcomingEventsResponse>(
    url,
    fetcher,
    {
      revalidateOnFocus: false,
      dedupingInterval: 30000,
    }
  );

  const eventsWithColors = useMemo(() => {
    if (!data?.events) return [];
    return addColorToEvents(data.events);
  }, [data?.events]);

  return {
    events: eventsWithColors,
    isLoading,
    error,
  };
}

export interface UseRemindersOptions {
  pollInterval?: number;
}

export interface UseRemindersReturn {
  reminders: CalendarEvent[];
  isLoading: boolean;
  error: Error | undefined;
}

/**
 * Hook for fetching reminders (events due soon)
 */
export function useReminders(options: UseRemindersOptions = {}): UseRemindersReturn {
  const { pollInterval } = options;
  const url = '/calendar/reminders';

  const { data, error, isLoading } = useSWR<RemindersResponse>(
    url,
    fetcher,
    {
      revalidateOnFocus: false,
      refreshInterval: pollInterval,
    }
  );

  const remindersWithColors = useMemo(() => {
    if (!data?.reminders) return [];
    return addColorToEvents(data.reminders);
  }, [data?.reminders]);

  return {
    reminders: remindersWithColors,
    isLoading,
    error,
  };
}

// Export event type colors for use in components
export { EVENT_TYPE_COLORS };
