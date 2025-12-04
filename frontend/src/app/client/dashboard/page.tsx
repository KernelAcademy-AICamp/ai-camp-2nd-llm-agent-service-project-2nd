/**
 * Client Dashboard Page
 * 003-role-based-ui Feature
 *
 * US4: 의뢰인 포털
 * - 케이스 진행 상황
 * - 진행 단계 시각화 (Progress Bar)
 * - 최근 활동
 * - 변호사 연락처
 */

import { Metadata } from 'next';

export const metadata: Metadata = {
  title: '내 현황 - Legal Evidence Hub',
  description: '의뢰인 대시보드',
};

// Progress Step Component
function ProgressStep({
  step,
  title,
  status,
  date,
}: {
  step: number;
  title: string;
  status: 'completed' | 'current' | 'pending';
  date?: string;
}) {
  const statusStyles = {
    completed: {
      circle: 'bg-[var(--color-success)] text-white',
      line: 'bg-[var(--color-success)]',
      text: 'text-[var(--color-text-primary)]',
    },
    current: {
      circle: 'bg-[var(--color-primary)] text-white ring-4 ring-[var(--color-primary-light)]',
      line: 'bg-[var(--color-neutral-200)]',
      text: 'text-[var(--color-primary)] font-semibold',
    },
    pending: {
      circle: 'bg-[var(--color-neutral-200)] text-[var(--color-text-tertiary)]',
      line: 'bg-[var(--color-neutral-200)]',
      text: 'text-[var(--color-text-tertiary)]',
    },
  };

  const styles = statusStyles[status];

  return (
    <div className="flex items-start gap-4">
      <div className="flex flex-col items-center">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${styles.circle}`}>
          {status === 'completed' ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            step
          )}
        </div>
        <div className={`w-0.5 h-12 ${styles.line}`} />
      </div>
      <div className="flex-1 pb-8">
        <p className={`${styles.text}`}>{title}</p>
        {date && (
          <p className="text-sm text-[var(--color-text-secondary)] mt-1">{date}</p>
        )}
      </div>
    </div>
  );
}

// Activity Item
function ActivityItem({
  title,
  description,
  time,
  type,
}: {
  title: string;
  description: string;
  time: string;
  type: 'evidence' | 'message' | 'document' | 'status';
}) {
  const typeIcons = {
    evidence: (
      <div className="w-8 h-8 rounded-full bg-[var(--color-primary-light)] flex items-center justify-center text-[var(--color-primary)]">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
    ),
    message: (
      <div className="w-8 h-8 rounded-full bg-[var(--color-success-light)] flex items-center justify-center text-[var(--color-success)]">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </div>
    ),
    document: (
      <div className="w-8 h-8 rounded-full bg-[var(--color-warning-light)] flex items-center justify-center text-[var(--color-warning)]">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
    ),
    status: (
      <div className="w-8 h-8 rounded-full bg-[var(--color-secondary-light)] flex items-center justify-center text-[var(--color-secondary)]">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
    ),
  };

  return (
    <div className="flex items-start gap-3 p-3 hover:bg-[var(--color-bg-secondary)] rounded-lg transition-colors">
      {typeIcons[type]}
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm text-[var(--color-text-primary)]">{title}</p>
        <p className="text-sm text-[var(--color-text-secondary)] truncate">{description}</p>
      </div>
      <span className="text-xs text-[var(--color-text-tertiary)] whitespace-nowrap">{time}</span>
    </div>
  );
}

export default function ClientDashboardPage() {
  // Mock data
  const caseProgress = [
    { step: 1, title: '상담 완료', status: 'completed' as const, date: '2024년 11월 15일' },
    { step: 2, title: '증거자료 수집', status: 'completed' as const, date: '2024년 11월 20일' },
    { step: 3, title: '서류 작성 중', status: 'current' as const, date: '진행 중' },
    { step: 4, title: '법원 제출', status: 'pending' as const },
    { step: 5, title: '재판 진행', status: 'pending' as const },
  ];

  const recentActivity = [
    { id: '1', title: '새 증거자료 업로드됨', description: '카카오톡 대화내역 3건', time: '2시간 전', type: 'evidence' as const },
    { id: '2', title: '변호사 메시지', description: '서류 검토 요청드립니다.', time: '5시간 전', type: 'message' as const },
    { id: '3', title: '서류 작성 완료', description: '답변서 초안이 준비되었습니다.', time: '1일 전', type: 'document' as const },
    { id: '4', title: '케이스 상태 변경', description: '증거 수집 → 서류 작성', time: '3일 전', type: 'status' as const },
  ];

  const lawyerInfo = {
    name: '김변호사',
    firm: '정의법률사무소',
    phone: '02-1234-5678',
    email: 'kim@justice-law.com',
  };

  return (
    <div className="space-y-6">
      {/* Welcome Message */}
      <div className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-primary-hover)] rounded-xl p-6 text-white">
        <h1 className="text-2xl font-semibold">안녕하세요, 의뢰인님</h1>
        <p className="mt-2 opacity-90">현재 케이스가 순조롭게 진행되고 있습니다.</p>
        <div className="mt-4 flex items-center gap-2">
          <span className="px-3 py-1 bg-white/20 rounded-full text-sm">진행률 60%</span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Case Progress - 2 columns */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-[var(--color-border-default)]">
          <div className="p-4 border-b border-[var(--color-border-default)]">
            <h2 className="font-semibold text-[var(--color-text-primary)]">케이스 진행 상황</h2>
          </div>
          <div className="p-6">
            {caseProgress.map((step, index) => (
              <ProgressStep
                key={step.step}
                {...step}
              />
            ))}
          </div>
        </div>

        {/* Lawyer Info - 1 column */}
        <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)]">
          <div className="p-4 border-b border-[var(--color-border-default)]">
            <h2 className="font-semibold text-[var(--color-text-primary)]">담당 변호사</h2>
          </div>
          <div className="p-6">
            <div className="flex items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-full bg-[var(--color-secondary)] flex items-center justify-center text-white text-xl font-semibold">
                {lawyerInfo.name.slice(0, 1)}
              </div>
              <div>
                <p className="font-semibold text-lg text-[var(--color-text-primary)]">{lawyerInfo.name}</p>
                <p className="text-sm text-[var(--color-text-secondary)]">{lawyerInfo.firm}</p>
              </div>
            </div>

            <div className="space-y-3">
              <a
                href={`tel:${lawyerInfo.phone}`}
                className="flex items-center gap-3 p-3 rounded-lg border border-[var(--color-border-default)] hover:bg-[var(--color-bg-secondary)] transition-colors"
              >
                <svg className="w-5 h-5 text-[var(--color-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                </svg>
                <span className="text-sm">{lawyerInfo.phone}</span>
              </a>
              <a
                href={`mailto:${lawyerInfo.email}`}
                className="flex items-center gap-3 p-3 rounded-lg border border-[var(--color-border-default)] hover:bg-[var(--color-bg-secondary)] transition-colors"
              >
                <svg className="w-5 h-5 text-[var(--color-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                <span className="text-sm truncate">{lawyerInfo.email}</span>
              </a>
              <a
                href="/client/messages"
                className="flex items-center justify-center gap-2 p-3 rounded-lg bg-[var(--color-primary)] text-white hover:bg-[var(--color-primary-hover)] transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                <span>메시지 보내기</span>
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-sm border border-[var(--color-border-default)]">
        <div className="p-4 border-b border-[var(--color-border-default)]">
          <h2 className="font-semibold text-[var(--color-text-primary)]">최근 활동</h2>
        </div>
        <div className="divide-y divide-[var(--color-border-default)]">
          {recentActivity.map((activity) => (
            <ActivityItem key={activity.id} {...activity} />
          ))}
        </div>
      </div>
    </div>
  );
}
