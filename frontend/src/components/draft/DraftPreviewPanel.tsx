'use client';

import { useState, useMemo, useEffect, useRef, useCallback } from 'react';
import {
    Loader2,
    FileText,
    Download,
    Sparkles,
    Bold,
    Italic,
    Underline,
    List,
    Save,
    History,
    X,
    Clock3,
} from 'lucide-react';
import DOMPurify from 'dompurify';
import { DraftCitation } from '@/types/draft';
import { DraftDownloadFormat } from '@/services/documentService';
import EvidenceTraceabilityPanel from './EvidenceTraceabilityPanel';
import {
    DraftVersionSnapshot,
    DraftSaveReason,
    loadDraftState,
    persistDraftState,
} from '@/services/draftStorageService';

interface DraftPreviewPanelProps {
    caseId: string;
    draftText: string;
    citations: DraftCitation[];
    isGenerating: boolean;
    hasExistingDraft: boolean;
    onGenerate: () => void;
    onDownload?: (data: { format: DraftDownloadFormat; content: string }) => void;
    onManualSave?: (content: string) => Promise<void> | void;
}

const AUTOSAVE_INTERVAL_MS = 5 * 60 * 1000;
const HISTORY_LIMIT = 10;
const SANITIZE_OPTIONS = {
    ALLOWED_TAGS: ['b', 'i', 'u', 'strong', 'em', 'p', 'br', 'span', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4'],
    ALLOWED_ATTR: ['class', 'data-evidence-id'],
};

const sanitizeDraftHtml = (html: string) => DOMPurify.sanitize(html, SANITIZE_OPTIONS);

const generateVersionId = () => {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
    }
    return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
};

const formatAutosaveStatus = (timestamp: string | null) => {
    if (!timestamp) {
        return '자동 저장 준비 중';
    }
    const diffMs = Date.now() - new Date(timestamp).getTime();
    if (diffMs < 60_000) {
        return '자동 저장됨 · 방금';
    }
    const minutes = Math.floor(diffMs / 60_000);
    if (minutes < 60) {
        return `자동 저장됨 · ${minutes}분 전`;
    }
    const hours = Math.floor(minutes / 60);
    return `자동 저장됨 · ${hours}시간 전`;
};

const formatVersionReason = (reason: DraftSaveReason) => {
    switch (reason) {
        case 'manual':
            return '수동 저장';
        case 'auto':
            return '자동 저장';
        case 'ai':
            return 'AI 초안';
        default:
            return '저장';
    }
};

const formatTimestamp = (iso: string) =>
    new Date(iso).toLocaleString('ko-KR', {
        hour12: false,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
    });

