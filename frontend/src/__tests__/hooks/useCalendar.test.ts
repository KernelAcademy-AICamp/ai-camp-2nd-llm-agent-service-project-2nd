/**
 * Integration tests for useCalendar hook
 * Task T128 - TDD RED Phase
 *
 * Tests for frontend/src/hooks/useCalendar.ts:
 * - Fetching events with date range
 * - Creating, updating, deleting events
 * - SWR caching and revalidation
 * - Error handling
 * - Loading states
 */

import { renderHook, waitFor, act } from '@testing-library/react';

// Mock fetch
const mockFetch = jest.fn();
global.fetch = mockFetch;

// Mock SWR
jest.mock('swr', () => ({
  __esModule: true,
  default: jest.fn(),
  useSWRConfig: () => ({
    mutate: jest.fn(),
  }),
}));

import useSWR from 'swr';

// Mock data (without color - this is what the API returns)
const mockEventsFromApi = [
  {
    id: 'event-1',
    user_id: 'user-1',
    title: '재판 출석',
    event_type: 'court',
    start_time: '2024-01-15T09:00:00Z',
    end_time: '2024-01-15T11:00:00Z',
    case_id: 'case-1',
    case_title: '이혼 소송 건',
    reminder_minutes: 60,
  },
  {
    id: 'event-2',
    user_id: 'user-1',
    title: '의뢰인 상담',
    event_type: 'meeting',
    start_time: '2024-01-16T14:00:00Z',
    end_time: '2024-01-16T15:00:00Z',
    reminder_minutes: 30,
  },
];

// Expected data (with color added by hook)
const mockEvents = [
  {
    ...mockEventsFromApi[0],
    color: '#ef4444', // court color
  },
  {
    ...mockEventsFromApi[1],
    color: '#3b82f6', // meeting color
  },
];

const mockUpcomingEventsFromApi = [
  {
    id: 'event-1',
    title: '재판 출석',
    event_type: 'court',
    start_time: '2024-01-15T09:00:00Z',
    case_title: '이혼 소송 건',
  },
];

// Expected data (with color added by hook)
const mockUpcomingEvents = [
  {
    ...mockUpcomingEventsFromApi[0],
    color: '#ef4444', // court color
  },
];

// Import after mocks
// Note: Hook doesn't exist yet, so this will fail (TDD RED phase)
import { useCalendar, useUpcomingEvents, useReminders } from '@/hooks/useCalendar';

