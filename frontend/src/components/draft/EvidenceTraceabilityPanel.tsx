/**
 * EvidenceTraceabilityPanel Component
 *
 * Plan 3.17 - AI Traceability Panel
 * Displays source evidence and metadata for AI-generated draft content.
 *
 * Features:
 * - Shows original evidence content with highlighted citations
 * - Displays evidence metadata (type, speaker, labels)
 * - Shows AI generation context (prompt info)
 * - Side panel design with smooth animations
 *
 * Design: Calm Control (UI_UX_DESIGN.md)
 * - Deep Trust Blue (#2C3E50) for headers
 * - Calm Grey (#F8F9FA) for backgrounds
 * - Yellow highlight for cited text
 */

import { useEffect, useState } from 'react';
import { X, FileText, User, Tag, Clock, Sparkles } from 'lucide-react';

interface EvidenceTraceabilityPanelProps {
    isOpen: boolean;
    evidenceId: string | null;
    onClose: () => void;
}

interface EvidenceDetail {
    id: string;
    filename: string;
    type: 'text' | 'audio' | 'video' | 'image' | 'pdf';
    content: string;
    speaker?: string;
    timestamp?: string;
    labels?: string[];
    aiPrompt?: string;
}

export default function EvidenceTraceabilityPanel({
    isOpen,
    evidenceId,
    onClose,
}: EvidenceTraceabilityPanelProps) {
    const [evidence, setEvidence] = useState<EvidenceDetail | null>(null);

    useEffect(() => {
        // ESC key handler
        const handleEscape = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose();
            }
        };

        if (isOpen) {
            document.addEventListener('keydown', handleEscape);
        }

        return () => {
            document.removeEventListener('keydown', handleEscape);
        };
    }, [isOpen, onClose]);

    useEffect(() => {
        // Fetch evidence details when evidenceId changes
        if (evidenceId) {
            // Mock data for testing - will be replaced with actual API call
            const mockEvidence: EvidenceDetail = {
                id: evidenceId,
                filename: '녹취록_20240501.mp3',
                type: 'audio',
                content: '피고가 원고에게 "너는 쓸모없는 사람이야"라고 반복적으로 말했습니다.',
                speaker: '원고',
                timestamp: '2024-05-01T14:30:00Z',
                labels: ['폭언', '계속적 불화'],
                aiPrompt: 'Summarize the following evidence and identify fault grounds according to Article 840 of the Civil Act.',
            };
            setEvidence(mockEvidence);
        }
    }, [evidenceId]);

    if (!isOpen) {
        return null;
    }

    return (
        <aside
            data-testid="traceability-panel"
            role="dialog"
            aria-label="Evidence Traceability Panel"
            className="fixed right-0 top-0 h-full w-96 max-w-md bg-white shadow-2xl z-50 transition-opacity duration-300 ease-in-out overflow-y-auto"
        >
            {/* Header */}
            <header className="sticky top-0 bg-deep-trust-blue text-white px-6 py-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-accent" />
                    <h2 className="text-lg font-semibold">AI 근거 추적</h2>
                </div>
                <button
                    onClick={onClose}
                    aria-label="닫기"
                    className="p-1 hover:bg-white/20 rounded-lg transition-colors"
                >
                    <X className="w-5 h-5" />
                </button>
            </header>

            {/* Content */}
            {evidence ? (
                <div className="p-6 space-y-6">
                    {/* Evidence Metadata */}
                    <section>
                        <h3 className="text-sm font-semibold text-secondary mb-3">증거 정보</h3>
                        <div className="space-y-2 bg-neutral-50 rounded-lg p-4">
                            <div className="flex items-center gap-2 text-sm">
                                <FileText className="w-4 h-4 text-gray-500" />
                                <span className="text-neutral-600">파일명:</span>
                                <span className="font-medium text-gray-800">{evidence.filename}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm">
                                <Tag className="w-4 h-4 text-gray-500" />
                                <span className="text-neutral-600">유형:</span>
                                <span className="font-medium text-gray-800">{evidence.type}</span>
                            </div>
                            {evidence.speaker && (
                                <div className="flex items-center gap-2 text-sm">
                                    <User className="w-4 h-4 text-gray-500" />
                                    <span className="text-neutral-600">화자:</span>
                                    <span className="font-medium text-gray-800">{evidence.speaker}</span>
                                </div>
                            )}
                            {evidence.timestamp && (
                                <div className="flex items-center gap-2 text-sm">
                                    <Clock className="w-4 h-4 text-gray-500" />
                                    <span className="text-neutral-600">시점:</span>
                                    <span className="font-medium text-gray-800">
                                        {new Date(evidence.timestamp).toLocaleString('ko-KR')}
                                    </span>
                                </div>
                            )}
                            {evidence.labels && evidence.labels.length > 0 && (
                                <div className="flex items-start gap-2 text-sm">
                                    <Tag className="w-4 h-4 text-gray-500 mt-0.5" />
                                    <span className="text-neutral-600">라벨:</span>
                                    <div className="flex flex-wrap gap-1">
                                        {evidence.labels.map((label) => (
                                            <span
                                                key={label}
                                                className="px-2 py-0.5 bg-accent/10 text-accent text-xs rounded-full"
                                            >
                                                {label}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </section>

                    {/* Original Evidence Content with Highlight */}
                    <section>
                        <h3 className="text-sm font-semibold text-secondary mb-3">원본 증거</h3>
                        <div className="bg-neutral-50 rounded-lg p-4">
                            <p
                                data-testid="highlighted-evidence"
                                className="text-sm text-gray-800 leading-relaxed bg-yellow-200 p-2 rounded"
                            >
                                {evidence.content}
                            </p>
                        </div>
                    </section>

                    {/* AI Generation Context */}
                    <section>
                        <h3 className="text-sm font-semibold text-secondary mb-3">AI 근거 데이터</h3>
                        <div className="bg-neutral-50 rounded-lg p-4 space-y-3">
                            <div>
                                <h4 className="text-xs font-medium text-neutral-600 mb-1">사용된 프롬프트</h4>
                                <p className="text-xs text-neutral-700 leading-relaxed">
                                    {evidence.aiPrompt || '프롬프트 정보 없음'}
                                </p>
                            </div>
                            <div>
                                <h4 className="text-xs font-medium text-neutral-600 mb-1">생성 모델</h4>
                                <p className="text-xs text-neutral-700">GPT-4o</p>
                            </div>
                            <div>
                                <h4 className="text-xs font-medium text-neutral-600 mb-1">증거 ID</h4>
                                <p className="text-xs font-mono text-neutral-700">{evidence.id}</p>
                            </div>
                        </div>
                    </section>

                    {/* Disclaimer */}
                    <section className="border-t border-gray-200 pt-4">
                        <p className="text-xs text-gray-500 leading-relaxed">
                            이 패널은 AI가 생성한 초안의 근거가 된 실제 증거를 보여줍니다.
                            최종 문서 작성 시 반드시 원본 증거를 직접 확인하시기 바랍니다.
                        </p>
                    </section>
                </div>
            ) : (
                <div className="p-6 text-center text-gray-500">
                    <p className="text-sm">증거 정보를 불러오는 중...</p>
                </div>
            )}
        </aside>
    );
}
