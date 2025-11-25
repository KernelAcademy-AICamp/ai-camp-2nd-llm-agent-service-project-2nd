import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { Plus } from 'lucide-react';
import CaseCard from '@/components/cases/CaseCard';
import AddCaseModal from '@/components/cases/AddCaseModal'; // 모달 컴포넌트 임포트
import { Case } from '@/types/case';

// Mock Data for MVP
const MOCK_CASES: Case[] = [
    {
        id: '1',
        title: '김철수 이혼 소송',
        clientName: '김철수',
        status: 'open',
        evidenceCount: 128,
        draftStatus: 'ready',
        lastUpdated: '2024-05-20T09:00:00Z',
    },
    {
        id: '2',
        title: '이영희 재산분할 청구',
        clientName: '이영희',
        status: 'open',
        evidenceCount: 45,
        draftStatus: 'generating',
        lastUpdated: '2024-05-19T15:30:00Z',
    },
    {
        id: '3',
        title: '박민수 양육권 분쟁',
        clientName: '박민수',
        status: 'closed',
        evidenceCount: 12,
        draftStatus: 'not_started',
        lastUpdated: '2024-04-10T11:20:00Z',
    },
];

export default function CasesPage() {
    const router = useRouter();
    const [cases] = useState<Case[]>(MOCK_CASES);
    const [isModalOpen, setIsModalOpen] = useState(false); // 모달 상태 추가
    const [isAuthChecking, setIsAuthChecking] = useState(true);

    // Navigation Guard: Check if user is authenticated
    useEffect(() => {
        const token = localStorage.getItem('authToken');
        if (!token) {
            router.replace('/login');
        } else {
            setIsAuthChecking(false);
        }
    }, [router]);

    // Show nothing while checking auth to prevent content flash
    if (isAuthChecking) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-calm-grey">
                <div className="text-gray-500">로딩 중...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-calm-grey">
            <Head>
                <title>사건 목록 | Legal Evidence Hub</title>
            </Head>

            {/* Header / Navigation (To be separated later) */}
            <nav className="bg-white border-b border-gray-200 px-6 py-4">
                <div className="max-w-7xl mx-auto flex justify-between items-center">
                    <h1 className="text-2xl font-bold text-deep-trust-blue">LEH</h1>
                    <div className="flex items-center space-x-4">
                        <span className="text-sm text-gray-600">변호사님, 환영합니다.</span>
                        <button className="text-sm text-gray-500 hover:text-gray-800">로그아웃</button>
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
                        onClick={() => setIsModalOpen(true)} // onClick 핸들러 추가
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

                {/* Empty State (Hidden for now as we have mock data) */}
                {cases.length === 0 && (
                    <div className="text-center py-20">
                        <p className="text-gray-500 text-lg">등록된 사건이 없습니다.</p>
                    </div>
                )}
            </main>

            {/* 모달 렌더링 */}
            <AddCaseModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
        </div>
    );
}