describe('useCalendar hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useSWR as jest.Mock).mockImplementation((key, fetcher, options) => ({
      data: { events: mockEventsFromApi, total: 2 },
      error: undefined,
      isLoading: false,
      isValidating: false,
      mutate: jest.fn(),
    }));
  });

  describe('Data Fetching', () => {
    test('should return events', () => {
      const { result } = renderHook(() => useCalendar());

      expect(result.current.events).toEqual(mockEvents);
      expect(result.current.total).toBe(2);
    });

    test('should fetch with date range', () => {
      const startDate = new Date('2024-01-01');
      const endDate = new Date('2024-01-31');

      renderHook(() => useCalendar({ startDate, endDate }));

      expect(useSWR).toHaveBeenCalledWith(
        expect.stringContaining('start_date='),
        expect.any(Function),
        expect.any(Object)
      );
    });

    test('should handle loading state', () => {
      (useSWR as jest.Mock).mockReturnValue({
        data: undefined,
        error: undefined,
        isLoading: true,
        mutate: jest.fn(),
      });

      const { result } = renderHook(() => useCalendar());

      expect(result.current.isLoading).toBe(true);
      expect(result.current.events).toEqual([]);
    });

    test('should handle error state', () => {
      const error = new Error('Failed to fetch events');
      (useSWR as jest.Mock).mockReturnValue({
        data: undefined,
        error,
        isLoading: false,
        mutate: jest.fn(),
      });

      const { result } = renderHook(() => useCalendar());

      expect(result.current.error).toBe(error);
      expect(result.current.events).toEqual([]);
    });

    test('should add color property based on event_type', () => {
      const { result } = renderHook(() => useCalendar());

      const courtEvent = result.current.events.find(e => e.event_type === 'court');
      const meetingEvent = result.current.events.find(e => e.event_type === 'meeting');

      expect(courtEvent?.color).toBe('#ef4444'); // Red for court
      expect(meetingEvent?.color).toBe('#3b82f6'); // Blue for meeting
    });
  });

  describe('Create Event', () => {
    test('should create event successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 'new-event', title: 'New Event' }),
      });

      const { result } = renderHook(() => useCalendar());

      await act(async () => {
        const response = await result.current.createEvent({
          title: 'New Event',
          event_type: 'meeting',
          start_time: '2024-01-20T10:00:00Z',
        });

        expect(response.id).toBe('new-event');
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/calendar/events'),
        expect.objectContaining({
          method: 'POST',
          body: expect.any(String),
        })
      );
    });

    test('should throw error on create failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ detail: 'Invalid data' }),
      });

      const { result } = renderHook(() => useCalendar());

      await act(async () => {
        await expect(
          result.current.createEvent({
            title: '',
            event_type: 'meeting',
            start_time: '2024-01-20T10:00:00Z',
          })
        ).rejects.toThrow();
      });
    });

    test('should mutate cache after create', async () => {
      const mutateMock = jest.fn();
      (useSWR as jest.Mock).mockReturnValue({
        data: { events: mockEvents, total: 2 },
        error: undefined,
        isLoading: false,
        mutate: mutateMock,
      });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 'new-event' }),
      });

      const { result } = renderHook(() => useCalendar());

      await act(async () => {
        await result.current.createEvent({
          title: 'New Event',
          event_type: 'meeting',
          start_time: '2024-01-20T10:00:00Z',
        });
      });

      expect(mutateMock).toHaveBeenCalled();
    });
  });

  describe('Update Event', () => {
    test('should update event successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ id: 'event-1', title: 'Updated Title' }),
      });

      const { result } = renderHook(() => useCalendar());

      await act(async () => {
        const response = await result.current.updateEvent('event-1', {
          title: 'Updated Title',
        });

        expect(response.title).toBe('Updated Title');
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/calendar/events/event-1'),
        expect.objectContaining({
          method: 'PUT',
        })
      );
    });

    test('should throw error on update failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: 'Event not found' }),
      });

      const { result } = renderHook(() => useCalendar());

      await act(async () => {
        await expect(
          result.current.updateEvent('nonexistent', { title: 'Test' })
        ).rejects.toThrow();
      });
    });
  });

  describe('Delete Event', () => {
    test('should delete event successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({}),
      });

      const { result } = renderHook(() => useCalendar());

      await act(async () => {
        await result.current.deleteEvent('event-1');
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/calendar/events/event-1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    test('should throw error on delete failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: () => Promise.resolve({ detail: 'Not authorized' }),
      });

      const { result } = renderHook(() => useCalendar());

      await act(async () => {
        await expect(
          result.current.deleteEvent('event-1')
        ).rejects.toThrow();
      });
    });
  });

  describe('Event Type Colors', () => {
    test('should return correct color for court event', () => {
      const { result } = renderHook(() => useCalendar());
      expect(result.current.getEventColor('court')).toBe('#ef4444');
    });

    test('should return correct color for meeting event', () => {
      const { result } = renderHook(() => useCalendar());
      expect(result.current.getEventColor('meeting')).toBe('#3b82f6');
    });

    test('should return correct color for deadline event', () => {
      const { result } = renderHook(() => useCalendar());
      expect(result.current.getEventColor('deadline')).toBe('#f59e0b');
    });

    test('should return correct color for internal event', () => {
      const { result } = renderHook(() => useCalendar());
      expect(result.current.getEventColor('internal')).toBe('#8b5cf6');
    });

    test('should return default color for other event', () => {
      const { result } = renderHook(() => useCalendar());
      expect(result.current.getEventColor('other')).toBe('#6b7280');
    });
  });

  describe('Date Navigation', () => {
    test('should set date range', () => {
      const { result } = renderHook(() => useCalendar());

      const newStart = new Date('2024-02-01');
      const newEnd = new Date('2024-02-29');

      act(() => {
        result.current.setDateRange(newStart, newEnd);
      });

      expect(result.current.startDate).toEqual(newStart);
      expect(result.current.endDate).toEqual(newEnd);
    });

    test('should navigate to month', () => {
      const { result } = renderHook(() => useCalendar());

      act(() => {
        result.current.goToMonth(new Date('2024-03-15'));
      });

      // Should set date range to March 2024
      expect(result.current.startDate?.getMonth()).toBe(2); // March (0-indexed)
      expect(result.current.endDate?.getMonth()).toBe(2);
    });
  });
});

describe('useUpcomingEvents hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useSWR as jest.Mock).mockReturnValue({
      data: { events: mockUpcomingEventsFromApi },
      error: undefined,
      isLoading: false,
    });
  });

  test('should return upcoming events', () => {
    const { result } = renderHook(() => useUpcomingEvents());

    expect(result.current.events).toEqual(mockUpcomingEvents);
  });

  test('should fetch with default 7 days', () => {
    renderHook(() => useUpcomingEvents());

    expect(useSWR).toHaveBeenCalledWith(
      expect.stringContaining('/calendar/upcoming'),
      expect.any(Function),
      expect.any(Object)
    );
  });

  test('should support custom days parameter', () => {
    renderHook(() => useUpcomingEvents(14));

    expect(useSWR).toHaveBeenCalledWith(
      expect.stringContaining('days=14'),
      expect.any(Function),
      expect.any(Object)
    );
  });
});

describe('useReminders hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useSWR as jest.Mock).mockReturnValue({
      data: { reminders: [] },
      error: undefined,
      isLoading: false,
    });
  });

  test('should return reminders', () => {
    const { result } = renderHook(() => useReminders());

    expect(result.current.reminders).toBeDefined();
  });

  test('should fetch from reminders endpoint', () => {
    renderHook(() => useReminders());

    expect(useSWR).toHaveBeenCalledWith(
      expect.stringContaining('/calendar/reminders'),
      expect.any(Function),
      expect.any(Object)
    );
  });

  test('should poll at interval when enabled', () => {
    renderHook(() => useReminders({ pollInterval: 60000 }));

    expect(useSWR).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(Function),
      expect.objectContaining({
        refreshInterval: 60000,
      })
    );
  });
});
