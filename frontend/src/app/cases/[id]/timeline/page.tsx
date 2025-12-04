/**
 * Timeline Page
 * Display evidence timeline for a case
 *
 * Feature: 002-evidence-timeline
 */

'use client';

import { use } from 'react';
import Link from 'next/link';
import { useTimeline } from '@/hooks/useTimeline';
import { Timeline } from '@/components/evidence/Timeline';

interface TimelinePageProps {
    params: Promise<{ id: string }>;
}

export default function TimelinePage({ params }: TimelinePageProps) {
    const { id: caseId } = use(params);

    const {
        data,
        events,
        isLoading,
        error,
        filter,
        setFilter,
        loadMore,
        hasMore,
    } = useTimeline({
        caseId,
        autoFetch: true,
    });

    const handleSortChange = (order: 'asc' | 'desc') => {
        setFilter({ sortOrder: order });
    };

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b">
                <div className="max-w-5xl mx-auto px-4 py-4">
                    <nav className="flex items-center gap-2 text-sm text-gray-500 mb-2">
                        <Link href="/cases" className="hover:text-gray-700">
                            케이스 목록
                        </Link>
                        <span>/</span>
                        <Link href={`/cases/${caseId}`} className="hover:text-gray-700">
                            케이스 상세
                        </Link>
                        <span>/</span>
                        <span className="text-gray-900">타임라인</span>
                    </nav>
                    <h1 className="text-2xl font-bold text-gray-900">
                        증거 타임라인
                    </h1>
                    <p className="text-gray-600 mt-1">
                        케이스의 모든 증거를 시간순으로 확인합니다.
                    </p>
                </div>
            </header>

            {/* Main content */}
            <main className="max-w-5xl mx-auto px-4 py-6">
                <Timeline
                    data={data}
                    events={events}
                    isLoading={isLoading}
                    error={error}
                    sortOrder={filter.sortOrder}
                    onSortChange={handleSortChange}
                    onLoadMore={loadMore}
                    hasMore={hasMore}
                    caseId={caseId}
                />
            </main>
        </div>
    );
}
