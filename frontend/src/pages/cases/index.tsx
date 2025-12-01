import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { Plus, LogOut } from 'lucide-react';
import CaseCard from '@/components/cases/CaseCard';
import AddCaseModal from '@/components/cases/AddCaseModal';
import { Case } from '@/types/case';
import { useAuth } from '@/hooks/useAuth';
import { getCases, Case as ApiCase } from '@/lib/api/cases';

// Helper function to map API response to frontend Case type
function mapApiCaseToCase(apiCase: ApiCase): Case {
    return {
        id: apiCase.id,
        title: apiCase.title,
        clientName: apiCase.client_name,
        status: apiCase.status === 'active' ? 'open' : apiCase.status === 'closed' ? 'closed' : 'open',
        evidenceCount: apiCase.evidence_count,
        draftStatus: apiCase.draft_status === 'completed' ? 'ready' :
                     apiCase.draft_status === 'in_progress' ? 'generating' : 'not_started',
        lastUpdated: apiCase.updated_at,
    };
}

export default function CasesPage() {
    const router = useRouter();
    const { isAuthenticated, isLoading: isAuthLoading, logout } = useAuth();
    const [cases, setCases] = useState<Case[]>([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Redirect to login if not authenticated
    useEffect(() => {
        if (!isAuthLoading && !isAuthenticated) {
            router.replace('/login');
        }
    }, [isAuthLoading, isAuthenticated, router]);

    // Fetch cases from API
    useEffect(() => {
        async function fetchCases() {
            if (isAuthLoading || !isAuthenticated) return;

            setIsLoading(true);
            setError(null);

            try {
                const response = await getCases();
                if (response.error) {
                    setError(response.error);
                    setCases([]);
                } else if (response.data) {
                    const mappedCases = response.data.cases.map(mapApiCaseToCase);
                    setCases(mappedCases);
                }
            } catch (err) {
                setError('사건 목록을 불러오는데 실패했습니다.');
                setCases([]);
            } finally {
                setIsLoading(false);
            }
        }

        fetchCases();
    }, [isAuthLoading, isAuthenticated]);

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
            <Head>
                <title>사건 목록 | Legal Evidence Hub</title>
            </Head>

            {/* Header / Navigation (To be separated later) */}
            <nav className="bg-white border-b border-gray-200 px-6 py-4">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <h1 className="text-2xl font-bold text-secondary">LEH</h1>
                    <div className="flex items-center space-x-4">
                        <span className="text-sm text-neutral-600">변호사님, 환영합니다.</span>
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
                        className="btn-primary flex items-center shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all"
                    >
                        <Plus className="w-5 h-5 mr-2" />
                        새 사건 등록
                    </button>
                </div>

                {/* Case Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {cases.map((caseItem) => (
                        <CaseCard key={caseItem.id} caseData={caseItem} />
                    ))}
                </div>

                {/* Error State */}
                {error && (
                    <div className="text-center py-10">
                        <p className="text-red-500 text-lg">{error}</p>
                    </div>
                )}

                {/* Empty State */}
                {!error && cases.length === 0 && (
                    <div className="text-center py-20">
                        <p className="text-gray-500 text-lg">등록된 사건이 없습니다.</p>
                        <p className="text-gray-400 mt-2">새 사건 등록 버튼을 눌러 첫 사건을 추가해보세요.</p>
                    </div>
                )}
            </main>

            {/* 모달 렌더링 */}
            <AddCaseModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
        </div>
    );
}
