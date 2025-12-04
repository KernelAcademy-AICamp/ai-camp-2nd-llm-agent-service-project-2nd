/**
 * Timeline Page
 * Displays evidence timeline for a case
 *
 * Feature: 002-evidence-timeline
 */

'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useMemo, useCallback, useState } from 'react';
import { ArrowLeft, Clock, AlertCircle, ChevronDown, RefreshCw } from 'lucide-react';
import Timeline from '@/components/evidence/Timeline';
import { useTimeline } from '@/hooks/useTimeline';
import { useAuth } from '@/hooks/useAuth';
import { TimelineFilter, COMMON_LABELS, SPEAKER_OPTIONS } from '@/types/timeline';

interface TimelinePageProps {
    params: { id: string };
}

export default function TimelinePage({ params }: TimelinePageProps) {
    const router = useRouter();
    const searchParams = useSearchParams();
    const { isAuthenticated, isLoading: authLoading } = useAuth();

    const caseId = params.id;

    // Parse filter from URL search params
    const initialFilter = useMemo((): TimelineFilter => {
        const filter: TimelineFilter = {
            limit: 50,
            offset: 0,
            sortOrder: (searchParams?.get('sort') as 'asc' | 'desc') || 'asc',
        };

        const dateStart = searchParams?.get('date_start');
        const dateEnd = searchParams?.get('date_end');
        const labels = searchParams?.get('labels');
        const speakers = searchParams?.get('speakers');
        const keyOnly = searchParams?.get('key_only');

        if (dateStart) filter.dateStart = dateStart;
        if (dateEnd) filter.dateEnd = dateEnd;
        if (labels) filter.labels = labels.split(',');
        if (speakers) filter.speakers = speakers.split(',');
        if (keyOnly === 'true') filter.keyOnly = true;

        return filter;
    }, [searchParams]);

    // Timeline hook
    const {
        data,
        isLoading,
        error,
        filter,
        setFilter,
        clearFilters,
        refetch,
        loadMore,
        hasMore,
    } = useTimeline(caseId, {
        initialFilter,
        autoFetch: isAuthenticated === true,
    });

    // Filter dropdown states
    const [showLabelFilter, setShowLabelFilter] = useState(false);
    const [showSpeakerFilter, setShowSpeakerFilter] = useState(false);

    // Update URL when filter changes
    useEffect(() => {
        const params = new URLSearchParams();

        if (filter.dateStart) params.set('date_start', filter.dateStart);
        if (filter.dateEnd) params.set('date_end', filter.dateEnd);
        if (filter.labels?.length) params.set('labels', filter.labels.join(','));
        if (filter.speakers?.length) params.set('speakers', filter.speakers.join(','));
        if (filter.keyOnly) params.set('key_only', 'true');
        if (filter.sortOrder && filter.sortOrder !== 'asc') params.set('sort', filter.sortOrder);

        const queryString = params.toString();
        const newUrl = queryString
            ? `/cases/${caseId}/timeline?${queryString}`
            : `/cases/${caseId}/timeline`;

        // Update URL without navigation
        window.history.replaceState(null, '', newUrl);
    }, [filter, caseId]);

    // Handle evidence selection
    const handleSelectEvidence = useCallback(
        (evidenceId: string) => {
            // Navigate to evidence detail (assuming route exists)
            router.push(`/evidence/${evidenceId}`);
        },
        [router]
    );

    // Toggle sort order
    const toggleSortOrder = useCallback(() => {
        setFilter({
            ...filter,
            sortOrder: filter.sortOrder === 'asc' ? 'desc' : 'asc',
        });
    }, [filter, setFilter]);

    // Toggle key evidence only
    const toggleKeyOnly = useCallback(() => {
        setFilter({
            ...filter,
            keyOnly: !filter.keyOnly,
        });
    }, [filter, setFilter]);

    // Toggle label filter
    const toggleLabel = useCallback(
        (label: string) => {
            const currentLabels = filter.labels || [];
            const newLabels = currentLabels.includes(label)
                ? currentLabels.filter((l) => l !== label)
                : [...currentLabels, label];

            setFilter({
                ...filter,
                labels: newLabels.length > 0 ? newLabels : undefined,
            });
        },
        [filter, setFilter]
    );

    // Toggle speaker filter
    const toggleSpeaker = useCallback(
        (speaker: string) => {
            const currentSpeakers = filter.speakers || [];
            const newSpeakers = currentSpeakers.includes(speaker)
                ? currentSpeakers.filter((s) => s !== speaker)
                : [...currentSpeakers, speaker];

            setFilter({
                ...filter,
                speakers: newSpeakers.length > 0 ? newSpeakers : undefined,
            });
        },
        [filter, setFilter]
    );

    // Check if any filter is active
    const hasActiveFilters = useMemo(() => {
        return (
            filter.dateStart ||
            filter.dateEnd ||
            (filter.labels && filter.labels.length > 0) ||
            (filter.speakers && filter.speakers.length > 0) ||
            filter.keyOnly
        );
    }, [filter]);

    // Auth loading state
    if (authLoading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
        );
    }

    // Not authenticated
    if (isAuthenticated === false) {
        router.push('/login');
        return null;
    }

    return (
        <div className="min-h-screen bg-gray-50">
            {/* Header */}
            <header className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        <div className="flex items-center">
                            <button
                                onClick={() => router.push(`/cases/${caseId}`)}
                                className="mr-4 p-2 rounded-md hover:bg-gray-100 transition-colors"
                            >
                                <ArrowLeft className="w-5 h-5 text-gray-600" />
                            </button>
                            <div>
                                <h1 className="text-lg font-semibold text-gray-900 flex items-center">
                                    <Clock className="w-5 h-5 mr-2 text-blue-600" />
                                    증거 타임라인
                                </h1>
                                {data && (
                                    <p className="text-sm text-gray-500">
                                        총 {data.totalCount}개 증거
                                        {data.filteredCount !== data.totalCount && (
                                            <span> (필터 적용: {data.filteredCount}개)</span>
                                        )}
                                    </p>
                                )}
                            </div>
                        </div>

                        <button
                            onClick={() => refetch()}
                            className="p-2 rounded-md hover:bg-gray-100 transition-colors"
                            title="새로고침"
                        >
                            <RefreshCw className={`w-5 h-5 text-gray-600 ${isLoading ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </div>
            </header>

            {/* Filter bar */}
            <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
                    <div className="flex flex-wrap items-center gap-2">
                        {/* Date range filter */}
                        <div className="flex items-center gap-2">
                            <input
                                type="date"
                                value={filter.dateStart || ''}
                                onChange={(e) =>
                                    setFilter({ ...filter, dateStart: e.target.value || undefined })
                                }
                                className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="시작일"
                            />
                            <span className="text-gray-400">~</span>
                            <input
                                type="date"
                                value={filter.dateEnd || ''}
                                onChange={(e) =>
                                    setFilter({ ...filter, dateEnd: e.target.value || undefined })
                                }
                                className="px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                placeholder="종료일"
                            />
                        </div>

                        {/* Label filter dropdown */}
                        <div className="relative">
                            <button
                                onClick={() => setShowLabelFilter(!showLabelFilter)}
                                className={`px-3 py-1 text-sm border rounded-md flex items-center gap-1 ${
                                    filter.labels?.length
                                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                                }`}
                            >
                                라벨
                                {filter.labels?.length ? ` (${filter.labels.length})` : ''}
                                <ChevronDown className="w-4 h-4" />
                            </button>
                            {showLabelFilter && (
                                <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-20 min-w-[150px]">
                                    {COMMON_LABELS.map((label) => (
                                        <label
                                            key={label}
                                            className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
                                        >
                                            <input
                                                type="checkbox"
                                                checked={filter.labels?.includes(label) || false}
                                                onChange={() => toggleLabel(label)}
                                                className="mr-2"
                                            />
                                            <span className="text-sm">{label}</span>
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Speaker filter dropdown */}
                        <div className="relative">
                            <button
                                onClick={() => setShowSpeakerFilter(!showSpeakerFilter)}
                                className={`px-3 py-1 text-sm border rounded-md flex items-center gap-1 ${
                                    filter.speakers?.length
                                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                                }`}
                            >
                                발화자
                                {filter.speakers?.length ? ` (${filter.speakers.length})` : ''}
                                <ChevronDown className="w-4 h-4" />
                            </button>
                            {showSpeakerFilter && (
                                <div className="absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-20 min-w-[120px]">
                                    {SPEAKER_OPTIONS.map((speaker) => (
                                        <label
                                            key={speaker}
                                            className="flex items-center px-3 py-2 hover:bg-gray-50 cursor-pointer"
                                        >
                                            <input
                                                type="checkbox"
                                                checked={filter.speakers?.includes(speaker) || false}
                                                onChange={() => toggleSpeaker(speaker)}
                                                className="mr-2"
                                            />
                                            <span className="text-sm">{speaker}</span>
                                        </label>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Key evidence toggle */}
                        <button
                            onClick={toggleKeyOnly}
                            className={`px-3 py-1 text-sm border rounded-md ${
                                filter.keyOnly
                                    ? 'border-amber-500 bg-amber-50 text-amber-700'
                                    : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                            }`}
                        >
                            핵심 증거만
                        </button>

                        {/* Sort toggle */}
                        <button
                            onClick={toggleSortOrder}
                            className="px-3 py-1 text-sm border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                        >
                            {filter.sortOrder === 'asc' ? '오래된 순' : '최신 순'}
                        </button>

                        {/* Clear filters */}
                        {hasActiveFilters && (
                            <button
                                onClick={clearFilters}
                                className="px-3 py-1 text-sm text-red-600 hover:text-red-800"
                            >
                                필터 초기화
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Close dropdowns when clicking outside */}
            {(showLabelFilter || showSpeakerFilter) && (
                <div
                    className="fixed inset-0 z-10"
                    onClick={() => {
                        setShowLabelFilter(false);
                        setShowSpeakerFilter(false);
                    }}
                />
            )}

            {/* Main content */}
            <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                {/* Error state */}
                {error && (
                    <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
                        <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
                        <span className="text-red-700">{error}</span>
                        <button
                            onClick={() => refetch()}
                            className="ml-auto text-red-600 hover:text-red-800 underline"
                        >
                            다시 시도
                        </button>
                    </div>
                )}

                {/* Statistics bar */}
                {data && !isLoading && (
                    <div className="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                            <div className="text-2xl font-bold text-gray-900">{data.totalCount}</div>
                            <div className="text-sm text-gray-500">전체 증거</div>
                        </div>
                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                            <div className="text-2xl font-bold text-amber-600">{data.keyEventsCount}</div>
                            <div className="text-sm text-gray-500">핵심 증거</div>
                        </div>
                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                            <div className="text-sm font-medium text-gray-900">
                                {data.dateRange.start || '-'}
                            </div>
                            <div className="text-sm text-gray-500">시작일</div>
                        </div>
                        <div className="bg-white p-4 rounded-lg border border-gray-200">
                            <div className="text-sm font-medium text-gray-900">
                                {data.dateRange.end || '-'}
                            </div>
                            <div className="text-sm text-gray-500">종료일</div>
                        </div>
                    </div>
                )}

                {/* Timeline */}
                <div className="bg-white rounded-lg border border-gray-200 p-6">
                    <Timeline
                        events={data?.events || []}
                        onSelect={handleSelectEvidence}
                        sortOrder={filter.sortOrder}
                        isLoading={isLoading}
                        showSignificance={true}
                    />

                    {/* Load more button */}
                    {hasMore && !isLoading && (
                        <div className="mt-6 text-center">
                            <button
                                onClick={loadMore}
                                className="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-800 border border-blue-300 rounded-md hover:bg-blue-50"
                            >
                                더 보기
                            </button>
                        </div>
                    )}
                </div>

                {/* Empty filter results */}
                {data && data.filteredCount === 0 && data.totalCount > 0 && (
                    <div className="mt-4 text-center text-gray-500">
                        <p>필터 조건에 맞는 증거가 없습니다.</p>
                        <button
                            onClick={clearFilters}
                            className="mt-2 text-blue-600 hover:text-blue-800 underline"
                        >
                            필터 초기화
                        </button>
                    </div>
                )}
            </main>
        </div>
    );
}
