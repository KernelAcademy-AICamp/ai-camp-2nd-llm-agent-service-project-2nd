/**
 * Timeline Types
 * 타임라인 이벤트 및 관련 타입 정의
 */

// =============================================================================
// Enums
// =============================================================================

export enum TimelineEventType {
  MESSAGE = 'message',
  DOCUMENT = 'document',
  IMAGE = 'image',
  AUDIO = 'audio',
  VIDEO = 'video',
  INCIDENT = 'incident',
}

// =============================================================================
// Interfaces
// =============================================================================

/**
 * 타임라인 이벤트
 */
export interface TimelineEvent {
  event_id: string;
  evidence_id: string;
  case_id: string;
  timestamp: string; // ISO 8601
  date: string; // YYYY-MM-DD
  time: string; // HH:MM
  description: string;
  content_preview?: string;
  event_type: TimelineEventType;
  labels: string[];
  speaker?: string;
  source_file: string;
  significance: number; // 1-5
  is_pinned: boolean;
  is_key_evidence: boolean;
  metadata?: Record<string, unknown>;
}

/**
 * 타임라인 결과
 */
export interface TimelineResult {
  case_id: string;
  events: TimelineEvent[];
  total_events: number;
  date_range: {
    start: string | null;
    end: string | null;
  };
  events_by_type: Record<string, number>;
  events_by_label: Record<string, number>;
  key_events_count: number;
  generated_at: string;
}

/**
 * 월별 그룹
 */
export interface TimelineMonthGroup {
  month: string; // YYYY-MM
  label: string; // 예: "2024년 3월"
  events: TimelineEvent[];
  eventCount: number;
}

/**
 * 타임라인 노드 (마인드맵용)
 */
export interface TimelineNode {
  id: string;
  type: 'root' | 'month' | 'event';
  label: string;
  date?: string;
  children?: TimelineNode[];
  // event 타입인 경우
  event?: TimelineEvent;
}

/**
 * 타임라인 트리 (마인드맵용)
 */
export interface TimelineTree {
  case_id: string;
  root: TimelineNode;
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * 이벤트 타입별 아이콘 반환
 */
export function getEventTypeIcon(type: TimelineEventType): string {
  const icons: Record<TimelineEventType, string> = {
    [TimelineEventType.MESSAGE]: '💬',
    [TimelineEventType.DOCUMENT]: '📄',
    [TimelineEventType.IMAGE]: '📷',
    [TimelineEventType.AUDIO]: '🎤',
    [TimelineEventType.VIDEO]: '🎥',
    [TimelineEventType.INCIDENT]: '⚠️',
  };
  return icons[type] || '📌';
}

/**
 * 이벤트 타입 한글 라벨
 */
export function getEventTypeLabel(type: TimelineEventType): string {
  const labels: Record<TimelineEventType, string> = {
    [TimelineEventType.MESSAGE]: '메시지',
    [TimelineEventType.DOCUMENT]: '문서',
    [TimelineEventType.IMAGE]: '이미지',
    [TimelineEventType.AUDIO]: '음성',
    [TimelineEventType.VIDEO]: '영상',
    [TimelineEventType.INCIDENT]: '사건',
  };
  return labels[type] || '기타';
}

/**
 * 중요도별 색상 반환
 */
export function getSignificanceColor(significance: number): string {
  const colors: Record<number, string> = {
    1: '#9E9E9E', // 회색
    2: '#2196F3', // 파랑
    3: '#FF9800', // 주황
    4: '#F44336', // 빨강
    5: '#E91E63', // 핑크
  };
  return colors[significance] || colors[1];
}

/**
 * 날짜를 한글 월로 변환
 */
export function formatMonthLabel(yearMonth: string): string {
  const [year, month] = yearMonth.split('-');
  return `${year}년 ${parseInt(month, 10)}월`;
}

/**
 * 이벤트를 월별로 그룹화
 */
export function groupEventsByMonth(events: TimelineEvent[]): TimelineMonthGroup[] {
  const groups: Record<string, TimelineEvent[]> = {};

  events.forEach((event) => {
    const month = event.date.substring(0, 7); // YYYY-MM
    if (!groups[month]) {
      groups[month] = [];
    }
    groups[month].push(event);
  });

  return Object.entries(groups)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, monthEvents]) => ({
      month,
      label: formatMonthLabel(month),
      events: monthEvents,
      eventCount: monthEvents.length,
    }));
}

/**
 * 타임라인 결과를 트리 구조로 변환
 */
export function convertToTree(result: TimelineResult): TimelineTree {
  const monthGroups = groupEventsByMonth(result.events);

  const monthNodes: TimelineNode[] = monthGroups.map((group) => ({
    id: group.month,
    type: 'month' as const,
    label: group.label,
    date: group.month,
    children: group.events.map((event) => ({
      id: event.event_id,
      type: 'event' as const,
      label: event.description,
      date: event.date,
      event,
    })),
  }));

  return {
    case_id: result.case_id,
    root: {
      id: 'root',
      type: 'root',
      label: '사건 타임라인',
      children: monthNodes,
    },
  };
}
