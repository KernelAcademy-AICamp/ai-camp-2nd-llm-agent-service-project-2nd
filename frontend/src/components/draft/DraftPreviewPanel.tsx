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
    LayoutTemplate,
    Quote,
    MessageSquare,
    GitBranch,
    Users,
    CheckCircle,
    AlertCircle,
} from 'lucide-react';
import DOMPurify from 'dompurify';
import { DraftCitation } from '@/types/draft';
import { DraftDownloadFormat, DownloadResult } from '@/services/documentService';
import EvidenceTraceabilityPanel from './EvidenceTraceabilityPanel';
import {
    DraftVersionSnapshot,
    DraftSaveReason,
    DraftCommentSnapshot,
    DraftChangeLogEntry,
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
    onDownload?: (data: { format: DraftDownloadFormat; content: string }) => Promise<DownloadResult> | void;
    onManualSave?: (content: string) => Promise<void> | void;
}

interface ExportToast {
    type: 'success' | 'error';
    message: string;
    filename?: string;
}


const AUTOSAVE_INTERVAL_MS = 5 * 60 * 1000;
const HISTORY_LIMIT = 10;
const CHANGELOG_LIMIT = 20;
const SANITIZE_OPTIONS = {
    ALLOWED_TAGS: ['b', 'i', 'u', 'strong', 'em', 'p', 'br', 'span', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4'],
    ALLOWED_ATTR: ['class', 'data-evidence-id', 'data-comment-id', 'data-change-id'],
};

const DOCUMENT_TEMPLATES = [
    {
        id: 'answer-basic',
        name: '답변서 기본 템플릿',
        description: '사건 개요, 청구원인, 결론을 포함한 기본 양식',
        content: `
<h1>답 변 서</h1>
<p>사건번호: ________</p>
<p>원고: ________ / 피고: ________</p>
<h2>1. 사건 개요</h2>
<p>원고는 ____에 따라 본 소송을 제기하였습니다.</p>
<h2>2. 청구원인에 대한 답변</h2>
<p>원고의 주장에 대하여 피고는 다음과 같이 답변합니다.</p>
<h3>2.1 원고 주장 제1항에 대하여</h3>
<p>[증거기재]</p>
<h2>3. 결론</h2>
<p>따라서 원고의 청구는 기각되어야 합니다.</p>`,
    },
    {
        id: 'petition-basic',
        name: '준비서면 - 청구취지 강조',
        description: '청구취지, 청구원인, 증거목록으로 구성된 양식',
        content: `
<h1>준 비 서 면</h1>
<h2>1. 청구취지</h2>
<p>1. 피고는 원고에게 위자료 금 ________원을 지급하라.</p>
<h2>2. 청구원인</h2>
<h3>2.1 혼인 파탄 경위</h3>
<p>...</p>
<h3>2.2 유책 사유</h3>
<p>...</p>
<h2>3. 증거목록</h2>
<p>- 갑 제1호증: ________</p>
<p>- 갑 제2호증: ________</p>`,
    },
];

const sanitizeDraftHtml = (html: string) =>
    typeof window === 'undefined' ? html : DOMPurify.sanitize(html, SANITIZE_OPTIONS);
type IntervalHandle = ReturnType<typeof setInterval> | number;
type TimeoutHandle = ReturnType<typeof setTimeout> | number;
const stripHtml = (html: string) => html.replace(/<[^>]+>/g, '').trim();

const generateId = () => {
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
    const [isTemplateModalOpen, setIsTemplateModalOpen] = useState(false);
    const [isCitationModalOpen, setIsCitationModalOpen] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState<string | null>(null);
    const [comments, setComments] = useState<DraftCommentSnapshot[]>([]);
    const [newCommentText, setNewCommentText] = useState('');
    const [changeLog, setChangeLog] = useState<DraftChangeLogEntry[]>([]);
    const [isTrackChangesEnabled, setIsTrackChangesEnabled] = useState(false);
    const [collabStatus, setCollabStatus] = useState<string | null>(null);
    const [isExporting, setIsExporting] = useState(false);
    const [exportingFormat, setExportingFormat] = useState<DraftDownloadFormat | null>(null);
    const [exportToast, setExportToast] = useState<ExportToast | null>(null);
    const editorRef = useRef<HTMLDivElement>(null);
    const autosaveTimerRef = useRef<IntervalHandle | null>(null);
    const collabSyncTimerRef = useRef<TimeoutHandle | null>(null);
    const versionHistoryRef = useRef<DraftVersionSnapshot[]>([]);
    const lastSavedAtRef = useRef<string | null>(null);
    const lastImportedDraftRef = useRef<string | null>(null);
    const commentsRef = useRef<DraftCommentSnapshot[]>([]);
    const changeLogRef = useRef<DraftChangeLogEntry[]>([]);
    const channelRef = useRef<BroadcastChannel | null>(null);
    const clientIdRef = useRef<string>(generateId());
    const lastRemoteUpdateRef = useRef<number>(0);

    const sanitizedDraftText = useMemo(() => sanitizeDraftHtml(draftText), [draftText]);
    const pageCount = useMemo(() => Math.max(1, Math.ceil(stripHtml(editorHtml).length / 1800)), [editorHtml]);

    useEffect(() => {
        versionHistoryRef.current = versionHistory;
    }, [versionHistory]);

    useEffect(() => {
        lastSavedAtRef.current = lastSavedAt;
    }, [lastSavedAt]);

    useEffect(() => {
        commentsRef.current = comments;
    }, [comments]);

    useEffect(() => {
        changeLogRef.current = changeLog;
    }, [changeLog]);

    const persistCurrentState = useCallback(
        (
            content: string,
            history?: DraftVersionSnapshot[],
            savedAt?: string | null,
            commentsOverride?: DraftCommentSnapshot[],
            changeLogOverride?: DraftChangeLogEntry[]
        ) => {
            persistDraftState(caseId, {
                content,
                history: history ?? versionHistoryRef.current,
                lastSavedAt: savedAt ?? lastSavedAtRef.current,
                comments: commentsOverride ?? commentsRef.current,
                changeLog: changeLogOverride ?? changeLogRef.current,
            });
        },
        [caseId]
    );

    const recordVersion = useCallback(
        (reason: DraftSaveReason, overrideContent?: string) => {
            const contentToSave = sanitizeDraftHtml(overrideContent ?? editorHtml);
            if (!contentToSave || !stripHtml(contentToSave)) {
                return;
            }

            const version: DraftVersionSnapshot = {
                id: generateId(),
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
            setComments(storedState.comments || []);
            setChangeLog(storedState.changeLog || []);
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
        const timer = window.setInterval(() => {
            recordVersion('auto');
        }, AUTOSAVE_INTERVAL_MS);
        autosaveTimerRef.current = timer;

        return () => {
            if (autosaveTimerRef.current) {
                clearInterval(autosaveTimerRef.current);
            }
        };
    }, [recordVersion]);

    useEffect(() => {
        if (typeof BroadcastChannel === 'undefined') {
            return;
        }
        const channel = new BroadcastChannel(`leh-draft-collab-${caseId}`);
        channelRef.current = channel;

        const handleMessage = (event: MessageEvent) => {
            const data = event.data as {
                type: string;
                caseId: string;
                clientId: string;
                savedAt?: string;
                html?: string;
                comments?: DraftCommentSnapshot[];
                changeLog?: DraftChangeLogEntry[];
                timestamp?: number;
            };
            if (!data || data.caseId !== caseId || data.clientId === clientIdRef.current) {
                return;
            }
            if (data.type === 'presence') {
                setCollabStatus('다른 사용자가 편집 중');
            }
            if (data.type === 'save') {
                setCollabStatus('동료가 방금 저장했습니다');
                setTimeout(() => setCollabStatus(null), 4000);
            }
            if (data.type === 'content-update' && data.timestamp) {
                if (data.timestamp <= lastRemoteUpdateRef.current) {
                    return;
                }
                lastRemoteUpdateRef.current = data.timestamp;
                const sanitized = sanitizeDraftHtml(data.html || '');
                setEditorHtml(sanitized);
                setComments(data.comments || []);
                setChangeLog(data.changeLog || []);
                persistCurrentState(sanitized, undefined, undefined, data.comments || [], data.changeLog || []);
                lastImportedDraftRef.current = sanitized;
                setCollabStatus('동료가 편집 내용을 동기화했습니다.');
                setTimeout(() => setCollabStatus(null), 4000);
            }
        };

        channel.addEventListener('message', handleMessage);
        channel.postMessage({ type: 'presence', caseId, clientId: clientIdRef.current });
        const presenceInterval = window.setInterval(() => {
            channel.postMessage({ type: 'presence', caseId, clientId: clientIdRef.current });
        }, 15000);

        return () => {
            channel.removeEventListener('message', handleMessage);
            channel.close();
            window.clearInterval(presenceInterval);
        };
    }, [caseId]);

    useEffect(() => {
        if (!channelRef.current) {
            return;
        }

        if (collabSyncTimerRef.current) {
            clearTimeout(collabSyncTimerRef.current);
        }

        const timeout = window.setTimeout(() => {
            channelRef.current?.postMessage({
                type: 'content-update',
                caseId,
                clientId: clientIdRef.current,
                html: editorHtml,
                comments,
                changeLog,
                timestamp: Date.now(),
            });
        }, 500);
        collabSyncTimerRef.current = timeout;

        return () => {
            if (collabSyncTimerRef.current) {
                clearTimeout(collabSyncTimerRef.current);
            }
        };
    }, [caseId, editorHtml, comments, changeLog]);

    const handleFormat = (command: string) => {
        document.execCommand(command, false, undefined);
    };

    const handleDownload = async (format: DraftDownloadFormat) => {
        if (!onDownload) return;

        setIsExporting(true);
        setExportingFormat(format);
        setExportToast(null);

        try {
            const result = await onDownload({ format, content: editorHtml });

            if (result) {
                if (result.success) {
                    setExportToast({
                        type: 'success',
                        message: `${format.toUpperCase()} 파일이 다운로드되었습니다.`,
                        filename: result.filename,
                    });
                } else {
                    setExportToast({
                        type: 'error',
                        message: result.error || '다운로드에 실패했습니다.',
                    });
                }
            }
        } catch (error) {
            setExportToast({
                type: 'error',
                message: error instanceof Error ? error.message : '다운로드 중 오류가 발생했습니다.',
            });
        } finally {
            setIsExporting(false);
            setExportingFormat(null);

            // Auto-dismiss toast after 5 seconds
            setTimeout(() => setExportToast(null), 5000);
        }
    };

    const handleEditorClick = (e: React.MouseEvent<HTMLDivElement>) => {
        const target = e.target as HTMLElement;
        const evidenceId = target.getAttribute('data-evidence-id');

        if (evidenceId) {
            setSelectedEvidenceId(evidenceId);
            setIsTraceabilityPanelOpen(true);
        }
    };

    const insertTrackChangeMarkup = (text: string) => {
        const safeText = DOMPurify.sanitize(text, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] });
        const changeId = generateId();
        document.execCommand(
            'insertHTML',
            false,
            `<span class="track-change-insert" data-change-id="${changeId}">${safeText}</span>`
        );
        const entry: DraftChangeLogEntry = {
            id: changeId,
            action: 'insert',
            snippet: safeText,
            createdAt: new Date().toISOString(),
        };
        setChangeLog((prev) => {
            const updated = [entry, ...prev].slice(0, CHANGELOG_LIMIT);
            persistCurrentState(editorRef.current?.innerHTML || editorHtml, undefined, undefined, undefined, updated);
            return updated;
        });
    };

    const handleBeforeInput = (event: React.FormEvent<HTMLDivElement>) => {
        if (!isTrackChangesEnabled) {
            return;
        }
        const nativeEvent = event.nativeEvent as InputEvent;
        if (!nativeEvent || nativeEvent.isComposing) {
            return;
        }
        if (nativeEvent.inputType === 'insertText' && nativeEvent.data) {
            event.preventDefault();
            insertTrackChangeMarkup(nativeEvent.data);
            const html = sanitizeDraftHtml(editorRef.current?.innerHTML || editorHtml);
            setEditorHtml(html);
            persistCurrentState(html);
        }
    };

    const handleEditorInput = (event: React.FormEvent<HTMLDivElement>) => {
        const html = sanitizeDraftHtml((event.currentTarget as HTMLDivElement).innerHTML);
        setEditorHtml(html);

        const inputEvent = event.nativeEvent as InputEvent;
        if (isTrackChangesEnabled && inputEvent) {
            if (inputEvent.inputType === 'insertText') {
                persistCurrentState(html);
                return;
            }
            const snippet = (inputEvent.data || window.getSelection()?.toString() || '변경됨').trim() || '변경됨';
            const action: 'insert' | 'delete' | 'edit' = inputEvent.inputType?.startsWith('delete')
                ? 'delete'
                : inputEvent.inputType?.includes('format')
                    ? 'edit'
                    : 'insert';
            const entry: DraftChangeLogEntry = {
                id: generateId(),
                action,
                snippet,
                createdAt: new Date().toISOString(),
            };
            setChangeLog((prev) => {
                const updated = [entry, ...prev].slice(0, CHANGELOG_LIMIT);
                persistCurrentState(html, undefined, undefined, undefined, updated);
                return updated;
            });
        } else {
            persistCurrentState(html);
        }
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
            channelRef.current?.postMessage({
                type: 'save',
                caseId,
                clientId: clientIdRef.current,
                savedAt: new Date().toISOString(),
            });
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

    const handleApplyTemplate = (templateContent: string) => {
        const content = sanitizeDraftHtml(templateContent);
        setEditorHtml(content);
        persistCurrentState(content);
        setIsTemplateModalOpen(false);
    };

    const handleInsertCitation = (citation: DraftCitation) => {
        const markup = `<span class="evidence-ref" data-evidence-id="${citation.evidenceId}">[증거: ${citation.title}]</span>`;
        document.execCommand('insertHTML', false, markup);
        const html = sanitizeDraftHtml(editorRef.current?.innerHTML || editorHtml);
        setEditorHtml(html);
        persistCurrentState(html);
        setIsCitationModalOpen(false);
    };

    const wrapSelectionWithSpan = (className: string, attributes: Record<string, string>) => {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
            return false;
        }
        const range = selection.getRangeAt(0);
        const span = document.createElement('span');
        span.className = className;
        Object.entries(attributes).forEach(([key, value]) => span.setAttribute(key, value));
        try {
            range.surroundContents(span);
        } catch {
            const selectedHtml = selection.toString();
            if (!selectedHtml) return false;
            const safeSelection = DOMPurify.sanitize(selectedHtml, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] });
            document.execCommand(
                'insertHTML',
                false,
                `<span class="${className}" ${Object.entries(attributes)
                    .map(([key, value]) => `${key}="${value}"`)
                    .join(' ')}>${safeSelection}</span>`
            );
        }
        selection.removeAllRanges();
        const html = sanitizeDraftHtml(editorRef.current?.innerHTML || editorHtml);
        setEditorHtml(html);
        persistCurrentState(html);
        return true;
    };

    const handleAddComment = () => {
        const selection = window.getSelection();
        const quote = selection?.toString().trim();
        if (!quote) {
            setSaveMessage('코멘트 추가 전 텍스트를 선택하세요.');
            setTimeout(() => setSaveMessage(null), 2500);
            return;
        }
        if (!newCommentText.trim()) {
            setSaveMessage('코멘트 내용을 입력하세요.');
            setTimeout(() => setSaveMessage(null), 2500);
            return;
        }
        const comment: DraftCommentSnapshot = {
            id: generateId(),
            quote,
            text: newCommentText.trim(),
            createdAt: new Date().toISOString(),
            resolved: false,
        };
        wrapSelectionWithSpan('comment-highlight', { 'data-comment-id': comment.id });
        setComments((prev) => {
            const updated = [comment, ...prev];
            persistCurrentState(editorRef.current?.innerHTML || editorHtml, undefined, undefined, updated);
            return updated;
        });
        setNewCommentText('');
    };

    const handleToggleCommentResolved = (commentId: string) => {
        setComments((prev) => {
            const updated = prev.map((comment) =>
                comment.id === commentId ? { ...comment, resolved: !comment.resolved } : comment
            );
            const editorEl = editorRef.current;
            if (editorEl) {
                const highlights = editorEl.querySelectorAll(`[data-comment-id="${commentId}"]`);
                const resolved = updated.find((c) => c.id === commentId)?.resolved;
                highlights.forEach((node) => {
                    if (resolved) {
                        node.classList.add('comment-highlight-resolved');
                    } else {
                        node.classList.remove('comment-highlight-resolved');
                    }
                });
                const html = sanitizeDraftHtml(editorEl.innerHTML);
                setEditorHtml(html);
                persistCurrentState(html, undefined, undefined, updated);
            } else {
                persistCurrentState(editorHtml, undefined, undefined, updated);
            }
            return updated;
        });
    };

    const handleTrackChangeToggle = () => {
        setIsTrackChangesEnabled((prev) => !prev);
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
                    <div className="flex flex-wrap items-center gap-2">
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
                        <button
                            type="button"
                            onClick={() => setIsTemplateModalOpen(true)}
                            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-secondary hover:border-accent hover:text-accent transition-colors"
                        >
                            <LayoutTemplate className="w-4 h-4" />
                            템플릿 적용
                        </button>
                        <button
                            type="button"
                            onClick={() => setIsCitationModalOpen(true)}
                            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2 text-sm font-medium text-secondary hover:border-accent hover:text-accent transition-colors"
                        >
                            <Quote className="w-4 h-4" />
                            증거 인용 삽입
                        </button>
                        <button
                            type="button"
                            onClick={handleTrackChangeToggle}
                            className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors ${
                                isTrackChangesEnabled
                                    ? 'border-accent bg-accent/10 text-secondary'
                                    : 'border-gray-200 bg-white text-secondary hover:border-accent hover:text-accent'
                            }`}
                        >
                            <GitBranch className="w-4 h-4" />
                            변경 추적 {isTrackChangesEnabled ? 'ON' : 'OFF'}
                        </button>
                        {saveMessage && <span className="text-xs text-accent">{saveMessage}</span>}
                    </div>
                    <div className="inline-flex flex-col text-xs text-gray-500 items-end gap-1" data-testid="autosave-indicator">
                        <div className="inline-flex items-center">
                            <Clock3 className="w-4 h-4 mr-1" />
                            {formatAutosaveStatus(lastSavedAt)}
                        </div>
                        <span>페이지 {pageCount}</span>
                        {collabStatus && (
                            <span className="inline-flex items-center gap-1 text-secondary">
                                <Users className="w-4 h-4" />
                                {collabStatus}
                            </span>
                        )}
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
                        <button
                            type="button"
                            aria-label="List"
                            onClick={() => handleFormat('insertUnorderedList')}
                            className="p-1 hover:bg-gray-200 rounded transition-colors"
                        >
                            <List className="w-4 h-4 text-neutral-700" />
                        </button>
                    </div>
                    <div className="inline-flex items-center gap-2">
                        <button
                            type="button"
                            onClick={() => handleDownload('docx')}
                            disabled={isExporting}
                            className="inline-flex items-center gap-1 text-xs font-medium text-secondary hover:text-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isExporting && exportingFormat === 'docx' ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Download className="w-4 h-4" />
                            )}
                            DOCX
                        </button>
                        <button
                            type="button"
                            onClick={() => handleDownload('pdf')}
                            disabled={isExporting}
                            className="inline-flex items-center gap-1 text-xs font-medium text-secondary hover:text-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isExporting && exportingFormat === 'pdf' ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Download className="w-4 h-4" />
                            )}
                            PDF
                        </button>
                        <button
                            type="button"
                            onClick={() => handleDownload('hwp')}
                            disabled={isExporting}
                            className="inline-flex items-center gap-1 text-xs font-medium text-secondary hover:text-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isExporting && exportingFormat === 'hwp' ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                                <Download className="w-4 h-4" />
                            )}
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
                    onBeforeInput={handleBeforeInput}
                    onInput={handleEditorInput}
                    className="w-full min-h-[320px] bg-transparent p-6 text-gray-800 leading-relaxed focus:outline-none overflow-auto cursor-pointer [&_.evidence-ref]:underline [&_.evidence-ref]:text-secondary [&_.evidence-ref]:cursor-pointer [&_.evidence-ref:hover]:text-accent [&_.evidence-ref]:decoration-dotted"
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

            <div className="border-t border-gray-100 pt-4 space-y-6">
                <div>
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

                <div className="rounded-2xl border border-gray-100 bg-white p-4 space-y-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <MessageSquare className="w-4 h-4 text-secondary" />
                            <h4 className="text-sm font-semibold text-neutral-700">코멘트</h4>
                        </div>
                        <span className="text-xs text-gray-400">선택한 텍스트에 코멘트를 남길 수 있습니다.</span>
                    </div>
                    <textarea
                        aria-label="코멘트 작성"
                        className="w-full rounded-xl border border-gray-200 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                        placeholder="선택한 부분에 대한 코멘트를 입력하세요."
                        value={newCommentText}
                        onChange={(event) => setNewCommentText(event.target.value)}
                    />
                    <button
                        type="button"
                        onClick={handleAddComment}
                        className="btn-secondary text-sm px-4 py-2"
                    >
                        코멘트 추가
                    </button>
                    <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
                        {comments.length === 0 && <p className="text-sm text-gray-400">아직 코멘트가 없습니다.</p>}
                        {comments.map((comment) => (
                            <div key={comment.id} className="rounded-xl border border-gray-100 bg-neutral-50/80 p-3 space-y-1">
                                <p className="text-xs text-gray-400">{formatTimestamp(comment.createdAt)}</p>
                                <p className="text-xs text-secondary">&ldquo;{comment.quote}&rdquo;</p>
                                <p className="text-sm text-neutral-700">{comment.text}</p>
                                <button
                                    type="button"
                                    onClick={() => handleToggleCommentResolved(comment.id)}
                                    className={`text-xs font-medium ${
                                        comment.resolved ? 'text-accent' : 'text-secondary'
                                    }`}
                                >
                                    {comment.resolved ? '해결됨' : '해결 표시'}
                                </button>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="rounded-2xl border border-gray-100 bg-white p-4 space-y-3">
                    <div className="flex items-center gap-2">
                        <GitBranch className="w-4 h-4 text-secondary" />
                        <h4 className="text-sm font-semibold text-neutral-700">변경 추적</h4>
                    </div>
                    <div className="space-y-3 max-h-48 overflow-y-auto pr-1">
                        {changeLog.length === 0 && <p className="text-sm text-gray-400">기록된 변경 사항이 없습니다.</p>}
                        {changeLog.map((entry) => (
                            <div key={entry.id} className="rounded-xl border border-gray-100 bg-neutral-50/80 p-3">
                                <p className="text-xs text-gray-400">{formatTimestamp(entry.createdAt)}</p>
                                <p className="text-sm font-semibold text-gray-900">{entry.action.toUpperCase()}</p>
                                <p className="text-sm text-neutral-700 truncate">{entry.snippet}</p>
                            </div>
                        ))}
                    </div>
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

            {isTemplateModalOpen && (
                <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 px-4" role="dialog" aria-label="템플릿 선택">
                    <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-gray-900">법률 문서 템플릿</h3>
                            <button
                                type="button"
                                aria-label="템플릿 모달 닫기"
                                onClick={() => setIsTemplateModalOpen(false)}
                                className="rounded-full p-2 text-gray-500 hover:bg-gray-100"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                        <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
                            {DOCUMENT_TEMPLATES.map((template) => (
                                <div key={template.id} className="rounded-xl border border-gray-200 p-4 bg-neutral-50/40">
                                    <p className="text-sm font-semibold text-gray-900">{template.name}</p>
                                    <p className="text-xs text-gray-500 mb-3">{template.description}</p>
                                    <button
                                        type="button"
                                        onClick={() => handleApplyTemplate(template.content)}
                                        className="btn-secondary text-xs px-3 py-1.5"
                                    >
                                        템플릿 적용
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {isCitationModalOpen && (
                <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 px-4" role="dialog" aria-label="증거 인용 삽입">
                    <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-gray-900">증거 인용 선택</h3>
                            <button
                                type="button"
                                aria-label="증거 인용 모달 닫기"
                                onClick={() => setIsCitationModalOpen(false)}
                                className="rounded-full p-2 text-gray-500 hover:bg-gray-100"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                        <div className="space-y-3 max-h-[60vh] overflow-y-auto pr-1">
                            {citations.length === 0 && <p className="text-sm text-gray-500">현재 인용 가능한 증거가 없습니다.</p>}
                            {citations.map((citation) => (
                                <button
                                    key={citation.evidenceId}
                                    type="button"
                                    onClick={() => handleInsertCitation(citation)}
                                    className="w-full rounded-xl border border-gray-200 bg-white p-3 text-left hover:border-accent focus:outline-none focus:ring-2 focus:ring-accent"
                                >
                                    <p className="text-sm font-semibold text-gray-900">{citation.title}</p>
                                    <p className="text-xs text-gray-500 truncate">{citation.quote}</p>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Export Toast Notification */}
            {exportToast && (
                <div
                    className={`fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-xl px-4 py-3 shadow-lg transition-all duration-300 ${
                        exportToast.type === 'success'
                            ? 'bg-green-50 border border-green-200 text-green-800'
                            : 'bg-red-50 border border-red-200 text-red-800'
                    }`}
                    role="alert"
                    aria-live="polite"
                >
                    {exportToast.type === 'success' ? (
                        <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                        <AlertCircle className="w-5 h-5 text-red-600" />
                    )}
                    <div className="flex flex-col">
                        <span className="text-sm font-medium">{exportToast.message}</span>
                        {exportToast.filename && (
                            <span className="text-xs opacity-75">{exportToast.filename}</span>
                        )}
                    </div>
                    <button
                        type="button"
                        onClick={() => setExportToast(null)}
                        className="ml-2 rounded-full p-1 hover:bg-black/5 transition-colors"
                        aria-label="알림 닫기"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}
        </section>
    );
}
