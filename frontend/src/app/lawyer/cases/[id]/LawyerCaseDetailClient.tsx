'use client';

/**
 * Lawyer Case Detail Client Component
 * 003-role-based-ui Feature - US3
 *
 * Client-side component for case detail view with evidence list and AI summary.
 *
 * Phase C.1: Refactored to use shared hooks and components from Phase A and B.
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Loader2, RefreshCw, Sparkles, CheckCircle2, FileText, Scale, Filter, Wallet, MessageSquare, FileUp, Edit3, UserPlus, Calendar, Bell, Activity, ClipboardList } from 'lucide-react';
import { apiClient } from '@/lib/api/client';
import ExplainerCard from '@/components/cases/ExplainerCard';
import ShareSummaryModal from '@/components/cases/ShareSummaryModal';
import EditCaseModal from '@/components/cases/EditCaseModal';
import { ApiCase } from '@/lib/api/cases';
import { getCaseDetailPath, getLawyerCasePath } from '@/lib/portalPaths';
import { PartyGraph } from '@/components/party/PartyGraph';
// Phase A: Shared Hooks
import { useCaseIdValidation, useEvidenceUpload } from '@/hooks';
// New components for refactored UI
import { AnalysisTab } from '@/components/case/AnalysisTab';
// Evidence imports
import EvidenceUpload from '@/components/evidence/EvidenceUpload';
import EvidenceUploadModal from '@/components/evidence/EvidenceUploadModal';
import EvidenceTable from '@/components/evidence/EvidenceTable';
import { Evidence, EvidenceType, EvidenceStatus } from '@/types/evidence';
import { getEvidence } from '@/lib/api/evidence';
import { mapApiEvidenceToEvidence, mapApiEvidenceListToEvidence } from '@/lib/utils/evidenceMapper';
import { EvidenceEmptyState } from '@/components/evidence/EvidenceEmptyState';
import { ErrorState } from '@/components/shared/EmptyState';
import { logger } from '@/lib/logger';
// Phase A.1: Status Config
import { getCaseStatusConfig } from '@/lib/utils/statusConfig';
// Draft imports
import DraftGenerationModal from '@/components/draft/DraftGenerationModal';
import DraftPreviewPanel from '@/components/draft/DraftPreviewPanel';
import { generateDraftPreviewAsync, DraftJobStatus } from '@/lib/api/draft';
import { DraftCitation } from '@/types/draft';
import { downloadDraftAsDocx, DraftDownloadFormat, DownloadResult } from '@/services/documentService';
import { ExpertInsightsPanel } from '@/components/case/ExpertInsightsPanel';
import { useProcedure } from '@/hooks/useProcedure';
import { ProcedureTimeline } from '@/components/procedure';
// New tab components
import { AssetSummaryTab } from '@/components/case/AssetSummaryTab';
import { ConsultationHistoryTab } from '@/components/case/ConsultationHistoryTab';
// Independent modals for consultation and asset
import { ConsultationModal } from '@/components/consultation/ConsultationModal';
import { AssetModal } from '@/components/asset/AssetModal';
// 014-case-fact-summary: FactSummaryPanel
import { FactSummaryPanel } from '@/components/fact-summary/FactSummaryPanel';
// 014-ui-settings-completion: New 3-column layout components
import { CaseWorkspace } from '@/components/case/CaseWorkspace';
import { CaseDataPanel } from '@/components/case/DataPanel';
import { MainWorkspace } from '@/components/case/MainWorkspace';
import { ContextPanel } from '@/components/case/ContextPanel';
import { FactSummaryEditor } from '@/components/legal-analysis/FactSummaryEditor';
import { EvidenceListCompact, type LegalEvidence } from '@/components/case/EvidenceListCompact';
// LDS2: UtilityBar for top navigation
import { UtilityBar, CaseStatus } from '@/components/shared/UtilityBar';
// 016-draft-fact-summary: fact-summary 조회
import { getFactSummary, generateFactSummary } from '@/lib/api/fact-summary';
// Issue #423: Pipeline progress visualization - moved to separate component
// DataPanel compact lists for consultation and assets
import { ConsultationListCompact } from '@/components/consultation/ConsultationListCompact';
import { AssetListCompact } from '@/components/asset/AssetListCompact';
import { SimilarPrecedentList } from '@/components/precedent/SimilarPrecedentList';
import { getConsultations } from '@/lib/api/consultation';
import { getAssets } from '@/lib/api/assets';
import type { Consultation } from '@/types/consultation';
import type { LegacyAsset as Asset } from '@/types/asset';

interface CaseDetail {
  id: string;
  title: string;
  clientName?: string;
  description?: string;
  status: string;
  createdAt: string;
  updatedAt: string;
  ownerId: string;
  ownerName?: string;
  ownerEmail?: string;
  evidenceCount: number;
  evidenceSummary: { type: string; count: number }[];
  aiSummary?: string;
  aiLabels: string[];
  recentActivities: { action: string; timestamp: string; user: string }[];
  members: { userId: string; userName?: string; role: string }[];
}

// Phase A.1: Status colors/labels now imported from @/lib/utils/statusConfig

interface CaseDetailResponse {
  id: string;
  title: string;
  client_name?: string;
  description?: string;
  status: string;
  created_at: string;
  updated_at: string;
  owner_id: string;
  owner_name?: string;
  owner_email?: string;
  evidence_count?: number;
  evidence_summary?: { type: string; count: number }[];
  ai_summary?: string;
  ai_labels?: string[];
  recent_activities?: { action: string; timestamp: string; user: string }[];
  // API returns snake_case, we transform to camelCase
  members?: { user_id: string; user_name?: string; role: string }[];
}

interface LawyerCaseDetailClientProps {
  id: string;
}

// Phase A.3: Upload types now imported from useEvidenceUpload hook

export default function LawyerCaseDetailClient({ id: paramId }: LawyerCaseDetailClientProps) {
  const router = useRouter();

  // Phase A.2: Use useCaseIdValidation hook for ID handling with timeout
  const { caseId, isIdMissing, idWaitTimedOut } = useCaseIdValidation(paramId);

  // Derived paths (prefixed with _ as currently unused, may be needed for navigation)
  const _detailPath = caseId ? getCaseDetailPath('lawyer', caseId) : '/lawyer/cases/detail';
  const _assetsPath = caseId ? getLawyerCasePath('assets', caseId) : '/lawyer/cases/assets';
  const [caseDetail, setCaseDetail] = useState<CaseDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // 014-ui-settings-completion: Tabs reduced to 4 with workspace as default
  const [activeTab, setActiveTab] = useState<'workspace' | 'evidence' | 'timeline' | 'consultation' | 'analysis' | 'relations' | 'assets' | 'draft' | 'caseSummary'>('workspace');
  const [showSummaryCard, setShowSummaryCard] = useState(false);
  // 014-ui-settings-completion: Fact summary editor state
  const [factSummaryContent, setFactSummaryContent] = useState('');
  const [showShareModal, setShowShareModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showExpertPanel, setShowExpertPanel] = useState(false);
  const [showEvidenceUploadModal, setShowEvidenceUploadModal] = useState(false);
  const [showConsultationAddModal, setShowConsultationAddModal] = useState(false);
  const [showAssetAddModal, setShowAssetAddModal] = useState(false);

  // Draft state
  const [showDraftModal, setShowDraftModal] = useState(false);
  const [draftText, setDraftText] = useState('');
  const [draftCitations, setDraftCitations] = useState<DraftCitation[]>([]);
  const [isGeneratingDraft, setIsGeneratingDraft] = useState(false);
  const [draftError, setDraftError] = useState<string | null>(null);
  const [hasExistingDraft, setHasExistingDraft] = useState(false);
  const [draftProgress, setDraftProgress] = useState(0);
  const [draftStatus, setDraftStatus] = useState<DraftJobStatus | null>(null);
  // 016-draft-fact-summary: fact-summary 존재 여부 및 생성 상태
  const [hasFactSummary, setHasFactSummary] = useState(false);
  const [isGeneratingFactSummary, setIsGeneratingFactSummary] = useState(false);

  // Evidence state
  const [evidenceList, setEvidenceList] = useState<Evidence[]>([]);
  const [isLoadingEvidence, setIsLoadingEvidence] = useState(true);
  const [evidenceError, setEvidenceError] = useState<string | null>(null);

  // Consultation state (for DataPanel)
  const [consultationList, setConsultationList] = useState<Consultation[]>([]);
  const [, setIsLoadingConsultations] = useState(true);

  // Asset state (for DataPanel)
  const [assetList, setAssetList] = useState<Asset[]>([]);
  const [, setIsLoadingAssets] = useState(true);

  // 증거 필터 상태
  const [showFilterDropdown, setShowFilterDropdown] = useState(false);
  const [filterType, setFilterType] = useState<EvidenceType | 'all'>('all');
  const [filterStatus, setFilterStatus] = useState<EvidenceStatus | 'all'>('all');

  // 필터링된 증거 목록
  const filteredEvidenceList = useMemo(() => {
    return evidenceList.filter(item => {
      const typeMatch = filterType === 'all' || item.type === filterType;
      const statusMatch = filterStatus === 'all' || item.status === filterStatus;
      return typeMatch && statusMatch;
    });
  }, [evidenceList, filterType, filterStatus]);

  // Phase A.2: ID validation is now handled by useCaseIdValidation hook

  // Fetch case data with race condition prevention
  useEffect(() => {
    // ID가 없으면 fetch 건너뛰기
    if (!caseId) {
      setIsLoading(false);
      return;
    }

    // 이전 요청 무시 플래그
    let isCancelled = false;

    const fetchCaseDetail = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await apiClient.get<CaseDetailResponse>(`/lawyer/cases/${caseId}`);

        // caseId가 변경되어 이 요청이 무효화된 경우 무시
        if (isCancelled) return;

        if (response.error || !response.data) {
          throw new Error(response.error || '케이스 정보를 불러오는데 실패했습니다.');
        }

        const data = response.data;
        // Transform members from snake_case to camelCase
        const transformedMembers = (data.members || []).map((m) => ({
          userId: m.user_id,
          userName: m.user_name,
          role: m.role,
        }));
        setCaseDetail({
          id: data.id,
          title: data.title,
          clientName: data.client_name,
          description: data.description,
          status: data.status,
          createdAt: data.created_at,
          updatedAt: data.updated_at,
          ownerId: data.owner_id,
          ownerName: data.owner_name,
          ownerEmail: data.owner_email,
          evidenceCount: data.evidence_count || 0,
          evidenceSummary: data.evidence_summary || [],
          aiSummary: data.ai_summary,
          aiLabels: data.ai_labels || [],
          recentActivities: data.recent_activities || [],
          members: transformedMembers,
        });
      } catch (err) {
        if (isCancelled) return;
        setError(err instanceof Error ? err.message : '오류가 발생했습니다.');
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchCaseDetail();

    // cleanup: caseId 변경 또는 언마운트 시 이전 요청 무시
    return () => {
      isCancelled = true;
    };
  }, [caseId, router]);

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
      logger.error('Failed to fetch evidence:', err);
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

  // Fetch consultations for DataPanel
  const fetchConsultations = useCallback(async () => {
    if (!caseId) return;
    setIsLoadingConsultations(true);
    try {
      const response = await getConsultations(caseId);
      if (response.data) {
        setConsultationList(response.data.consultations);
      }
    } catch {
      // Silently handle errors for sidebar data
    } finally {
      setIsLoadingConsultations(false);
    }
  }, [caseId]);

  // Fetch assets for DataPanel
  const fetchAssets = useCallback(async () => {
    if (!caseId) return;
    setIsLoadingAssets(true);
    try {
      const assets = await getAssets(caseId);
      setAssetList(assets);
    } catch {
      // Silently handle errors for sidebar data
    } finally {
      setIsLoadingAssets(false);
    }
  }, [caseId]);

  // Load consultations and assets on mount
  useEffect(() => {
    fetchConsultations();
    fetchAssets();
  }, [fetchConsultations, fetchAssets]);

  // 016-draft-fact-summary: fact-summary 존재 여부 확인
  const checkFactSummary = useCallback(async () => {
    if (!caseId) return;
    try {
      const response = await getFactSummary(caseId);
      const aiSummary = response.data?.ai_summary || '';
      const modifiedSummary = response.data?.modified_summary || '';
      setHasFactSummary(!!(aiSummary || modifiedSummary));
      // Set editor content if summary exists
      if (modifiedSummary) {
        setFactSummaryContent(modifiedSummary);
      } else if (aiSummary) {
        setFactSummaryContent(aiSummary);
      }
    } catch {
      setHasFactSummary(false);
    }
  }, [caseId]);

  useEffect(() => {
    checkFactSummary();
  }, [checkFactSummary]);

  // Handle fact summary generation
  const handleGenerateFactSummary = useCallback(async () => {
    if (!caseId) return;

    setIsGeneratingFactSummary(true);
    try {
      const response = await generateFactSummary(caseId, {
        force_regenerate: hasFactSummary,
      });

      if (response.error) {
        logger.error('Fact summary generation error:', response.error);
        alert(`요약 생성 실패: ${response.error}`);
        return;
      }

      if (response.data?.ai_summary) {
        setFactSummaryContent(response.data.ai_summary);
        setHasFactSummary(true);
      }
    } catch (err) {
      logger.error('Fact summary generation error:', err);
      alert('사실관계 요약 생성에 실패했습니다.');
    } finally {
      setIsGeneratingFactSummary(false);
    }
  }, [caseId, hasFactSummary]);

  // Auto-polling: silently check for status updates
  useEffect(() => {
    const hasProcessingItems = evidenceList.some(
      e => e.status === 'processing' || e.status === 'queued' || e.status === 'uploading'
    );

    if (!hasProcessingItems || !caseId) return;

    const pollInterval = setInterval(async () => {
      try {
        const result = await getEvidence(caseId);
        if (result.data) {
          const newList = result.data.evidence.map(e => mapApiEvidenceToEvidence(e));

          setEvidenceList(prevList => {
            let hasChanges = false;
            const updatedList = prevList.map(prevItem => {
              const newItem = newList.find(n => n.id === prevItem.id);
              if (newItem && (newItem.status !== prevItem.status || newItem.summary !== prevItem.summary)) {
                hasChanges = true;
                return newItem;
              }
              return prevItem;
            });

            const newItems = newList.filter(n => !prevList.some(p => p.id === n.id));
            if (newItems.length > 0) {
              hasChanges = true;
            }

            return hasChanges ? [...updatedList, ...newItems] : prevList;
          });
        }
      } catch {
        // Silently ignore polling errors
      }
    }, 5000);

    return () => clearInterval(pollInterval);
  }, [evidenceList, caseId]);

  // Phase A.3: Use useEvidenceUpload hook for file upload
  const {
    handleUpload,
    uploadStatus,
    uploadFeedback,
    isUploading,
  } = useEvidenceUpload(caseId, {
    onUploadComplete: fetchEvidence,
  });

  // Draft generation handler (async with polling)
  // 016-draft-fact-summary: 증거 선택 없이 fact-summary 기반 생성
  const handleGenerateDraft = useCallback(async () => {
    if (!caseId) return;

    setIsGeneratingDraft(true);
    setDraftError(null);
    setDraftProgress(0);
    setDraftStatus('queued');

    try {
      // Use async version with progress callback
      const response = await generateDraftPreviewAsync(
        caseId,
        {
          sections: ['청구취지', '청구원인'],
          language: 'ko',
          style: '법원 제출용_표준',
        },
        // Progress callback
        (progress, status) => {
          setDraftProgress(progress);
          setDraftStatus(status);
        },
        120000,  // 2 minute max wait
        1500     // 1.5 second poll interval
      );

      if (response.error || !response.data) {
        throw new Error(response.error || '초안 생성에 실패했습니다.');
      }

      const { draft_text, citations } = response.data;

      // Map API citations to component format
      const mappedCitations: DraftCitation[] = citations.map(c => ({
        evidenceId: c.evidence_id,
        title: c.snippet.substring(0, 50) + (c.snippet.length > 50 ? '...' : ''),
        quote: c.snippet,
      }));

      setDraftText(draft_text);
      setDraftCitations(mappedCitations);
      setHasExistingDraft(true);
      setShowDraftModal(false);
      setActiveTab('draft');
    } catch (err) {
      logger.error('Draft generation error:', err);
      setDraftError(err instanceof Error ? err.message : '초안 생성에 실패했습니다.');
    } finally {
      setIsGeneratingDraft(false);
      setDraftProgress(0);
      setDraftStatus(null);
    }
  }, [caseId]);

  // Draft download handler
  const handleDraftDownload = useCallback(async (data: { format: DraftDownloadFormat; content: string }): Promise<DownloadResult> => {
    try {
      const result = await downloadDraftAsDocx(data.content, caseId, data.format);
      return result;
    } catch (err) {
      logger.error('Draft download error:', err);
      return {
        success: false,
        error: err instanceof Error ? err.message : '다운로드에 실패했습니다.',
      };
    }
  }, [caseId]);

  // Draft re-generate handler (opens modal)
  const handleDraftRegenerate = useCallback(() => {
    setShowDraftModal(true);
  }, []);

  // Phase B.4: Procedure Logic (Round 2 UX)
  const procedure = useProcedure(caseId || '');

  // Race condition 방어: ID가 없으면 로딩 스피너 또는 에러 표시
  if (isIdMissing) {
    // 2초 후에도 ID가 없으면 에러 UI 표시
    if (idWaitTimedOut) {
      return (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <svg className="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <h2 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">잘못된 접근입니다</h2>
            <p className="text-sm text-[var(--color-text-secondary)] mb-4">사건 ID가 올바르지 않거나 전달되지 않았습니다.</p>
            <Link
              href="/lawyer/cases"
              className="inline-flex items-center px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] transition-colors"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              목록으로 돌아가기
            </Link>
          </div>
        </div>
      );
    }
    // 타임아웃 전에는 로딩 스피너 표시
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
      </div>
    );
  }

  if (error || !caseDetail) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
          <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
          {error || '케이스를 찾을 수 없습니다'}
        </h2>
        <Link
          href="/lawyer/cases"
          className="text-[var(--color-primary)] hover:underline"
        >
          케이스 목록으로 돌아가기
        </Link>
      </div>
    );
  }

  // Phase A.1: Use getCaseStatusConfig for status colors/labels
  const statusConfig = getCaseStatusConfig(caseDetail.status);

  // Map case status to UtilityBar status
  const utilityBarStatus: CaseStatus = caseDetail.status === 'completed' ? 'completed'
    : caseDetail.status === 'on_hold' ? 'on_hold'
    : caseDetail.status === 'in_progress' ? 'in_progress'
    : 'pending';

  return (
    <div className="space-y-0">
      {/* LDS2: UtilityBar replaces breadcrumb and header */}
      <UtilityBar
        breadcrumbs={[
          { label: '케이스 관리', href: '/lawyer/cases' },
          { label: caseDetail.title },
        ]}
        caseStatus={utilityBarStatus}
        assignee={caseDetail.ownerName || caseDetail.ownerEmail}
        onSettingsClick={() => setShowEditModal(true)}
        onShareClick={() => setShowShareModal(true)}
        showNotifications={true}
      />

      {/* Expert Insights Panel */}
      <ExpertInsightsPanel
        isOpen={showExpertPanel}
        onClose={() => setShowExpertPanel(false)}
      />

      {/* LDS2 Tabs - 4 main tabs with Compact styling */}
      <div className="border-b border-gray-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 px-3">
        <nav className="flex gap-0.5">
          {[
            { id: 'workspace', label: '워크스페이스', icon: <Scale className="w-3.5 h-3.5" /> },
            { id: 'caseSummary', label: '사건정리', icon: <ClipboardList className="w-3.5 h-3.5" /> },
            { id: 'relations', label: '고객정보', icon: <FileText className="w-3.5 h-3.5" /> },
            { id: 'timeline', label: '타임라인', icon: <Activity className="w-3.5 h-3.5" /> },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`
                flex items-center gap-1 px-3 py-2 text-xs font-medium rounded-t
                border-b-2 -mb-[2px] transition-all duration-150 ease-out
                active:scale-[0.98]
                ${activeTab === tab.id
                  ? 'border-[var(--color-primary)] text-[var(--color-primary)] bg-primary/5'
                  : 'border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] hover:bg-gray-50 dark:hover:bg-neutral-700'
                }
              `}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content - LDS2 Compact */}
      <div className="bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-lg p-2">
        {/* 014-ui-settings-completion: 3-column workspace layout */}
        {activeTab === 'workspace' && (
          <CaseWorkspace
            leftPanel={
              <CaseDataPanel
                evidenceContent={
                  <EvidenceListCompact
                    items={evidenceList.map((e): LegalEvidence => ({
                      ...e,
                      legalNumber: e.legalNumber || `${e.submittedBy === 'defendant' ? '을' : e.submittedBy === 'third_party' ? '병' : '갑'}제${evidenceList.indexOf(e) + 1}호증`,
                    }))}
                    onItemClick={(_item) => { /* TODO: Navigate to evidence detail */ }}
                  />
                }
                evidenceCount={evidenceList.length}
                onUploadEvidence={() => setShowEvidenceUploadModal(true)}
                consultationContent={
                  <ConsultationListCompact
                    consultations={consultationList}
                    onItemClick={() => setShowConsultationAddModal(true)}
                  />
                }
                consultationCount={consultationList.length}
                onAddConsultation={() => setShowConsultationAddModal(true)}
                assetContent={
                  <AssetListCompact
                    assets={assetList}
                    onItemClick={() => setShowAssetAddModal(true)}
                  />
                }
                assetCount={assetList.length}
                onAddAsset={() => setShowAssetAddModal(true)}
                precedentContent={
                  <SimilarPrecedentList
                    caseId={caseId}
                    maxItems={5}
                    onViewDetail={(_precedent) => { /* TODO: Open precedent detail modal */ }}
                  />
                }
              />
            }
            mainContent={
              <MainWorkspace
                factSummaryContent={
                  <FactSummaryEditor
                    content={factSummaryContent}
                    onChange={setFactSummaryContent}
                    placeholder="사실관계를 입력하세요..."
                  />
                }
                onGenerateFactSummary={handleGenerateFactSummary}
                isGeneratingFactSummary={isGeneratingFactSummary}
                hasFactSummary={hasFactSummary}
                analysisContent={
                  <AnalysisTab
                    caseId={caseId || ''}
                    evidenceCount={evidenceList.length}
                    onDraftGenerate={() => setShowDraftModal(true)}
                  />
                }
                onGenerateDraft={() => setShowDraftModal(true)}
                hasDraft={hasExistingDraft}
                isGeneratingDraft={isGeneratingDraft}
              />
            }
            rightPanel={
              <ContextPanel
                timelineEvents={caseDetail.recentActivities.slice(0, 5).map((a, i) => ({
                  id: String(i),
                  action: a.action,
                  timestamp: a.timestamp,
                  user: a.user,
                }))}
                onViewTimeline={() => setActiveTab('timeline')}
                onViewRelations={() => setActiveTab('relations')}
                onViewAssets={() => setActiveTab('assets')}
              />
            }
            leftPanelTitle="자료"
            rightPanelTitle="컨텍스트"
            defaultLeftOpen={true}
            defaultRightOpen={false}
          />
        )}

        {activeTab === 'evidence' && (
          <div className="space-y-6">
            {/* Evidence Upload Section */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-[var(--color-text-primary)]">증거 업로드</h2>
                  <p className="text-sm text-[var(--color-text-secondary)]">파일을 드래그하거나 클릭하여 업로드할 수 있습니다.</p>
                </div>
                <span className="text-xs text-[var(--color-text-secondary)] flex items-center">
                  <Sparkles className="w-4 h-4 text-[var(--color-primary)] mr-1" /> Whisper · OCR 자동 적용
                </span>
              </div>
              <EvidenceUpload onUpload={handleUpload} disabled={uploadStatus.isUploading} />
              {uploadStatus.isUploading && (
                <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg px-4 py-3 text-sm">
                  <div className="flex items-center space-x-2 mb-2">
                    <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
                    <span className="text-blue-800 dark:text-blue-300 font-medium">
                      업로드 중 ({uploadStatus.completed + 1}/{uploadStatus.total})
                    </span>
                  </div>
                  <p className="text-blue-700 dark:text-blue-400 text-xs mb-2 truncate">{uploadStatus.currentFile}</p>
                  <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${uploadStatus.progress}%` }}
                    />
                  </div>
                </div>
              )}
              {uploadFeedback && !uploadStatus.isUploading && (
                <div
                  className={`flex items-start space-x-2 rounded-lg px-4 py-3 text-sm ${
                    uploadFeedback.tone === 'success'
                      ? 'bg-green-50 dark:bg-green-900/20 text-green-800 dark:text-green-300'
                      : uploadFeedback.tone === 'error'
                      ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800'
                      : 'bg-gray-100 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300'
                  }`}
                >
                  <CheckCircle2 className={`w-4 h-4 mt-0.5 ${
                    uploadFeedback.tone === 'error' ? 'text-red-500' : 'text-green-500'
                  }`} />
                  <p>{uploadFeedback.message}</p>
                </div>
              )}
            </section>

            {/* Evidence List Section */}
            <section className="space-y-4 pt-4 border-t border-gray-200 dark:border-neutral-700">
              <div className="flex justify-between items-center">
                <div>
                  <h2 className="text-lg font-bold text-[var(--color-text-primary)]">
                    증거 목록 <span className="text-[var(--color-text-secondary)] text-sm font-normal">
                      ({filteredEvidenceList.length}{(filterType !== 'all' || filterStatus !== 'all') && `/${evidenceList.length}`})
                    </span>
                  </h2>
                  <p className="text-xs text-[var(--color-text-secondary)]">상태 컬럼을 통해 AI 분석 파이프라인의 진행 상황을 확인하세요.</p>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={fetchEvidence}
                    disabled={isLoadingEvidence}
                    className="flex items-center text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] bg-white dark:bg-neutral-800 border border-gray-300 dark:border-neutral-600 px-3 py-1.5 rounded-md shadow-sm disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 mr-2 ${isLoadingEvidence ? 'animate-spin' : ''}`} />
                    새로고침
                  </button>
                  <div className="relative">
                    <button
                      onClick={() => setShowFilterDropdown(!showFilterDropdown)}
                      className={`flex items-center text-sm text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] bg-white dark:bg-neutral-800 border px-3 py-1.5 rounded-md shadow-sm ${
                        (filterType !== 'all' || filterStatus !== 'all')
                          ? 'border-[var(--color-primary)] text-[var(--color-primary)]'
                          : 'border-gray-300 dark:border-neutral-600'
                      }`}
                    >
                      <Filter className="w-4 h-4 mr-2" />
                      필터{(filterType !== 'all' || filterStatus !== 'all') && ' (활성)'}
                    </button>
                    {showFilterDropdown && (
                      <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-neutral-800 border border-gray-300 dark:border-neutral-600 rounded-lg shadow-lg z-20 p-4">
                        <div className="mb-3">
                          <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">파일 타입</label>
                          <select
                            value={filterType}
                            onChange={(e) => setFilterType(e.target.value as EvidenceType | 'all')}
                            className="w-full text-sm border border-gray-300 dark:border-neutral-600 rounded-md px-2 py-1.5 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)]"
                          >
                            <option value="all">전체</option>
                            <option value="text">텍스트</option>
                            <option value="image">이미지</option>
                            <option value="audio">오디오</option>
                            <option value="video">비디오</option>
                            <option value="pdf">PDF</option>
                          </select>
                        </div>
                        <div className="mb-3">
                          <label className="block text-xs font-medium text-[var(--color-text-secondary)] mb-1">처리 상태</label>
                          <select
                            value={filterStatus}
                            onChange={(e) => setFilterStatus(e.target.value as EvidenceStatus | 'all')}
                            className="w-full text-sm border border-gray-300 dark:border-neutral-600 rounded-md px-2 py-1.5 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)]"
                          >
                            <option value="all">전체</option>
                            <option value="queued">대기중</option>
                            <option value="processing">처리중</option>
                            <option value="completed">완료</option>
                            <option value="failed">실패</option>
                          </select>
                        </div>
                        <div className="flex justify-between items-center pt-2 border-t border-gray-200 dark:border-neutral-700">
                          <button
                            onClick={() => {
                              setFilterType('all');
                              setFilterStatus('all');
                            }}
                            className="text-xs text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
                          >
                            필터 초기화
                          </button>
                          <button
                            onClick={() => setShowFilterDropdown(false)}
                            className="text-xs text-[var(--color-primary)] hover:underline"
                          >
                            닫기
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              {isLoadingEvidence && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 text-[var(--color-primary)] animate-spin" />
                  <span className="ml-2 text-[var(--color-text-secondary)]">증거 목록을 불러오는 중...</span>
                </div>
              )}
              {evidenceError && !isLoadingEvidence && (
                <ErrorState
                  title="증거 목록을 불러올 수 없습니다"
                  message={evidenceError}
                  onRetry={fetchEvidence}
                  retryText="다시 시도"
                  size="sm"
                />
              )}
              {!isLoadingEvidence && !evidenceError && evidenceList.length === 0 && (
                <EvidenceEmptyState
                  caseTitle={caseDetail?.title}
                  size="sm"
                />
              )}
              {!isLoadingEvidence && !evidenceError && evidenceList.length > 0 && filteredEvidenceList.length === 0 && (
                <div className="text-center py-8">
                  <p className="text-[var(--color-text-secondary)]">
                    필터 조건에 맞는 증거가 없습니다.
                  </p>
                  <button
                    onClick={() => {
                      setFilterType('all');
                      setFilterStatus('all');
                    }}
                    className="mt-2 text-sm text-[var(--color-primary)] hover:underline"
                  >
                    필터 초기화
                  </button>
                </div>
              )}
              {!isLoadingEvidence && !evidenceError && filteredEvidenceList.length > 0 && (
                <EvidenceTable items={filteredEvidenceList} />
              )}
            </section>
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="space-y-8 max-w-3xl">
            {/* Procedure Timeline Section */}
            <div>
              <h3 className="text-lg font-bold text-[var(--color-text-primary)] mb-4">절차 진행 현황</h3>
              <ProcedureTimeline
                stages={procedure.stages}
                currentStage={procedure.currentStage}
                progressPercent={procedure.progressPercent}
                validNextStages={procedure.validNextStages}
                loading={procedure.loading}
                error={procedure.error}
                onUpdateStage={procedure.updateStage}
                onCompleteStage={procedure.completeStage}
                onSkipStage={procedure.skipStage}
                onTransition={procedure.transition}
                onInitialize={procedure.initializeTimeline}
              />
            </div>

            {/* Recent Activity Section */}
            <div>
              <h3 className="text-lg font-bold text-[var(--color-text-primary)] mb-4">최근 활동 로그</h3>
              {caseDetail.recentActivities.length > 0 ? (
                <div className="bg-white dark:bg-neutral-800 rounded-lg border border-gray-200 dark:border-neutral-700 divide-y divide-gray-100 dark:divide-neutral-700">
                  {caseDetail.recentActivities.map((activity, index) => {
                    // Determine icon based on action text
                    const actionLower = activity.action.toLowerCase();
                    let Icon = Activity;
                    let iconColor = 'text-gray-500';
                    if (actionLower.includes('업로드') || actionLower.includes('증거')) {
                      Icon = FileUp;
                      iconColor = 'text-blue-500';
                    } else if (actionLower.includes('상담') || actionLower.includes('메시지')) {
                      Icon = MessageSquare;
                      iconColor = 'text-green-500';
                    } else if (actionLower.includes('수정') || actionLower.includes('편집')) {
                      Icon = Edit3;
                      iconColor = 'text-orange-500';
                    } else if (actionLower.includes('접수') || actionLower.includes('생성')) {
                      Icon = FileText;
                      iconColor = 'text-purple-500';
                    } else if (actionLower.includes('담당자') || actionLower.includes('멤버')) {
                      Icon = UserPlus;
                      iconColor = 'text-indigo-500';
                    } else if (actionLower.includes('일정') || actionLower.includes('기일')) {
                      Icon = Calendar;
                      iconColor = 'text-pink-500';
                    } else if (actionLower.includes('알림')) {
                      Icon = Bell;
                      iconColor = 'text-yellow-500';
                    }

                    return (
                      <div key={index} className="flex items-center gap-3 px-4 py-3">
                        <div className={`flex-shrink-0 ${iconColor}`}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-[var(--color-text-primary)] truncate">{activity.action}</p>
                        </div>
                        <div className="flex-shrink-0 text-xs text-[var(--color-text-secondary)] whitespace-nowrap">
                          <span className="hidden sm:inline">{activity.user} · </span>
                          {new Date(activity.timestamp).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-center text-[var(--color-text-secondary)] py-8 bg-gray-50 dark:bg-neutral-900/50 rounded-lg">
                  활동 기록이 없습니다.
                </p>
              )}
            </div>
          </div>
        )}

        {activeTab === 'caseSummary' && (
          <div className="space-y-6">
            {/* 사건정리 탭 헤더 */}
            <div className="bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-lg p-4 border border-purple-200 dark:border-purple-800">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-100 dark:bg-purple-800/50 rounded-lg">
                  <ClipboardList className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-purple-800 dark:text-purple-200">사건 정리</h3>
                  <p className="text-sm text-purple-600 dark:text-purple-400">사건의 인물 관계와 절차 진행 현황을 한눈에 확인합니다.</p>
                </div>
              </div>
            </div>

            {/* 인물 관계도 섹션 */}
            <div className="bg-white dark:bg-neutral-800 rounded-lg border border-gray-200 dark:border-neutral-700">
              <div className="px-4 py-3 border-b border-gray-200 dark:border-neutral-700 bg-gray-50 dark:bg-neutral-900/50">
                <div className="flex items-center gap-2">
                  <UserPlus className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  <h4 className="font-semibold text-[var(--color-text-primary)]">인물 관계도</h4>
                </div>
                <p className="text-xs text-[var(--color-text-secondary)] mt-1">사건 관련 당사자들의 관계를 시각적으로 표현합니다.</p>
              </div>
              <div className="p-4">
                <div className="h-[300px] lg:h-[350px]">
                  <PartyGraph caseId={caseId} />
                </div>
              </div>
            </div>

            {/* 절차 진행 현황 섹션 */}
            <div className="bg-white dark:bg-neutral-800 rounded-lg border border-gray-200 dark:border-neutral-700">
              <div className="px-4 py-3 border-b border-gray-200 dark:border-neutral-700 bg-gray-50 dark:bg-neutral-900/50">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <h4 className="font-semibold text-[var(--color-text-primary)]">절차 진행 현황</h4>
                </div>
                <p className="text-xs text-[var(--color-text-secondary)] mt-1">소송 절차의 진행 단계와 현재 상태를 확인합니다.</p>
              </div>
              <div className="p-4">
                <ProcedureTimeline
                  stages={procedure.stages}
                  currentStage={procedure.currentStage}
                  progressPercent={procedure.progressPercent}
                  validNextStages={procedure.validNextStages}
                  loading={procedure.loading}
                  error={procedure.error}
                  onUpdateStage={procedure.updateStage}
                  onCompleteStage={procedure.completeStage}
                  onSkipStage={procedure.skipStage}
                  onTransition={procedure.transition}
                  onInitialize={procedure.initializeTimeline}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'analysis' && (
          <div className="space-y-6">
            {/* 014-case-fact-summary: 사실관계 요약 패널 */}
            <FactSummaryPanel caseId={caseId} />

            {/* 기존 분석 탭 */}
            <AnalysisTab
              caseId={caseId}
              evidenceCount={caseDetail.evidenceCount}
              onDraftGenerate={() => {
                setActiveTab('draft');
                setShowDraftModal(true);
              }}
            />
          </div>
        )}

        {activeTab === 'relations' && (
          <div className="space-y-6">
            {/* Client Report Header - Task 7 */}
            <div className="bg-gradient-to-r from-indigo-50 to-blue-50 dark:from-indigo-900/20 dark:to-blue-900/20 rounded-lg p-4 border border-indigo-200 dark:border-indigo-800">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-indigo-100 dark:bg-indigo-800/50 rounded-lg">
                  <FileText className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-indigo-800 dark:text-indigo-200">고객 리포트</h3>
                  <p className="text-sm text-indigo-600 dark:text-indigo-400">의뢰인 정보와 관계도를 한눈에 확인합니다.</p>
                </div>
              </div>
            </div>

            {/* Client Information Card - Task 7 */}
            <div className="bg-white dark:bg-neutral-800 rounded-lg border border-gray-200 dark:border-neutral-700">
              <div className="px-4 py-3 border-b border-gray-200 dark:border-neutral-700">
                <h4 className="font-semibold text-[var(--color-text-primary)]">의뢰인 정보</h4>
              </div>
              <div className="p-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div>
                    <p className="text-xs text-[var(--color-text-secondary)] mb-1">이름</p>
                    <p className="font-medium text-[var(--color-text-primary)]">
                      {caseDetail.clientName || '미입력'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-text-secondary)] mb-1">사건 번호</p>
                    <p className="font-medium text-[var(--color-text-primary)]">
                      {caseDetail.id.slice(0, 8).toUpperCase()}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-text-secondary)] mb-1">사건 상태</p>
                    <p className="font-medium text-[var(--color-text-primary)]">
                      {statusConfig.label}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-text-secondary)] mb-1">담당 변호사</p>
                    <p className="font-medium text-[var(--color-text-primary)]">
                      {caseDetail.ownerName || caseDetail.ownerEmail || '미지정'}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-text-secondary)] mb-1">접수일</p>
                    <p className="font-medium text-[var(--color-text-primary)]">
                      {new Date(caseDetail.createdAt).toLocaleDateString('ko-KR')}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-[var(--color-text-secondary)] mb-1">증거 수</p>
                    <p className="font-medium text-[var(--color-text-primary)]">
                      {evidenceList.length}건
                    </p>
                  </div>
                </div>
                {caseDetail.description && (
                  <div className="mt-4 pt-4 border-t border-gray-100 dark:border-neutral-700">
                    <p className="text-xs text-[var(--color-text-secondary)] mb-1">사건 개요</p>
                    <p className="text-sm text-[var(--color-text-primary)]">
                      {caseDetail.description}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Relationship Graph - Kept from original */}
            <div className="bg-white dark:bg-neutral-800/50 rounded-lg border border-gray-200 dark:border-neutral-700 p-3">
              <div className="flex items-center gap-2 mb-2">
                <UserPlus className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                <h4 className="font-medium text-[var(--color-text-primary)]">인물 관계도</h4>
              </div>
              <div className="h-[280px] lg:h-[320px]">
                <PartyGraph caseId={caseId} />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'consultation' && (
          <div className="space-y-6">
            {/* Consultation Header */}
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-100 dark:bg-green-800/50 rounded-lg">
                  <MessageSquare className="w-5 h-5 text-green-600 dark:text-green-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-green-800 dark:text-green-200">상담 관리</h3>
                  <p className="text-sm text-green-600 dark:text-green-400">의뢰인과의 상담 기록을 체계적으로 관리하세요.</p>
                </div>
              </div>
            </div>
            {/* Consultation Content */}
            <div className="bg-white dark:bg-neutral-800/50 rounded-lg border border-gray-200 dark:border-neutral-700 p-6">
              <ConsultationHistoryTab
                caseId={caseId}
                externalOpenModal={showConsultationAddModal}
                onExternalModalClose={() => setShowConsultationAddModal(false)}
              />
            </div>
          </div>
        )}

        {activeTab === 'assets' && (
          <div className="space-y-6">
            {/* Assets Header */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-800/50 rounded-lg">
                  <Wallet className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h3 className="font-semibold text-blue-800 dark:text-blue-200">재산분할 현황</h3>
                  <p className="text-sm text-blue-600 dark:text-blue-400">부동산, 금융자산, 차량 등 재산 목록을 관리합니다.</p>
                </div>
              </div>
            </div>
            {/* Assets Content */}
            <div className="bg-white dark:bg-neutral-800/50 rounded-lg border border-gray-200 dark:border-neutral-700 p-6">
              <AssetSummaryTab
                caseId={caseId}
                externalOpenAddForm={showAssetAddModal}
                onExternalAddFormClose={() => setShowAssetAddModal(false)}
              />
            </div>
          </div>
        )}

        {activeTab === 'draft' && (
          <div className="space-y-6">
            {/* Draft Error State */}
            {draftError && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3 text-sm">
                <div className="flex items-center space-x-2">
                  <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-red-800 dark:text-red-300">{draftError}</span>
                </div>
              </div>
            )}

            {/* No Draft Yet - Show Generate Button */}
            {!hasExistingDraft && !isGeneratingDraft && (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                  <FileText className="w-8 h-8 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                  법률 초안 생성
                </h3>
                <p className="text-[var(--color-text-secondary)] mb-6 max-w-md mx-auto">
                  등록된 증거 자료를 기반으로 AI가 법률 문서 초안을 생성합니다.
                  생성된 초안은 검토 후 수정할 수 있습니다.
                </p>
                <button
                  onClick={() => setShowDraftModal(true)}
                  className="inline-flex items-center px-6 py-3 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] transition-colors"
                >
                  <Sparkles className="w-5 h-5 mr-2" />
                  초안 생성하기
                </button>
                {evidenceList.length === 0 && (
                  <p className="text-sm text-amber-600 dark:text-amber-400 mt-4">
                    초안 생성을 위해 먼저 증거 자료를 업로드해주세요.
                  </p>
                )}
              </div>
            )}

            {/* Generating State */}
            {isGeneratingDraft && (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                  <Loader2 className="w-8 h-8 text-purple-600 dark:text-purple-400 animate-spin" />
                </div>
                <h3 className="text-lg font-semibold text-[var(--color-text-primary)] mb-2">
                  초안 생성 중...
                </h3>
                <p className="text-[var(--color-text-secondary)]">
                  AI가 증거를 분석하고 법률 초안을 작성하고 있습니다.
                </p>
              </div>
            )}

            {/* Draft Preview Panel */}
            {hasExistingDraft && !isGeneratingDraft && (
              <DraftPreviewPanel
                caseId={caseId}
                draftText={draftText}
                citations={draftCitations}
                isGenerating={isGeneratingDraft}
                hasExistingDraft={hasExistingDraft}
                onGenerate={handleDraftRegenerate}
                onDownload={handleDraftDownload}
              />
            )}
          </div>
        )}
      </div>

      {/* Summary Card Modal */}
      <ExplainerCard
        caseId={caseId}
        isOpen={showSummaryCard}
        onClose={() => setShowSummaryCard(false)}
        onShare={() => {
          setShowSummaryCard(false);
          setShowShareModal(true);
        }}
      />

      {/* Share Summary Modal */}
      <ShareSummaryModal
        caseId={caseId}
        caseTitle={caseDetail.title}
        isOpen={showShareModal}
        onClose={() => setShowShareModal(false)}
      />

      {/* Edit Case Modal */}
      <EditCaseModal
        isOpen={showEditModal}
        onClose={() => setShowEditModal(false)}
        caseData={{
          id: caseDetail.id,
          title: caseDetail.title,
          clientName: caseDetail.clientName,
          description: caseDetail.description,
        }}
        onSuccess={(updatedCase: ApiCase) => {
          setCaseDetail((prev) =>
            prev
              ? {
                  ...prev,
                  title: updatedCase.title,
                  clientName: updatedCase.client_name,
                  description: updatedCase.description,
                  updatedAt: updatedCase.updated_at,
                }
              : null
          );
        }}
      />

      {/* Draft Generation Modal */}
      {/* 016-draft-fact-summary: fact-summary 기반 초안 생성 */}
      <DraftGenerationModal
        isOpen={showDraftModal}
        onClose={() => setShowDraftModal(false)}
        onGenerate={handleGenerateDraft}
        hasFactSummary={hasFactSummary}
        progress={draftProgress}
        status={draftStatus}
      />

      {/* Evidence Upload Modal */}
      <EvidenceUploadModal
        isOpen={showEvidenceUploadModal}
        onClose={() => setShowEvidenceUploadModal(false)}
        onUpload={async (files) => {
          for (const fileData of files) {
            await handleUpload([fileData.file]);
          }
          fetchEvidence();
        }}
        caseId={caseId}
        isLoading={isUploading}
      />

      {/* Independent Consultation Modal */}
      <ConsultationModal
        isOpen={showConsultationAddModal}
        onClose={() => setShowConsultationAddModal(false)}
        caseId={caseId}
        onSuccess={fetchConsultations}
      />

      {/* Independent Asset Modal */}
      <AssetModal
        isOpen={showAssetAddModal}
        onClose={() => setShowAssetAddModal(false)}
        caseId={caseId}
        onSuccess={fetchAssets}
      />
    </div>
  );
}
