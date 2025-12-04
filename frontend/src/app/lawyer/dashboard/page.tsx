/**
 * Lawyer Dashboard Page
 * 003-role-based-ui Feature
 *
 * US2: 변호사 대시보드
 * - 진행중/검토필요/완료 케이스 통계 카드
 * - 최근 케이스 목록 (5건)
 * - 오늘/이번주 일정 요약
 * - 최근 알림 피드
 * - 월간 업무 통계 차트
 */

import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '대시보드 - Legal Evidence Hub',
  description: '변호사 대시보드',
};

// Stats Card Component
function StatsCard({
  title,
  value,
  change,
  changeType,
  icon,
}: {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon: React.ReactNode;
}) {
  const changeColors = {
    increase: 'text-[var(--color-success)]',
    decrease: 'text-[var(--color-error)]',
    neutral: 'text-[var(--color-text-secondary)]',
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-[var(--color-border-default)]">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-[var(--color-text-secondary)]">{title}</p>
          <p className="text-2xl font-semibold mt-1 text-[var(--color-text-primary)]">
            {value}
          </p>
          {change && (
            <p className={`text-sm mt-1 ${changeColors[changeType || 'neutral']}`}>
              {change}
            </p>
          )}
        </div>
        <div className="w-12 h-12 rounded-lg bg-[var(--color-primary-light)] flex items-center justify-center text-[var(--color-primary)]">
          {icon}
        </div>
      </div>
    </div>
  );
}

// Recent Case Item
function RecentCaseItem({
  title,
  clientName,
  status,
  updatedAt,
}: {
  title: string;
  clientName: string;
  status: 'active' | 'review' | 'closed';
  updatedAt: string;
}) {
  const statusStyles = {
    active: 'bg-[var(--color-primary-light)] text-[var(--color-primary)]',
    review: 'bg-[var(--color-warning-light)] text-[var(--color-warning)]',
    closed: 'bg-[var(--color-neutral-100)] text-[var(--color-text-secondary)]',
  };

  const statusLabels = {
    active: '진행중',
    review: '검토필요',
    closed: '완료',
  };

  return (
    <div className="flex items-center gap-4 p-4 hover:bg-[var(--color-bg-secondary)] rounded-lg transition-colors cursor-pointer">
      <div className="flex-1 min-w-0">
        <p className="font-medium text-[var(--color-text-primary)] truncate">{title}</p>
        <p className="text-sm text-[var(--color-text-secondary)]">{clientName}</p>
      </div>
      <div className="flex items-center gap-3">
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusStyles[status]}`}>
          {statusLabels[status]}
        </span>
        <span className="text-xs text-[var(--color-text-tertiary)]">{updatedAt}</span>
      </div>
    </div>
  );
}

// Event Item
function EventItem({
  title,
  time,
  type,
}: {
  title: string;
  time: string;
  type: 'court' | 'meeting' | 'deadline';
}) {
  const typeStyles = {
    court: 'bg-[var(--color-error-light)] border-[var(--color-error)]',
    meeting: 'bg-[var(--color-primary-light)] border-[var(--color-primary)]',
    deadline: 'bg-[var(--color-warning-light)] border-[var(--color-warning)]',
  };

  return (
    <div className={`p-3 rounded-lg border-l-4 ${typeStyles[type]}`}>
      <p className="font-medium text-sm text-[var(--color-text-primary)]">{title}</p>
      <p className="text-xs text-[var(--color-text-secondary)] mt-1">{time}</p>
    </div>
  );
}

export default function LawyerDashboardPage() {
  // Mock data - will be replaced with real API data
  const stats = {
    activeCases: 12,
    reviewNeeded: 3,
    completedCases: 45,
    totalEvidence: 234,
  };

  const recentCases = [
    { id: '1', title: '김영희 이혼 소송', clientName: '김영희', status: 'active' as const, updatedAt: '2시간 전' },
    { id: '2', title: '박철수 위자료 청구', clientName: '박철수', status: 'review' as const, updatedAt: '5시간 전' },
    { id: '3', title: '이미영 양육권 분쟁', clientName: '이미영', status: 'active' as const, updatedAt: '1일 전' },
    { id: '4', title: '최정민 재산분할', clientName: '최정민', status: 'closed' as const, updatedAt: '2일 전' },
    { id: '5', title: '정수연 합의이혼', clientName: '정수연', status: 'active' as const, updatedAt: '3일 전' },
  ];

  const todayEvents = [
    { id: '1', title: '김영희 재판 출석', time: '오전 10:00', type: 'court' as const },
    { id: '2', title: '박철수 상담', time: '오후 2:00', type: 'meeting' as const },
    { id: '3', title: '이미영 답변서 마감', time: '오후 6:00', type: 'deadline' as const },
  ];

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">대시보드</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">오늘의 업무 현황을 확인하세요.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="진행중 케이스"
          value={stats.activeCases}
          change="+2 이번 주"
          changeType="increase"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
            </svg>
          }
        />
        <StatsCard
          title="검토 필요"
          value={stats.reviewNeeded}
          change="3건 대기중"
          changeType="neutral"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          }
        />
        <StatsCard
          title="완료된 케이스"
          value={stats.completedCases}
          change="+5 이번 달"
          changeType="increase"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
        />
        <StatsCard
          title="총 증거자료"
          value={stats.totalEvidence}
          change="+23 이번 주"
          changeType="increase"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Cases - 2 columns */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-[var(--color-border-default)]">
          <div className="p-4 border-b border-[var(--color-border-default)] flex items-center justify-between">
            <h2 className="font-semibold text-[var(--color-text-primary)]">최근 케이스</h2>
            <a
              href="/lawyer/cases"
              className="text-sm text-[var(--color-primary)] hover:underline"
            >
              전체보기
            </a>
          </div>
          <div className="divide-y divide-[var(--color-border-default)]">
            {recentCases.map((caseItem) => (
              <RecentCaseItem key={caseItem.id} {...caseItem} />
            ))}
          </div>
        </div>

        {/* Today's Schedule - 1 column */}
        <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)]">
          <div className="p-4 border-b border-[var(--color-border-default)] flex items-center justify-between">
            <h2 className="font-semibold text-[var(--color-text-primary)]">오늘 일정</h2>
            <a
              href="/lawyer/calendar"
              className="text-sm text-[var(--color-primary)] hover:underline"
            >
              캘린더
            </a>
          </div>
          <div className="p-4 space-y-3">
            {todayEvents.length > 0 ? (
              todayEvents.map((event) => (
                <EventItem key={event.id} {...event} />
              ))
            ) : (
              <p className="text-center text-[var(--color-text-secondary)] py-4">
                오늘 일정이 없습니다.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
