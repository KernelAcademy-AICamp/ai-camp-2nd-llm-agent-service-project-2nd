/**
 * Lawyer Dashboard Page
 * 003-role-based-ui Feature - US2
 * 007-lawyer-portal-v1 Feature - US7 (Today View)
 *
 * Dashboard:
 * - 오늘 내가 통제해야 할 사건/증거/드래프트를 상단에 배치
 * - 우선순위 기반 카드 위주
 */

'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useLawyerDashboard } from '@/hooks/useLawyerDashboard';
import { useTodayView } from '@/hooks/useTodayView';
import { StatsCard } from '@/components/lawyer/StatsCard';
import { TodayCard } from '@/components/lawyer/TodayCard';
import { WeeklyPreview } from '@/components/lawyer/WeeklyPreview';
import { DashboardSkeleton } from '@/components/shared/LoadingSkeletons';
import { useRole } from '@/hooks/useRole';
import { getCaseDetailPath } from '@/lib/portalPaths';

// Icons for stats cards (LDS2 Compact - 20px icons)
const ActiveIcon = () => (
  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
  </svg>
);

const CompletedIcon = () => (
  <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
      className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 dark:hover:bg-neutral-700 rounded transition-colors cursor-pointer"
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onClick()}
    >
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{title}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400">{client_name || '-'}</p>
      </div>
      <div className="flex items-center gap-2">
        <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded-full ${statusStyles[status] || statusStyles.active}`}>
          {statusLabels[status] || status}
        </span>
        <span className="text-[10px] text-gray-400">{formatDate(updated_at)}</span>
      </div>
    </div>
  );
}

export default function LawyerDashboardPage() {
  const router = useRouter();
  const { user } = useRole();
  const { data, isLoading, error } = useLawyerDashboard();
  const {
    urgent,
    thisWeek,
    allComplete,
    isLoading: todayLoading,
  } = useTodayView();

  // Loading state
  if (isLoading) {
    return <DashboardSkeleton />;
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-gray-100">대시보드</h1>
          <p className="text-red-500 mt-1">오류: {error}</p>
        </div>
      </div>
    );
  }

  const statsIcons = [<ActiveIcon key="0" />, <CompletedIcon key="1" />];

  return (
    <div className="space-y-4">
      {/* Page Title - LDS2 Compact */}
      <div>
        <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">대시보드</h1>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
          환영합니다{user?.name ? `, ${user.name}님` : ''}. 오늘의 업무 현황을 확인하세요.
        </p>
      </div>

      {/* Stats Grid - LDS2 Compact */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
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
            <StatsCard label="진행 중 케이스" value={data?.stats?.total_cases || 0} icon={<ActiveIcon />} />
            <StatsCard label="이번 달 완료" value={data?.stats?.completed_this_month || 0} icon={<CompletedIcon />} />
          </>
        )}
      </div>

      {/* Today View Section - LDS2 Compact */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Today's Urgent Items */}
        <TodayCard items={urgent} allComplete={allComplete} isLoading={todayLoading} />

        {/* This Week's Preview */}
        <WeeklyPreview items={thisWeek} isLoading={todayLoading} />
      </div>

      {/* Main Content Grid - LDS2 Compact */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Recent Cases - Full width */}
        <div className="lg:col-span-3 bg-white dark:bg-neutral-800 rounded-lg shadow-sm border border-gray-200 dark:border-neutral-700">
          <div className="px-3 py-2 border-b border-gray-200 dark:border-neutral-700 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">최근 케이스</h2>
            <Link
              href="/lawyer/cases"
              className="text-xs text-blue-600 hover:underline"
            >
              전체보기
            </Link>
          </div>
          <div className="divide-y divide-gray-100 dark:divide-neutral-700">
            {data?.recent_cases && data.recent_cases.length > 0 ? (
              data.recent_cases.map((caseItem, idx) => {
                // Debug: log if id is missing
                if (!caseItem.id) {
                  console.error(`[Dashboard] recent_cases[${idx}] missing id:`, caseItem);
                }
                const targetPath = getCaseDetailPath('lawyer', caseItem.id);
                console.log(`[Dashboard] Case "${caseItem.title}" -> ${targetPath}`);
                return (
                  <RecentCaseItem
                    key={caseItem.id || idx}
                    {...caseItem}
                    onClick={() => router.push(targetPath)}
                  />
                );
              })
            ) : (
              <p className="text-center text-gray-500 dark:text-gray-400 py-8">
                최근 케이스가 없습니다.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
