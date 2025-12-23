'use client';

/**
 * MainWorkspace - Central Content Area
 * 014-ui-settings-completion Feature
 *
 * Main workspace containing:
 * - Fact summary (with editor)
 * - Issue analysis
 * - Draft generation section
 */

import { ReactNode } from 'react';
import { FileText, Scale, Sparkles, Loader2 } from 'lucide-react';

interface WorkspaceSectionProps {
  id: string;
  title: string;
  icon: ReactNode;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
  className?: string;
}

function WorkspaceSection({
  title,
  icon,
  description,
  children,
  actions,
  className = '',
}: WorkspaceSectionProps) {
  return (
    <section className={`bg-white dark:bg-neutral-800 rounded-lg border border-gray-200 dark:border-neutral-700 shadow-sm ${className}`}>
      {/* Section Header - LDS2 Compact (32px height) */}
      <div className="px-3 py-2 border-b border-gray-200 dark:border-neutral-700 bg-gray-50 dark:bg-neutral-850">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <span className="text-[var(--color-primary)]">{icon}</span>
            <div>
              <h3 className="font-semibold text-xs text-[var(--color-text-primary)]">{title}</h3>
              {description && (
                <p className="text-[10px] text-[var(--color-text-secondary)]">{description}</p>
              )}
            </div>
          </div>
          {actions && <div className="flex items-center gap-1.5">{actions}</div>}
        </div>
      </div>
      {/* Section Content - LDS2 Compact */}
      <div className="p-3">
        {children}
      </div>
    </section>
  );
}

interface MainWorkspaceProps {
  // Fact Summary
  factSummaryContent: ReactNode;
  // Issue Analysis (hidden by default as per Task 6)
  analysisContent?: ReactNode;
  showAnalysis?: boolean;
  // Draft Generation
  onGenerateDraft: () => void;
  hasDraft: boolean;
  isGeneratingDraft: boolean;
  draftContent?: ReactNode;
}

export function MainWorkspace({
  factSummaryContent,
  analysisContent,
  showAnalysis = false, // Hidden by default as per Task 6
  onGenerateDraft,
  hasDraft,
  isGeneratingDraft,
  draftContent,
}: MainWorkspaceProps) {
  return (
    <div className="flex flex-col h-full space-y-3">
      {/* Fact Summary Section - LDS2 Compact */}
      <WorkspaceSection
        id="fact-summary"
        title="사실관계 요약"
        icon={<FileText className="w-4 h-4" />}
        description="증거 자료를 기반으로 정리된 사건 사실관계"
        className="flex-1"
      >
        <div className="min-h-[150px]">
          {factSummaryContent}
        </div>
      </WorkspaceSection>

      {/* Issue Analysis Section - Hidden by default (Task 6) */}
      {showAnalysis && analysisContent && (
        <WorkspaceSection
          id="analysis"
          title="쟁점 분석"
          icon={<Scale className="w-4 h-4" />}
          description="핵심 쟁점 및 법률적 판단 근거"
        >
          {analysisContent}
        </WorkspaceSection>
      )}

      {/* Draft Generation - LDS2 Compact Action Bar */}
      <div className="flex justify-end pt-1.5 border-t border-gray-200 dark:border-neutral-700">
        <button
          onClick={onGenerateDraft}
          disabled={isGeneratingDraft}
          className="inline-flex items-center px-3 py-1.5 text-xs font-medium bg-[var(--color-primary)] text-white rounded-md shadow-sm
            hover:bg-[var(--color-primary-hover)] active:scale-[0.98]
            transition-all duration-100 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGeneratingDraft ? (
            <>
              <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
              생성 중...
            </>
          ) : (
            <>
              <Sparkles className="w-3.5 h-3.5 mr-1.5" />
              초안 생성
            </>
          )}
        </button>
      </div>

      {/* Draft Content (if exists) */}
      {hasDraft && draftContent && (
        <div className="mt-3">
          {draftContent}
        </div>
      )}
    </div>
  );
}

export default MainWorkspace;
