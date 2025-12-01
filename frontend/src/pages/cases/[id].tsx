import { useCallback, useMemo, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { ArrowLeft, CheckCircle2, Filter, Shield, Sparkles, Upload, Loader2 } from 'lucide-react';
import Link from 'next/link';
import EvidenceUpload from '@/components/evidence/EvidenceUpload';
import EvidenceTable from '@/components/evidence/EvidenceTable';
import { Evidence } from '@/types/evidence';
import DraftPreviewPanel from '@/components/draft/DraftPreviewPanel';
import DraftGenerationModal from '@/components/draft/DraftGenerationModal';
import { DraftCitation } from '@/types/draft';
import { downloadDraftAsDocx, DraftDownloadFormat } from '@/services/documentService';
import {
  getPresignedUploadUrl,
  uploadToS3,
  notifyUploadComplete,
  UploadProgress
} from '@/lib/api/evidence';

// Mock Data
const MOCK_EVIDENCE: Evidence[] = [
    {
        id: '1',
        caseId: '1',
        filename: '녹취록_20240501.mp3',
        type: 'audio',
        status: 'completed',
        uploadDate: '2024-05-01T10:00:00Z',
        summary: '피고의 폭언이 담긴 통화 녹음',
        size: 15 * 1024 * 1024,
    },
    {
        id: '2',
        caseId: '1',
        filename: '카카오톡_대화내역.txt',
        type: 'text',
        status: 'processing',
        uploadDate: '2024-05-02T09:30:00Z',
        size: 50 * 1024,
    },
    {
        id: '3',
        caseId: '1',
        filename: '폭행_상해_진단서.pdf',
        type: 'pdf',
        status: 'queued',
        uploadDate: '2024-05-03T14:20:00Z',
        size: 2 * 1024 * 1024,
    },
];

const INITIAL_DRAFT_CONTENT = `Ⅰ. 핵심 주장 요약
- 피고의 반복적인 언어적 폭력과 경제적 통제 사실이 다수의 증거에서 확인됩니다.
- 원고는 자녀 양육과 생활비 부담을 대부분 담당해왔습니다.

Ⅱ. 사실관계
1. 폭언 및 협박 (녹취록_20240501.mp3)
  - 피고의 '너를 사회적으로 매장하겠다'는 발언 기록
2. 자녀 돌봄 소홀 (카카오톡_대화내역.txt)
  - 자녀 학업 행사 불참을 인정하는 메시지

Ⅲ. 청구 취지
- 위자료 7천만 원
- 자녀 친권 및 양육권 원고 단독
`;

const INITIAL_CITATIONS: DraftCitation[] = [
    {
        evidenceId: '1',
        title: '녹취록_20240501.mp3',
        quote: '피고가 반복적으로 위협적인 발언을 한 사실이 확인됩니다.',
    },
    {
        evidenceId: '2',
        title: '카카오톡_대화내역.txt',
        quote: '자녀 돌봄을 회피한 메시지가 명시되어 있습니다.',
    },
];

const GENERATION_DELAY_MS = 1200;
type CaseDetailTab = 'evidence' | 'opponent' | 'timeline' | 'draft';
type UploadFeedback = { message: string; tone: 'info' | 'success' | 'error' };
type UploadStatus = {
  isUploading: boolean;
  currentFile: string;
  progress: number;
  completed: number;
  total: number;
};

export default function CaseDetailPage() {
    const router = useRouter();
    const { id } = router.query;
    const [evidenceList] = useState<Evidence[]>(MOCK_EVIDENCE);
    const [draftContent, setDraftContent] = useState(INITIAL_DRAFT_CONTENT);
    const [draftCitations, setDraftCitations] = useState<DraftCitation[]>(INITIAL_CITATIONS);
    const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);
    const [hasGeneratedDraft, setHasGeneratedDraft] = useState(true);
    const [isDraftModalOpen, setIsDraftModalOpen] = useState(false);
    const [activeTab, setActiveTab] = useState<CaseDetailTab>('draft');
    const [uploadFeedback, setUploadFeedback] = useState<UploadFeedback | null>(null);
    const [uploadStatus, setUploadStatus] = useState<UploadStatus>({
        isUploading: false,
        currentFile: '',
        progress: 0,
        completed: 0,
        total: 0,
    });

    const caseId = typeof id === 'string' ? id : '';

    const handleUpload = useCallback(async (files: File[]) => {
        if (files.length === 0 || !caseId) return;

        setUploadStatus({
            isUploading: true,
            currentFile: files[0].name,
            progress: 0,
            completed: 0,
            total: files.length,
        });

        let successCount = 0;
        let failCount = 0;

        for (let i = 0; i < files.length; i++) {
            const file = files[i];

            setUploadStatus(prev => ({
                ...prev,
                currentFile: file.name,
                progress: 0,
            }));

            try {
                // Step 1: Get presigned URL from backend
                const presignedResult = await getPresignedUploadUrl(
                    caseId,
                    file.name,
                    file.type || 'application/octet-stream'
                );

                if (presignedResult.error || !presignedResult.data) {
                    throw new Error(presignedResult.error || 'Failed to get presigned URL');
                }

                const { upload_url, evidence_temp_id, s3_key } = presignedResult.data;

                // Step 2: Upload file directly to S3
                const uploadSuccess = await uploadToS3(
                    upload_url,
                    file,
                    (progress: UploadProgress) => {
                        setUploadStatus(prev => ({
                            ...prev,
                            progress: progress.percent,
                        }));
                    }
                );

                if (!uploadSuccess) {
                    throw new Error('S3 upload failed');
                }

                // Step 3: Notify backend of completed upload
                const completeResult = await notifyUploadComplete({
                    case_id: caseId,
                    evidence_temp_id,
                    s3_key,
                });

                if (completeResult.error) {
                    throw new Error(completeResult.error || 'Failed to complete upload');
                }

                successCount++;
            } catch (error) {
                console.error(`Upload failed for ${file.name}:`, error);
                failCount++;
            }

            setUploadStatus(prev => ({
                ...prev,
                completed: i + 1,
            }));
        }

        // Upload complete - show feedback
        setUploadStatus(prev => ({ ...prev, isUploading: false }));

        if (failCount === 0) {
            setUploadFeedback({
                tone: 'success',
                message: `${successCount}개 파일 업로드 완료. AI가 증거를 분석 중입니다.`,
            });
        } else if (successCount > 0) {
            setUploadFeedback({
                tone: 'info',
                message: `${successCount}개 성공, ${failCount}개 실패. 실패한 파일을 다시 업로드해주세요.`,
            });
        } else {
            setUploadFeedback({
                tone: 'error',
                message: `업로드 실패. 네트워크를 확인하고 다시 시도해주세요.`,
            });
        }

        setTimeout(() => setUploadFeedback(null), 5000);
    }, [caseId]);

    const openDraftModal = () => {
        setIsDraftModalOpen(true);
    };

    const handleGenerateDraft = (selectedEvidenceIds: string[]) => {
        setIsDraftModalOpen(false);
        if (isGeneratingDraft) return;

        setIsGeneratingDraft(true);
        setTimeout(() => {
            setDraftContent((prev) =>
                prev.includes('업데이트')
                    ? INITIAL_DRAFT_CONTENT
                    : `${prev}\n\n※ ${new Date().toLocaleString('ko-KR')} 업데이트: 선택된 ${selectedEvidenceIds.length}건의 증거를 기반으로 핵심 주장이 재정리되었습니다.`,
            );
            setDraftCitations((prev) =>
                prev.length > 2
                    ? INITIAL_CITATIONS
                    : [
                        ...prev,
                        {
                            evidenceId: '3',
                            title: '폭행_상해_진단서.pdf',
                            quote: '의료 기록상 상해 사실이 확인됩니다.',
                        },
                    ],
            );
            setHasGeneratedDraft(true);
            setIsGeneratingDraft(false);
        }, GENERATION_DELAY_MS);
    };

    const handleDownload = async (format: DraftDownloadFormat = 'docx') => {
        if (!id || typeof id !== 'string') return;
        await downloadDraftAsDocx(draftContent, id, format);
    };

    const tabItems: { id: CaseDetailTab; label: string; description: string }[] = useMemo(
        () => [
            { id: 'evidence', label: '증거', description: '업로드 · 상태 · 요약' },
            { id: 'opponent', label: '상대방 주장', description: '주장 정리 & AI 추천' },
            { id: 'timeline', label: '타임라인', description: '사건 맥락 · 흐름' },
            { id: 'draft', label: 'Draft', description: 'AI 초안 검토/다운로드' },
        ],
        [],
    );

    return (
        <div className="min-h-screen bg-neutral-50">
            <Head>
                <title>사건 상세 | Legal Evidence Hub</title>
            </Head>

            {/* Header */}
            <header className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center">
                        <Link href="/cases" className="mr-4 text-gray-500 hover:text-gray-800 transition-colors">
                            <ArrowLeft className="w-6 h-6" />
                        </Link>
                        <div>
                            <h1 className="text-xl font-bold text-secondary">김철수 이혼 소송</h1>
                            <p className="text-xs text-gray-500">Case ID: {id}</p>
                        </div>
                    </div>
                    <div className="flex space-x-3">
                        <button
                            onClick={openDraftModal}
                            className="btn-primary bg-deep-trust-blue hover:bg-slate-700"
                        >
                            Draft 작성
                        </button>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
                <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 grid gap-4 md:grid-cols-3">
                    <div>
                        <p className="text-xs uppercase tracking-widest text-gray-400 mb-1">의뢰인</p>
                        <p className="text-base font-semibold text-gray-900">김철수</p>
                        <p className="text-xs text-gray-500">최근 업데이트: {new Date().toLocaleDateString('ko-KR')}</p>
                    </div>
                    <div>
                        <p className="text-xs uppercase tracking-widest text-gray-400 mb-1">증거 현황</p>
                        <p className="text-base font-semibold text-gray-900">{evidenceList.length}건 처리 중</p>
                        <p className="text-xs text-gray-500">AI 분석 상태는 실시간으로 반영됩니다.</p>
                    </div>
                    <div className="flex items-center space-x-2 bg-neutral-50 rounded-xl px-4 py-3">
                        <Shield className="w-5 h-5 text-secondary" />
                        <div>
                            <p className="text-sm font-semibold text-gray-800">모든 데이터는 암호화되어 저장됩니다.</p>
                            <p className="text-xs text-gray-500">Calm Control · Sage & Caregiver</p>
                        </div>
                    </div>
                </section>

                <nav role="tablist" aria-label="Case detail tabs" className="flex flex-wrap gap-3 bg-white rounded-2xl border border-gray-100 p-3 shadow-sm">
                    {tabItems.map((tab) => {
                        const isActive = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                role="tab"
                                aria-selected={isActive}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex flex-col rounded-xl border px-4 py-3 text-left transition-all ${
                                    isActive ? 'border-accent bg-accent/10 text-secondary shadow-sm' : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300'
                                }`}
                            >
                                <span className="text-sm font-semibold">{tab.label}</span>
                                <span className="text-xs text-gray-500">{tab.description}</span>
                            </button>
                        );
                    })}
                </nav>

                {activeTab === 'evidence' && (
                    <div className="space-y-6" role="tabpanel" aria-label="증거 탭">
                        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h2 className="text-lg font-bold text-gray-900">증거 업로드</h2>
                                    <p className="text-sm text-gray-500">파일을 드래그하거나 클릭하여 업로드할 수 있습니다.</p>
                                </div>
                                <span className="text-xs text-gray-500 flex items-center">
                                    <Sparkles className="w-4 h-4 text-accent mr-1" /> Whisper · OCR 자동 적용
                                </span>
                            </div>
                            <EvidenceUpload onUpload={handleUpload} disabled={uploadStatus.isUploading} />
                            {uploadStatus.isUploading && (
                                <div
                                    role="status"
                                    aria-live="polite"
                                    className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 text-sm"
                                >
                                    <div className="flex items-center space-x-2 mb-2">
                                        <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                                        <span className="text-blue-800 font-medium">
                                            업로드 중 ({uploadStatus.completed + 1}/{uploadStatus.total})
                                        </span>
                                    </div>
                                    <p className="text-blue-700 text-xs mb-2 truncate">{uploadStatus.currentFile}</p>
                                    <div className="w-full bg-blue-200 rounded-full h-2">
                                        <div
                                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                            style={{ width: `${uploadStatus.progress}%` }}
                                        />
                                    </div>
                                </div>
                            )}
                            {uploadFeedback && !uploadStatus.isUploading && (
                                <div
                                    role="status"
                                    aria-live="polite"
                                    className={`flex items-start space-x-2 rounded-lg px-4 py-3 text-sm ${
                                        uploadFeedback.tone === 'success'
                                            ? 'bg-accent/10 text-secondary'
                                            : uploadFeedback.tone === 'error'
                                            ? 'bg-red-50 text-red-700 border border-red-200'
                                            : 'bg-gray-100 text-neutral-700'
                                    }`}
                                >
                                    <CheckCircle2 className={`w-4 h-4 mt-0.5 ${
                                        uploadFeedback.tone === 'error' ? 'text-red-500' : 'text-accent'
                                    }`} />
                                    <p>{uploadFeedback.message}</p>
                                </div>
                            )}
                        </section>

                        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4">
                            <div className="flex justify-between items-center">
                                <div>
                                    <h2 className="text-lg font-bold text-gray-900">
                                        증거 목록 <span className="text-gray-500 text-sm font-normal">({evidenceList.length})</span>
                                    </h2>
                                    <p className="text-xs text-gray-500">상태 컬럼을 통해 AI 분석 파이프라인의 진행 상황을 확인하세요.</p>
                                </div>
                                <button className="flex items-center text-sm text-neutral-600 hover:text-gray-900 bg-white border border-gray-300 px-3 py-1.5 rounded-md shadow-sm">
                                    <Filter className="w-4 h-4 mr-2" />
                                    뷰 필터
                                </button>
                            </div>
                            <EvidenceTable items={evidenceList} />
                        </section>
                    </div>
                )}

                {activeTab === 'opponent' && (
                    <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4" role="tabpanel" aria-label="상대방 주장 탭">
                        <h2 className="text-lg font-bold text-gray-900">상대방 주장 & AI 추천 증거</h2>
                        <p className="text-sm text-gray-500">
                            상대방의 주장을 기록하고, RAG 기반으로 자동 추천되는 증거를 매칭할 수 있도록 준비 중입니다. 지금은 사건 노트에 주요 쟁점을 메모해 두세요.
                        </p>
                        <div className="bg-neutral-50 rounded-xl p-4 text-sm text-neutral-600">⚙️ 곧 제공될 기능: 주장 카드 추가, AI 추천 증거 목록, 신뢰도 퍼센티지 뱃지</div>
                    </section>
                )}

                {activeTab === 'timeline' && (
                    <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-4" role="tabpanel" aria-label="타임라인 탭">
                        <h2 className="text-lg font-bold text-gray-900">사건 타임라인</h2>
                        <p className="text-sm text-gray-500">AI가 추출한 주요 사건들을 시간순으로 정리합니다. 증거 탭에서 “AI 요약”이 쌓일수록 타임라인의 정확도가 향상됩니다.</p>
                        <ul className="space-y-3">
                            {evidenceList.map((item) => (
                                <li key={item.id} className="flex items-start space-x-3 border-l-2 border-accent pl-3">
                                    <div className="text-xs text-gray-400">{new Date(item.uploadDate).toLocaleDateString()}</div>
                                    <div>
                                        <p className="text-sm font-semibold text-gray-800">{item.filename}</p>
                                        <p className="text-xs text-gray-500">{item.summary ? item.summary : '요약이 곧 제공됩니다. 증거를 검토 중입니다.'}</p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    </section>
                )}

                {activeTab === 'draft' && (
                    <section className="space-y-4" role="tabpanel" aria-label="Draft 탭">
                        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-3">
                            <div className="flex items-start space-x-3">
                                <CheckCircle2 className="w-5 h-5 text-accent mt-0.5" />
                                <div>
                                    <p className="text-sm font-semibold text-gray-900">이 문서는 AI가 생성한 초안이며, 최종 법적 책임은 검토한 변호사에게 있습니다.</p>
                                    <p className="text-xs text-gray-500">중요한 문장은 증거 탭에서 원본을 다시 확인하고, 필요한 경우 직접 수정하세요.</p>
                                </div>
                            </div>
                        </div>
                        <DraftPreviewPanel
                            draftText={draftContent}
                            citations={draftCitations}
                            isGenerating={isGeneratingDraft}
                            hasExistingDraft={hasGeneratedDraft}
                            onGenerate={openDraftModal}
                            onDownload={handleDownload}
                        />
                    </section>
                )}
            </main>

            <DraftGenerationModal
                isOpen={isDraftModalOpen}
                onClose={() => setIsDraftModalOpen(false)}
                onGenerate={handleGenerateDraft}
                evidenceList={evidenceList}
            />
        </div>
    );
}
