'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Plus, LogOut, RefreshCw, FileText } from 'lucide-react';
import CaseCard from '@/components/cases/CaseCard';
import AddCaseModal from '@/components/cases/AddCaseModal';
import { Case } from '@/types/case';
import { useAuth } from '@/hooks/useAuth';
import { getCases } from '@/lib/api/cases';
import { mapApiCaseToCase } from '@/lib/utils/caseMapper';

// Example mock cases for demonstration
const EXAMPLE_CASES: Case[] = [
    {
        id: 'example-1',
        title: '이혼 소송 예시 - 김OO vs 박OO',
        clientName: '김OO',
        status: 'open',
        evidenceCount: 12,
        draftStatus: 'ready',
        lastUpdated: new Date().toISOString(),
    },
    {
        id: 'example-2',
        title: '협의이혼 예시 - 이OO vs 최OO',
        clientName: '이OO',
        status: 'open',
        evidenceCount: 5,
        draftStatus: 'generating',
        lastUpdated: new Date().toISOString(),
    },
];

// Error type for distinguishing different error states
type ErrorType = 'network' | 'server' | null;

export default function CasesPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading: isAuthLoading, logout, user } = useAuth();
    const [cases, setCases] = useState<Case[]>([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [errorType, setErrorType] = useState<ErrorType>(null);

    // Redirect to login if not authenticated
    useEffect(() => {
        if (!isAuthLoading && !isAuthenticated) {
            router.replace('/login');
        }
    }, [isAuthLoading, isAuthenticated, router]);

    // Fetch cases from API
    const fetchCases = useCallback(async () => {
        if (isAuthLoading || !isAuthenticated) return;

        setIsLoading(true);
        setError(null);
        setErrorType(null);

        try {
            const response = await getCases();
            if (response.error) {
                setError(response.error);
                setErrorType('server');
                setCases([]);
            } else if (response.data) {
                const mappedCases = response.data.cases.map(mapApiCaseToCase);
                setCases(mappedCases);
            }
        } catch (err) {
            if (err instanceof Error && err.message.includes('Network')) {
                setError('네트워크 연결을 확인해주세요.');
                setErrorType('network');
            } else {
                setError('사건 목록을 불러오는데 실패했습니다.');
                setErrorType('server');
            }
            setCases([]);
        } finally {
            setIsLoading(false);
        }
    }, [isAuthLoading, isAuthenticated]);

    useEffect(() => {
        fetchCases();
    }, [fetchCases]);

    // Show loading while checking auth or fetching cases
    if (isAuthLoading || !isAuthenticated || isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-neutral-50">
                <div className="text-gray-500">로딩 중...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-neutral-50">
            {/* Header / Navigation (To be separated later) */}
            <nav className="bg-white border-b border-gray-200 px-6 py-4">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <Link href="/" className="text-2xl font-bold text-secondary hover:text-primary transition-colors">
                        LEH
                    </Link>
                    <div className="flex items-center space-x-4">
                        <span className="text-sm text-neutral-600">
                            {user?.name ? `${user.name}님, 환영합니다.` : '환영합니다.'}
                        </span>
                        <button
                            onClick={logout}
                            className="flex items-center gap-1 text-sm text-gray-500 hover:text-error transition-colors"
                        >
                            <LogOut className="w-4 h-4" />
                            로그아웃
                        </button>
                    </div>
                </div>
            </nav>

            <main className="max-w-7xl mx-auto px-6 py-8">
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h2 className="text-3xl font-bold text-gray-900">나의 사건</h2>
                        <p className="mt-1 text-gray-500">진행 중인 사건을 한눈에 확인하고 관리하세요.</p>
                    </div>
                    <button
                        onClick={() => setIsModalOpen(true)}
                        className="flex items-center px-4 py-2 bg-blue-500 text-white font-medium rounded-lg shadow-lg hover:bg-blue-600 hover:shadow-xl transform hover:-translate-y-0.5 transition-all"
                    >
                        <Plus className="w-5 h-5 mr-2" />
                        새 사건 등록
                    </button>
                </div>

                {/* Case Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {cases.map((caseItem) => (
                        <CaseCard key={caseItem.id} caseData={caseItem} onDelete={fetchCases} />
                    ))}
                </div>

                {/* Error State */}
                {error && errorType && (
                    <div className="text-center py-10 bg-red-50 rounded-lg border border-red-200">
                        <p className="text-red-600 text-lg font-medium mb-4">{error}</p>
                        <button
                            onClick={fetchCases}
                            className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                        >
                            <RefreshCw className="w-4 h-4 mr-2" />
                            다시 시도
                        </button>
                    </div>
                )}

                {/* Empty State with Example Cases */}
                {!error && cases.length === 0 && (
                    <div className="space-y-8">
                        {/* Empty state message */}
                        <div className="text-center py-10 bg-gray-50 rounded-lg border border-gray-200">
                            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                            <p className="text-gray-600 text-lg font-medium">등록된 사건이 없습니다.</p>
                            <p className="text-gray-400 mt-2">새 사건 등록 버튼을 눌러 첫 사건을 추가해보세요.</p>
                        </div>

                        {/* Example Cases Section */}
                        <div className="border-t border-gray-200 pt-8">
                            <div className="flex items-center gap-2 mb-4">
                                <span className="text-sm font-medium text-gray-500">예시 사건</span>
                                <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">데모</span>
                            </div>
                            <p className="text-sm text-gray-400 mb-4">
                                아래는 LEH 플랫폼 사용 예시입니다. 실제 사건을 등록하면 이와 같이 표시됩니다.
                            </p>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 opacity-75">
                                {EXAMPLE_CASES.map((caseItem) => (
                                    <div key={caseItem.id} className="relative">
                                        <div className="absolute -top-2 -right-2 z-10">
                                            <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full">
                                                예시
                                            </span>
                                        </div>
                                        <CaseCard caseData={caseItem} />
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </main>

            {/* 모달 렌더링 */}
            <AddCaseModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSuccess={fetchCases}
            />
        </div>
    );
}
