import { Loader2, FileText, Download, Sparkles, Bold, Italic, Underline, List } from 'lucide-react';
import { DraftCitation } from '@/types/draft';
import { DraftDownloadFormat } from '@/services/documentService';

interface DraftPreviewPanelProps {
    draftText: string;
    citations: DraftCitation[];
    isGenerating: boolean;
    hasExistingDraft: boolean;
    onGenerate: () => void;
    onDownload?: (format?: DraftDownloadFormat) => void;
}

export default function DraftPreviewPanel({
    draftText,
    citations,
    isGenerating,
    hasExistingDraft,
    onGenerate,
    onDownload,
}: DraftPreviewPanelProps) {
    const buttonLabel = hasExistingDraft ? '초안 재생성' : '초안 생성';

    const handleFormat = (command: string) => {
        document.execCommand(command, false, undefined);
    };

    const handleDownload = (format: DraftDownloadFormat) => {
        if (!onDownload) return;
        onDownload(format);
    };

    return (
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 space-y-6" aria-label="Draft preview">
            <div className="flex items-start justify-between gap-4">
                <div>
                    <p className="text-sm text-gray-600 leading-relaxed">
                        이 문서는 AI가 생성한 초안이며, 최종 책임은 변호사에게 있습니다.
                    </p>
                    <p className="text-xs text-gray-400 mt-2">
                        실제 제출 전 반드시 모든 내용을 검토하고 사실 관계를 확인해 주세요.
                    </p>
                </div>
                <div className="inline-flex items-center text-xs uppercase tracking-wide text-deep-trust-blue font-semibold">
                    <Sparkles className="w-4 h-4 mr-1 text-accent" />
                    AI Draft
                </div>
            </div>

            <div
                data-testid="draft-toolbar-panel"
                className="flex items-center justify-between bg-calm-grey/70 border border-gray-200 rounded-xl px-4 py-2 text-xs text-gray-500 tracking-wide"
            >
                <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-deep-trust-blue" />
                    <div className="h-4 w-px bg-gray-300 mx-2" />
                    <button
                        type="button"
                        aria-label="Bold"
                        onClick={() => handleFormat('bold')}
                        className="p-1 hover:bg-gray-200 rounded transition-colors"
                    >
                        <Bold className="w-4 h-4 text-gray-700" />
                    </button>
                    <button
                        type="button"
                        aria-label="Italic"
                        onClick={() => handleFormat('italic')}
                        className="p-1 hover:bg-gray-200 rounded transition-colors"
                    >
                        <Italic className="w-4 h-4 text-gray-700" />
                    </button>
                    <button
                        type="button"
                        aria-label="Underline"
                        onClick={() => handleFormat('underline')}
                        className="p-1 hover:bg-gray-200 rounded transition-colors"
                    >
                        <Underline className="w-4 h-4 text-gray-700" />
                    </button>
                    <div className="h-4 w-px bg-gray-300 mx-2" />
                    <button type="button" aria-label="List" className="p-1 hover:bg-gray-200 rounded transition-colors">
                        <List className="w-4 h-4 text-gray-700" />
                    </button>
                </div>
                <div className="inline-flex items-center gap-2">
                    <button
                        type="button"
                        onClick={() => handleDownload('docx')}
                        className="inline-flex items-center gap-1 text-xs font-medium text-deep-trust-blue hover:text-accent transition-colors"
                    >
                        <Download className="w-4 h-4" />
                        DOCX
                    </button>
                    <button
                        type="button"
                        onClick={() => handleDownload('hwp')}
                        className="inline-flex items-center gap-1 text-xs font-medium text-deep-trust-blue hover:text-accent transition-colors"
                    >
                        <Download className="w-4 h-4" />
                        HWP
                    </button>
                </div>
            </div>

            <div
                data-testid="draft-editor-surface"
                data-zen-mode="true"
                className="relative rounded-2xl border border-gray-100 bg-white shadow-inner focus-within:border-deep-trust-blue transition-colors"
            >
                <div
                    data-testid="draft-editor-content"
                    contentEditable
                    suppressContentEditableWarning
                    aria-label="Draft content"
                    className="w-full min-h-[320px] bg-transparent p-6 text-gray-800 leading-relaxed focus:outline-none resize-none placeholder:text-gray-400 overflow-auto"
                    dangerouslySetInnerHTML={{ __html: draftText }}
                />
                <div className="absolute top-4 right-6 text-xs text-gray-400">자동 저장 준비 중</div>
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
                    최신 초안 기준 <span className="font-semibold text-deep-trust-blue">실제 증거 인용</span> {citations.length}건
                </div>
            </div>

            <div className="border-t border-gray-100 pt-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Citations</h4>
                <div className="space-y-3">
                    {citations.map((citation) => (
                        <div key={citation.evidenceId} className="rounded-lg border border-gray-100 bg-calm-grey/60 p-3">
                            <p className="text-xs text-gray-500 mb-1">{citation.title}</p>
                            <p className="text-sm text-gray-700 leading-relaxed">&ldquo;{citation.quote}&rdquo;</p>
                        </div>
                    ))}
                    {citations.length === 0 && (
                        <p className="text-sm text-gray-400">아직 연결된 증거가 없습니다.</p>
                    )}
                </div>
            </div>
        </section>
    );
}
