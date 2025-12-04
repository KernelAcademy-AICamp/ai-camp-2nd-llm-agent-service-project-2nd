/**
 * Lawyer Dashboard Page
 * 003-role-based-ui Feature - US2
 *
 * - 진행중/검토필요/완료 케이스 통계 카드
 * - 최근 케이스 목록 (5건)
 * - 오늘/이번주 일정 요약
 */

'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useLawyerDashboard } from '@/hooks/useLawyerDashboard';
import { StatsCard } from '@/components/lawyer/StatsCard';
import { DashboardSkeleton } from '@/components/shared/LoadingSkeletons';
import { useRole } from '@/hooks/useRole';

// Icons for stats cards
const BriefcaseIcon = () => (
  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
  </svg>
);

const ActiveIcon = () => (
  <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
  </svg>
);

const PendingIcon = () => (
  <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const CompletedIcon = () => (
  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

// Recent Case Item
function RecentCaseItem({
  id,
  title,
  client_name,
  status,
  updated_at,
  onClick,
}: {
  id: string;
  title: string;
  client_name?: string;
  status: string;
  updated_at: string;
  onClick: () => void;
}) {
  const statusStyles: Record<string, string> = {
    active: 'bg-green-100 text-green-700',
    open: 'bg-blue-100 text-blue-700',
    in_progress: 'bg-yellow-100 text-yellow-700',
    closed: 'bg-gray-100 text-gray-500',
  };

  const statusLabels: Record<string, string> = {
    active: '진행중',
    open: '열림',
    in_progress: '검토중',
    closed: '완료',
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) return '방금 전';
    if (hours < 24) return `${hours}시간 전`;
    if (days < 7) return `${days}일 전`;
    return date.toLocaleDateString('ko-KR');
  };

  return (
    <div
      onClick={onClick}
      className="flex items-center gap-4 p-4 hover:bg-gray-50 rounded-lg transition-colors cursor-pointer"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
    >
      <div className="flex-1 min-w-0">
        <p className="font-medium text-gray-900 truncate">{title}</p>
        <p className="text-sm text-gray-500">{client_name || '-'}</p>
      </div>
      <div className="flex items-center gap-3">
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusStyles[status] || statusStyles.active}`}>
          {statusLabels[status] || status}
        </span>
        <span className="text-xs text-gray-400">{formatDate(updated_at)}</span>
      </div>
    </div>
  );
}

// Event Item
function EventItem({
  title,
  event_type,
  start_time,
  case_title,
}: {
  title: string;
  event_type: string;
  start_time: string;
  case_title?: string;
}) {
  const typeStyles: Record<string, string> = {
    court: 'bg-red-50 border-red-500',
    meeting: 'bg-blue-50 border-blue-500',
    deadline: 'bg-yellow-50 border-yellow-500',
    other: 'bg-gray-50 border-gray-500',
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`p-3 rounded-lg border-l-4 ${typeStyles[event_type] || typeStyles.other}`}>
      <p className="font-medium text-sm text-gray-900">{title}</p>
      <div className="flex items-center gap-2 mt-1">
        <span className="text-xs text-gray-500">{formatTime(start_time)}</span>
        {case_title && (
          <span className="text-xs text-gray-400">• {case_title}</span>
        )}
      </div>
    </div>
  );
}

export default function LawyerDashboardPage() {
  const router = useRouter();
  const { user } = useRole();
  const { data, isLoading, error } = useLawyerDashboard();

  // Loading state
  if (isLoading) {
    return <DashboardSkeleton />;
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">대시보드</h1>
          <p className="text-red-500 mt-1">오류: {error}</p>
        </div>
      </div>
    );
  }

  const statsIcons = [<BriefcaseIcon key="0" />, <ActiveIcon key="1" />, <PendingIcon key="2" />, <CompletedIcon key="3" />];

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">대시보드</h1>
        <p className="text-gray-500 mt-1">
          환영합니다{user?.name ? `, ${user.name}님` : ''}. 오늘의 업무 현황을 확인하세요.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {data?.stats?.stats_cards?.map((card, index) => (
          <StatsCard
            key={card.label}
            label={card.label}
            value={card.value}
            change={card.change}
            trend={card.trend as 'up' | 'down' | 'stable'}
            icon={statsIcons[index % statsIcons.length]}
          />
        )) || (
          <>
            <StatsCard label="전체 케이스" value={data?.stats?.total_cases || 0} icon={<BriefcaseIcon />} />
            <StatsCard label="진행 중" value={data?.stats?.active_cases || 0} icon={<ActiveIcon />} />
            <StatsCard label="검토 대기" value={data?.stats?.pending_review || 0} icon={<PendingIcon />} />
            <StatsCard label="이번 달 완료" value={data?.stats?.completed_this_month || 0} icon={<CompletedIcon />} />
          </>
        )}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Cases - 2 columns */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">최근 케이스</h2>
            <Link
              href="/lawyer/cases"
              className="text-sm text-blue-600 hover:underline"
            >
              전체보기
            </Link>
          </div>
          <div className="divide-y divide-gray-200">
            {data?.recent_cases && data.recent_cases.length > 0 ? (
              data.recent_cases.map((caseItem) => (
                <RecentCaseItem
                  key={caseItem.id}
                  {...caseItem}
                  onClick={() => router.push(`/lawyer/cases/${caseItem.id}`)}
                />
              ))
            ) : (
              <p className="text-center text-gray-500 py-8">
                최근 케이스가 없습니다.
              </p>
            )}
          </div>
        </div>

        {/* Upcoming Events - 1 column */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200">
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">예정된 일정</h2>
            <Link
              href="/lawyer/calendar"
              className="text-sm text-blue-600 hover:underline"
            >
              캘린더
            </Link>
          </div>
          <div className="p-4 space-y-3">
            {data?.upcoming_events && data.upcoming_events.length > 0 ? (
              data.upcoming_events.map((event) => (
                <EventItem key={event.id} {...event} />
              ))
            ) : (
              <p className="text-center text-gray-500 py-4">
                예정된 일정이 없습니다.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
