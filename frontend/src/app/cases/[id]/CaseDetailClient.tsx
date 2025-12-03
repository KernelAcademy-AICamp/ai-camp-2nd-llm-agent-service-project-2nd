'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { ArrowLeft, CheckCircle2, Filter, Shield, Sparkles, Loader2, AlertCircle, RefreshCw } from 'lucide-react';
import Link from 'next/link';
import EvidenceUpload from '@/components/evidence/EvidenceUpload';
import EvidenceTable from '@/components/evidence/EvidenceTable';
import { Evidence, EvidenceType, EvidenceStatus } from '@/types/evidence';
import DraftPreviewPanel from '@/components/draft/DraftPreviewPanel';
import DraftGenerationModal from '@/components/draft/DraftGenerationModal';
import { DraftCitation } from '@/types/draft';
import { downloadDraftAsDocx, DraftDownloadFormat } from '@/services/documentService';
import {
  getPresignedUploadUrl,
  uploadToS3,
  notifyUploadComplete,
  getEvidence,
  UploadProgress
} from '@/lib/api/evidence';
import { getCase, Case } from '@/lib/api/cases';
import { generateDraftPreview, DraftCitation as ApiDraftCitation } from '@/lib/api/draft';
import { mapApiEvidenceListToEvidence } from '@/lib/utils/evidenceMapper';

/**
 * Convert API draft citation to component DraftCitation type
 */
function mapApiCitationToCitation(apiCitation: ApiDraftCitation, evidenceList: Evidence[]): DraftCitation {
  // Try to find evidence by ID to get the filename as title
  const evidence = evidenceList.find(e => e.id === apiCitation.evidence_id);
  return {
    evidenceId: apiCitation.evidence_id,
    title: evidence?.filename || `증거 ${apiCitation.evidence_id}`,
    quote: apiCitation.snippet,
  };
}
type CaseDetailTab = 'evidence' | 'opponent' | 'timeline' | 'draft';
type UploadFeedback = { message: string; tone: 'info' | 'success' | 'error' };
type UploadStatus = {
  isUploading: boolean;
  currentFile: string;
  progress: number;
  completed: number;
  total: number;
};

interface CaseDetailClientProps {
  id: string;
}

