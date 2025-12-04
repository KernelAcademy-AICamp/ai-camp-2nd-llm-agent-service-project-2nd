/**
 * Detective Dashboard Page
 * 003-role-based-ui Feature
 *
 * US5: 탐정 포털
 * - 의뢰 현황
 * - 진행 중 조사
 * - 일정 요약
 * - 수익 현황
 */

import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '대시보드 - Legal Evidence Hub',
  description: '탐정 대시보드',
};

// Stats Card Component
function StatsCard({
  title,
  value,
  subtitle,
  icon,
  color = 'primary',
}: {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'primary' | 'success' | 'warning' | 'secondary';
}) {
  const colorStyles = {
    primary: 'bg-[var(--color-primary-light)] text-[var(--color-primary)]',
    success: 'bg-[var(--color-success-light)] text-[var(--color-success)]',
    warning: 'bg-[var(--color-warning-light)] text-[var(--color-warning)]',
    secondary: 'bg-[var(--color-secondary-light)] text-[var(--color-secondary)]',
  };

  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-[var(--color-border-default)]">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-[var(--color-text-secondary)]">{title}</p>
          <p className="text-2xl font-semibold mt-1 text-[var(--color-text-primary)]">
            {value}
          </p>
          {subtitle && (
            <p className="text-sm text-[var(--color-text-tertiary)] mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorStyles[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

// Investigation Case Card
function InvestigationCard({
  title,
  lawyerName,
  status,
  deadline,
  recordCount,
}: {
  title: string;
  lawyerName: string;
  status: 'pending' | 'active' | 'review' | 'completed';
  deadline?: string;
  recordCount: number;
}) {
  const statusStyles = {
    pending: { bg: 'bg-[var(--color-warning-light)]', text: 'text-[var(--color-warning)]', label: '대기중' },
    active: { bg: 'bg-[var(--color-primary-light)]', text: 'text-[var(--color-primary)]', label: '진행중' },
    review: { bg: 'bg-[var(--color-secondary-light)]', text: 'text-[var(--color-secondary)]', label: '검토중' },
    completed: { bg: 'bg-[var(--color-success-light)]', text: 'text-[var(--color-success)]', label: '완료' },
  };

  const style = statusStyles[status];

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-[var(--color-border-default)] hover:shadow-md transition-shadow cursor-pointer">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-[var(--color-text-primary)] truncate">{title}</h3>
          <p className="text-sm text-[var(--color-text-secondary)]">의뢰: {lawyerName}</p>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${style.bg} ${style.text}`}>
          {style.label}
        </span>
      </div>

      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1 text-[var(--color-text-secondary)]">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            기록 {recordCount}건
          </span>
          {deadline && (
            <span className="flex items-center gap-1 text-[var(--color-warning)]">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {deadline}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// Quick Action Button
function QuickAction({
  title,
  description,
  icon,
  href,
}: {
  title: string;
  description: string;
  icon: React.ReactNode;
  href: string;
}) {
  return (
    <a
      href={href}
      className="flex items-center gap-4 p-4 bg-white rounded-xl border border-[var(--color-border-default)] hover:border-[var(--color-primary)] hover:shadow-md transition-all"
    >
      <div className="w-12 h-12 rounded-lg bg-[var(--color-primary-light)] flex items-center justify-center text-[var(--color-primary)]">
        {icon}
      </div>
      <div>
        <p className="font-medium text-[var(--color-text-primary)]">{title}</p>
        <p className="text-sm text-[var(--color-text-secondary)]">{description}</p>
      </div>
    </a>
  );
}

export default function DetectiveDashboardPage() {
  // Mock data
  const stats = {
    activeInvestigations: 5,
    pendingRequests: 2,
    completedThisMonth: 8,
    monthlyEarnings: '2,450,000',
  };

  const investigations = [
    { id: '1', title: '김영희 건 현장조사', lawyerName: '김변호사', status: 'active' as const, deadline: '마감 3일', recordCount: 12 },
    { id: '2', title: '박철수 건 증거수집', lawyerName: '이변호사', status: 'pending' as const, recordCount: 0 },
    { id: '3', title: '최정민 건 보고서 작성', lawyerName: '김변호사', status: 'review' as const, recordCount: 23 },
  ];

  const todaySchedule = [
    { id: '1', time: '10:00', title: '현장 조사 - 강남구', type: 'field' },
    { id: '2', time: '14:00', title: '변호사 미팅', type: 'meeting' },
    { id: '3', time: '17:00', title: '보고서 제출 마감', type: 'deadline' },
  ];

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-semibold text-[var(--color-text-primary)]">대시보드</h1>
        <p className="text-[var(--color-text-secondary)] mt-1">오늘의 조사 현황을 확인하세요.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          title="진행중 의뢰"
          value={stats.activeInvestigations}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          }
          color="primary"
        />
        <StatsCard
          title="대기중 요청"
          value={stats.pendingRequests}
          subtitle="승인 대기"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="warning"
        />
        <StatsCard
          title="이번 달 완료"
          value={stats.completedThisMonth}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="success"
        />
        <StatsCard
          title="이번 달 수익"
          value={`₩${stats.monthlyEarnings}`}
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          color="secondary"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <QuickAction
          title="현장 기록"
          description="GPS, 사진, 메모 기록"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          }
          href="/detective/field"
        />
        <QuickAction
          title="사진 촬영"
          description="증거 사진 즉시 업로드"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          }
          href="/detective/field?mode=photo"
        />
        <QuickAction
          title="보고서 작성"
          description="조사 결과 정리"
          icon={
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          }
          href="/detective/cases?action=report"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Investigations - 2 columns */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-[var(--color-text-primary)]">진행중 의뢰</h2>
            <a
              href="/detective/cases"
              className="text-sm text-[var(--color-primary)] hover:underline"
            >
              전체보기
            </a>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {investigations.map((inv) => (
              <InvestigationCard key={inv.id} {...inv} />
            ))}
          </div>
        </div>

        {/* Today's Schedule - 1 column */}
        <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)]">
          <div className="p-4 border-b border-[var(--color-border-default)] flex items-center justify-between">
            <h2 className="font-semibold text-[var(--color-text-primary)]">오늘 일정</h2>
            <a
              href="/detective/calendar"
              className="text-sm text-[var(--color-primary)] hover:underline"
            >
              캘린더
            </a>
          </div>
          <div className="p-4 space-y-3">
            {todaySchedule.map((event) => (
              <div
                key={event.id}
                className="flex items-center gap-3 p-3 rounded-lg bg-[var(--color-bg-secondary)]"
              >
                <span className="text-sm font-medium text-[var(--color-primary)] w-12">
                  {event.time}
                </span>
                <span className="text-sm text-[var(--color-text-primary)]">{event.title}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