export default function DraftPreviewPanel({
    caseId,
    draftText,
    citations,
    isGenerating,
    hasExistingDraft,
    onGenerate,
    onDownload,
    onManualSave,
}: DraftPreviewPanelProps) {
    const buttonLabel = hasExistingDraft ? '초안 재생성' : '초안 생성';
    const [editorHtml, setEditorHtml] = useState(() => sanitizeDraftHtml(draftText));
    const [versionHistory, setVersionHistory] = useState<DraftVersionSnapshot[]>([]);
    const [lastSavedAt, setLastSavedAt] = useState<string | null>(null);
    const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
    const [isTraceabilityPanelOpen, setIsTraceabilityPanelOpen] = useState(false);
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState<string | null>(null);
    const editorRef = useRef<HTMLDivElement>(null);
    const autosaveTimerRef = useRef<NodeJS.Timeout | null>(null);
    const versionHistoryRef = useRef<DraftVersionSnapshot[]>([]);
    const lastSavedAtRef = useRef<string | null>(null);
    const lastImportedDraftRef = useRef<string | null>(null);

    const sanitizedDraftText = useMemo(() => sanitizeDraftHtml(draftText), [draftText]);

    useEffect(() => {
        versionHistoryRef.current = versionHistory;
    }, [versionHistory]);

    useEffect(() => {
        lastSavedAtRef.current = lastSavedAt;
    }, [lastSavedAt]);

    const persistCurrentState = useCallback(
        (content: string, history?: DraftVersionSnapshot[], savedAt?: string | null) => {
            persistDraftState(caseId, {
                content,
                history: history ?? versionHistoryRef.current,
                lastSavedAt: savedAt ?? lastSavedAtRef.current,
            });
        },
        [caseId]
    );

    const recordVersion = useCallback(
        (reason: DraftSaveReason, overrideContent?: string) => {
            const contentToSave = sanitizeDraftHtml(overrideContent ?? editorHtml);
            if (!contentToSave || !contentToSave.replace(/<[^>]+>/g, '').trim()) {
                return;
            }

            const version: DraftVersionSnapshot = {
                id: generateVersionId(),
                content: contentToSave,
                savedAt: new Date().toISOString(),
                reason,
            };

            setVersionHistory((prev) => {
                const filtered = prev.filter((entry) => entry.content !== contentToSave);
                const updated = [version, ...filtered].slice(0, HISTORY_LIMIT);
                persistCurrentState(contentToSave, updated, version.savedAt);
                return updated;
            });
            setLastSavedAt(version.savedAt);

            if (reason === 'manual') {
                setSaveMessage('수동 저장 완료');
                setTimeout(() => setSaveMessage(null), 3000);
            }
        },
        [editorHtml, persistCurrentState]
    );

    useEffect(() => {
        const storedState = loadDraftState(caseId);
        if (storedState) {
            setEditorHtml(storedState.content || sanitizedDraftText);
            setVersionHistory(storedState.history || []);
            setLastSavedAt(storedState.lastSavedAt);
            lastImportedDraftRef.current = storedState.content || sanitizedDraftText;
        } else {
            setEditorHtml(sanitizedDraftText);
            lastImportedDraftRef.current = sanitizedDraftText;
        }
    }, [caseId, sanitizedDraftText]);

    useEffect(() => {
        if (!sanitizedDraftText) return;
        if (!lastImportedDraftRef.current) {
            lastImportedDraftRef.current = sanitizedDraftText;
            return;
        }
        if (sanitizedDraftText !== lastImportedDraftRef.current) {
            setEditorHtml(sanitizedDraftText);
            recordVersion('ai', sanitizedDraftText);
            lastImportedDraftRef.current = sanitizedDraftText;
        }
    }, [sanitizedDraftText, recordVersion]);

    useEffect(() => {
        if (!editorRef.current) return;
        if (editorRef.current.innerHTML !== editorHtml) {
            editorRef.current.innerHTML = editorHtml;
        }
    }, [editorHtml]);

    useEffect(() => {
        autosaveTimerRef.current = window.setInterval(() => {
            recordVersion('auto');
        }, AUTOSAVE_INTERVAL_MS);

        return () => {
            if (autosaveTimerRef.current) {
                clearInterval(autosaveTimerRef.current);
            }
        };
    }, [recordVersion]);

    const handleFormat = (command: string) => {
        document.execCommand(command, false, undefined);
    };

    const handleDownload = (format: DraftDownloadFormat) => {
        if (!onDownload) return;
        onDownload({ format, content: editorHtml });
    };

    const handleEditorClick = (e: React.MouseEvent<HTMLDivElement>) => {
        const target = e.target as HTMLElement;
        const evidenceId = target.getAttribute('data-evidence-id');

        if (evidenceId) {
            setSelectedEvidenceId(evidenceId);
            setIsTraceabilityPanelOpen(true);
        }
    };

    const handleEditorInput = (event: React.FormEvent<HTMLDivElement>) => {
        const html = sanitizeDraftHtml((event.currentTarget as HTMLDivElement).innerHTML);
        setEditorHtml(html);
        persistCurrentState(html);
    };

    const handleCloseTraceability = () => {
        setIsTraceabilityPanelOpen(false);
        setSelectedEvidenceId(null);
    };

    const handleManualSave = async () => {
        setIsSaving(true);
        try {
            recordVersion('manual');
            if (onManualSave) {
                await onManualSave(editorHtml);
            }
        } finally {
            setIsSaving(false);
        }
    };

    const handleRestoreVersion = (versionId: string) => {
        const targetVersion = versionHistory.find((version) => version.id === versionId);
        if (!targetVersion) return;
        setEditorHtml(targetVersion.content);
        persistCurrentState(targetVersion.content);
        setIsHistoryOpen(false);
    };

    return (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-6" aria-label="Draft editor">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <p className="text-sm text-neutral-600 leading-relaxed">
                        이 문서는 AI가 생성한 초안이며, 최종 책임은 변호사에게 있습니다.
                    </p>
                    <p className="text-xs text-gray-400 mt-2">
                        실제 제출 전 반드시 모든 내용을 검토하고 사실 관계를 확인해 주세요.
                    </p>
                </div>
                <div className="inline-flex items-center text-xs uppercase tracking-wide text-secondary font-semibold">
                    <Sparkles className="w-4 h-4 mr-1 text-accent" />
                    AI Draft
                </div>
            </div>

            <div className="flex flex-col gap-3 rounded-xl border border-gray-100 bg-neutral-50/60 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2">
                        <button
                            type="button"
                            onClick={handleManualSave}
                            disabled={isSaving}
                            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-secondary hover:border-accent hover:text-accent transition-colors disabled:opacity-60"
                        >
                            <Save className="w-4 h-4" />
                            저장
                        </button>
                        <button
                            type="button"
                            onClick={() => setIsHistoryOpen(true)}
                            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-secondary hover:border-accent hover:text-accent transition-colors"
                        >
                            <History className="w-4 h-4" />
                            버전 히스토리
                        </button>
                        {saveMessage && <span className="text-xs text-accent">{saveMessage}</span>}
                    </div>
                    <div className="inline-flex items-center text-xs text-gray-500" data-testid="autosave-indicator">
                        <Clock3 className="w-4 h-4 mr-1" />
                        {formatAutosaveStatus(lastSavedAt)}
                    </div>
                </div>
                <div
                    data-testid="draft-toolbar-panel"
                    className="flex items-center justify-between rounded-xl border border-gray-200 bg-white px-4 py-2 text-xs text-gray-500 tracking-wide"
                >
                    <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-secondary" />
                        <div className="h-4 w-px bg-gray-300 mx-2" />
                        <button
                            type="button"
                            aria-label="Bold"
                            onClick={() => handleFormat('bold')}
                            className="p-1 hover:bg-gray-200 rounded transition-colors"
                        >
                            <Bold className="w-4 h-4 text-neutral-700" />
                        </button>
                        <button
                            type="button"
                            aria-label="Italic"
                            onClick={() => handleFormat('italic')}
                            className="p-1 hover:bg-gray-200 rounded transition-colors"
                        >
                            <Italic className="w-4 h-4 text-neutral-700" />
                        </button>
                        <button
                            type="button"
                            aria-label="Underline"
                            onClick={() => handleFormat('underline')}
                            className="p-1 hover:bg-gray-200 rounded transition-colors"
                        >
                            <Underline className="w-4 h-4 text-neutral-700" />
                        </button>
                        <div className="h-4 w-px bg-gray-300 mx-2" />
                        <button type="button" aria-label="List" onClick={() => handleFormat('insertUnorderedList')} className="p-1 hover:bg-gray-200 rounded transition-colors">
                            <List className="w-4 h-4 text-neutral-700" />
                        </button>
                    </div>
                    <div className="inline-flex items-center gap-2">
                        <button
                            type="button"
                            onClick={() => handleDownload('docx')}
                            className="inline-flex items-center gap-1 text-xs font-medium text-secondary hover:text-accent transition-colors"
                        >
                            <Download className="w-4 h-4" />
                            DOCX
                        </button>
                        <button
                            type="button"
                            onClick={() => handleDownload('hwp')}
                            className="inline-flex items-center gap-1 text-xs font-medium text-secondary hover:text-accent transition-colors"
                        >
                            <Download className="w-4 h-4" />
                            HWP
                        </button>
                    </div>
                </div>
            </div>

            <div
                data-testid="draft-editor-surface"
                data-zen-mode="true"
                className="relative rounded-2xl border border-gray-100 bg-white shadow-inner focus-within:border-deep-trust-blue transition-colors"
            >
                <div
                    ref={editorRef}
                    data-testid="draft-editor-content"
                    contentEditable
                    suppressContentEditableWarning
                    aria-label="Draft content"
                    onClick={handleEditorClick}
                    onInput={handleEditorInput}
                    className="w-full min-h-[320px] bg-transparent p-6 text-gray-800 leading-relaxed focus:outline-none resize-none placeholder:text-gray-400 overflow-auto cursor-pointer [&_.evidence-ref]:underline [&_.evidence-ref]:text-secondary [&_.evidence-ref]:cursor-pointer [&_.evidence-ref:hover]:text-accent [&_.evidence-ref]:decoration-dotted"
                    dangerouslySetInnerHTML={{ __html: editorHtml }}
                />
            </div>

            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <button
                    type="button"
                    onClick={onGenerate}
                    disabled={isGenerating}
                    className={`btn-primary inline-flex items-center justify-center px-6 py-3 text-base ${isGenerating ? 'opacity-80 cursor-not-allowed' : ''}`}
                >
                    {isGenerating ? (
                        <span className="flex items-center gap-2">
                            <Loader2 className="w-5 h-5 animate-spin" />
                            생성 중...
                        </span>
                    ) : (
                        <span>{buttonLabel}</span>
                    )}
                </button>
                <div className="text-sm text-gray-500">
                    최신 초안 기준 <span className="font-semibold text-secondary">실제 증거 인용</span> {citations.length}건
                </div>
            </div>

            <div className="border-t border-gray-100 pt-4">
                <h4 className="text-sm font-semibold text-neutral-700 mb-3">Citations</h4>
                <div className="space-y-3">
                    {citations.map((citation) => (
                        <div key={citation.evidenceId} className="rounded-lg border border-gray-100 bg-neutral-50/60 p-3">
                            <p className="text-xs text-gray-500 mb-1">{citation.title}</p>
                            <p className="text-sm text-neutral-700 leading-relaxed">&ldquo;{citation.quote}&rdquo;</p>
                        </div>
                    ))}
                    {citations.length === 0 && <p className="text-sm text-gray-400">아직 연결된 증거가 없습니다.</p>}
                </div>
            </div>

            <EvidenceTraceabilityPanel
                isOpen={isTraceabilityPanelOpen}
                evidenceId={selectedEvidenceId}
                onClose={handleCloseTraceability}
            />

            {isHistoryOpen && (
                <div className="fixed inset-0 z-40 flex items-end justify-center bg-black/30 px-4 pb-6 sm:items-center" role="dialog" aria-label="버전 히스토리 패널">
                    <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl" data-testid="version-history-panel">
                        <div className="flex items-center justify-between mb-4">
                            <div>
                                <p className="text-base font-semibold text-gray-900">버전 히스토리</p>
                                <p className="text-xs text-gray-500 mt-1">최대 {HISTORY_LIMIT}개의 버전이 보관됩니다.</p>
                            </div>
                            <button
                                type="button"
                                aria-label="버전 히스토리 닫기"
                                onClick={() => setIsHistoryOpen(false)}
                                className="rounded-full p-2 text-gray-500 hover:bg-gray-100"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                        <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
                            {versionHistory.length === 0 && <p className="text-sm text-gray-500">저장된 버전이 없습니다.</p>}
                            {versionHistory.map((version) => (
                                <button
                                    key={version.id}
                                    type="button"
                                    onClick={() => handleRestoreVersion(version.id)}
                                    className="w-full rounded-xl border border-gray-200 bg-white p-3 text-left hover:border-accent focus:outline-none focus:ring-2 focus:ring-accent"
                                >
                                    <p className="text-sm font-semibold text-gray-900">{formatVersionReason(version.reason)}</p>
                                    <p className="text-xs text-gray-500">{formatTimestamp(version.savedAt)}</p>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </section>
    );
}