export default function CaseDetailClient({ id }: CaseDetailClientProps) {
    const [caseData, setCaseData] = useState<Case | null>(null);
    const [isLoadingCase, setIsLoadingCase] = useState(true);
    const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
    const [isLoadingEvidence, setIsLoadingEvidence] = useState(true);
    const [evidenceError, setEvidenceError] = useState<string | null>(null);
    const [draftContent, setDraftContent] = useState('');
    const [draftCitations, setDraftCitations] = useState<DraftCitation[]>([]);
    const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);
    const [hasGeneratedDraft, setHasGeneratedDraft] = useState(false);
    const [draftError, setDraftError] = useState<string | null>(null);
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

    const caseId = id || '';

    // Fetch evidence list from API
    const fetchEvidence = useCallback(async () => {
        if (!caseId) return;

        setIsLoadingEvidence(true);
        setEvidenceError(null);

        try {
            const response = await getEvidence(caseId);
            if (response.error) {
                setEvidenceError(response.error);
                setEvidenceList([]);
            } else if (response.data) {
                const mappedEvidence = mapApiEvidenceListToEvidence(response.data.evidence);
                setEvidenceList(mappedEvidence);
            }
        } catch (err) {
            console.error('Failed to fetch evidence:', err);
            setEvidenceError('증거 목록을 불러오는데 실패했습니다.');
            setEvidenceList([]);
        } finally {
            setIsLoadingEvidence(false);
        }
    }, [caseId]);

    // Load evidence on mount
    useEffect(() => {
        fetchEvidence();
    }, [fetchEvidence]);

    // Fetch case data
    useEffect(() => {
        if (!caseId) return;

        const fetchCaseData = async () => {
            setIsLoadingCase(true);
            const response = await getCase(caseId);
            if (response.data) {
                setCaseData(response.data);
            }
            setIsLoadingCase(false);
        };

        fetchCaseData();
    }, [caseId]);

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
                const presignedResult = await getPresignedUploadUrl(
                    caseId,
                    file.name,
                    file.type || 'application/octet-stream'
                );

                if (presignedResult.error || !presignedResult.data) {
                    throw new Error(presignedResult.error || 'Failed to get presigned URL');
                }

                const { upload_url, evidence_temp_id, s3_key } = presignedResult.data;

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

                const completeResult = await notifyUploadComplete({
                    case_id: caseId,
                    evidence_temp_id,
                    s3_key,
                    file_size: file.size,
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

        setUploadStatus(prev => ({ ...prev, isUploading: false }));

        if (failCount === 0) {
            setUploadFeedback({
                tone: 'success',
                message: `${successCount}개 파일 업로드 완료. AI가 증거를 분석 중입니다.`,
            });
            // Refresh evidence list after successful upload
            fetchEvidence();
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

        // Refresh evidence list after upload
        if (successCount > 0) {
            fetchEvidence();
        }

        setTimeout(() => setUploadFeedback(null), 5000);
    }, [caseId, fetchEvidence]);

    const openDraftModal = () => {
        setIsDraftModalOpen(true);
    };

    const handleGenerateDraft = useCallback(async (selectedEvidenceIds: string[]) => {
        setIsDraftModalOpen(false);
        if (isGeneratingDraft || !caseId) return;

        setIsGeneratingDraft(true);
        setDraftError(null);

        try {
            const response = await generateDraftPreview(caseId, {
                sections: ['청구취지', '청구원인'],
            });

            if (response.error) {
                setDraftError(response.error);
            } else if (response.data) {
                setDraftContent(response.data.draft_text);
                // Convert API citations to component format
                const mappedCitations = response.data.citations.map(c =>
                    mapApiCitationToCitation(c, evidenceList)
                );
                setDraftCitations(mappedCitations);
                setHasGeneratedDraft(true);
            }
        } catch (err) {
            console.error('Failed to generate draft:', err);
            setDraftError('초안 생성에 실패했습니다. 다시 시도해주세요.');
        } finally {
            setIsGeneratingDraft(false);
        }
    }, [caseId, isGeneratingDraft, evidenceList]);

    const handleDownload = async (content: string, format: DraftDownloadFormat = 'docx') => {
        if (!id) return;
        await downloadDraftAsDocx(content, id, format);
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
            <header className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10">
                <div className="max-w-7xl mx-auto flex items-center justify-between">
                    <div className="flex items-center">
                        <Link href="/cases" className="mr-4 text-gray-500 hover:text-gray-800 transition-colors">
                            <ArrowLeft className="w-6 h-6" />
                        </Link>
                        <div>
                            <h1 className="text-xl font-bold text-secondary">
                                {isLoadingCase ? '로딩 중...' : caseData?.title || '사건 정보 없음'}
                            </h1>
                            <p className="text-xs text-gray-500">Case ID: {id}</p>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
                <section className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 grid gap-4 md:grid-cols-3">
                    <div>
                        <p className="text-xs uppercase tracking-widest text-gray-400 mb-1">의뢰인</p>
                        <p className="text-base font-semibold text-gray-900">
                            {isLoadingCase ? '로딩 중...' : caseData?.client_name || '-'}
                        </p>
                        <p className="text-xs text-gray-500">
                            최근 업데이트: {caseData?.updated_at
                                ? new Date(caseData.updated_at).toLocaleDateString('ko-KR')
                                : new Date().toLocaleDateString('ko-KR')}
                        </p>
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
                                <div className="flex items-center space-x-2">
                                    <button
                                        onClick={fetchEvidence}
                                        disabled={isLoadingEvidence}
                                        className="flex items-center text-sm text-neutral-600 hover:text-gray-900 bg-white border border-gray-300 px-3 py-1.5 rounded-md shadow-sm disabled:opacity-50"
                                    >
                                        <RefreshCw className={`w-4 h-4 mr-2 ${isLoadingEvidence ? 'animate-spin' : ''}`} />
                                        새로고침
                                    </button>
                                    <button className="flex items-center text-sm text-neutral-600 hover:text-gray-900 bg-white border border-gray-300 px-3 py-1.5 rounded-md shadow-sm">
                                        <Filter className="w-4 h-4 mr-2" />
                                        뷰 필터
                                    </button>
                                </div>
                            </div>
                            {isLoadingEvidence && (
                                <div className="flex items-center justify-center py-8">
                                    <Loader2 className="w-6 h-6 text-accent animate-spin" />
                                    <span className="ml-2 text-gray-500">증거 목록을 불러오는 중...</span>
                                </div>
                            )}
                            {evidenceError && !isLoadingEvidence && (
                                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
                                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
                                    <div>
                                        <p className="text-sm font-medium text-red-700">{evidenceError}</p>
                                        <button
                                            onClick={fetchEvidence}
                                            className="text-sm text-red-600 hover:text-red-800 underline mt-1"
                                        >
                                            다시 시도
                                        </button>
                                    </div>
                                </div>
                            )}
                            {!isLoadingEvidence && !evidenceError && evidenceList.length === 0 && (
                                <div className="text-center py-8">
                                    <p className="text-gray-500">등록된 증거가 없습니다.</p>
                                    <p className="text-sm text-gray-400 mt-1">위 영역에 파일을 업로드하여 증거를 추가하세요.</p>
                                </div>
                            )}
                            {!isLoadingEvidence && !evidenceError && evidenceList.length > 0 && (
                                <EvidenceTable items={evidenceList} />
                            )}
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
                        <p className="text-sm text-gray-500">AI가 추출한 주요 사건들을 시간순으로 정리합니다. 증거 탭에서 "AI 요약"이 쌓일수록 타임라인의 정확도가 향상됩니다.</p>
                        {isLoadingEvidence ? (
                            <div className="flex items-center justify-center py-8">
                                <Loader2 className="w-6 h-6 text-accent animate-spin" />
                                <span className="ml-2 text-gray-500">타임라인을 불러오는 중...</span>
                            </div>
                        ) : evidenceList.length === 0 ? (
                            <div className="text-center py-8 text-gray-500">
                                <p>아직 등록된 증거가 없어 타임라인을 표시할 수 없습니다.</p>
                            </div>
                        ) : (
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
                        )}
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
                        {draftError && (
                            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
                                <p>{draftError}</p>
                            </div>
                        )}
                        <DraftPreviewPanel
                            caseId={caseId}
                            draftText={draftContent}
                            citations={draftCitations}
                            isGenerating={isGeneratingDraft}
                            hasExistingDraft={hasGeneratedDraft}
                            onGenerate={openDraftModal}
                            onDownload={({ content, format }) => handleDownload(content, format)}
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
