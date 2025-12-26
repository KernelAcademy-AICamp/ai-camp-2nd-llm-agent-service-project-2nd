/**
 * Pipeline Progress Indicator Component
 *
 * Visualizes the 4-stage AI processing pipeline for evidence:
 * 1. 수집 (Collection) - Evidence uploaded
 * 2. 분석 (Analysis) - AI processing underway
 * 3. 구조화 (Structuring) - Data organized
 * 4. 생성 (Generation) - Draft ready
 *
 * Issue #423: Pipeline progress visualization
 */

'use client';

import { useMemo } from 'react';
import { CheckCircle2, Circle, Loader2, Upload, Brain, Network, FileText } from 'lucide-react';

export type PipelineStage = 'collection' | 'analysis' | 'structuring' | 'generation';
export type PipelineStatus = 'pending' | 'processing' | 'completed' | 'error';

export interface PipelineStageInfo {
  id: PipelineStage;
  label: string;
  description: string;
  status: PipelineStatus;
}

export interface PipelineProgressIndicatorProps {
  /** Number of total evidence items */
  totalEvidence: number;
  /** Number of completed (processed) evidence items */
  completedEvidence: number;
  /** Number of items currently processing */
  processingEvidence: number;
  /** Whether a draft has been generated */
  hasDraft: boolean;
  /** Whether relations/parties have been extracted */
  hasRelations: boolean;
  /** Compact mode for smaller displays */
  compact?: boolean;
}

/**
 * Calculate the current pipeline status based on evidence states
 */
export function calculatePipelineStatus(props: PipelineProgressIndicatorProps): PipelineStageInfo[] {
  const { totalEvidence, completedEvidence, processingEvidence, hasDraft, hasRelations } = props;

  const collectionStatus: PipelineStatus = totalEvidence > 0 ? 'completed' : 'pending';

  const analysisStatus: PipelineStatus =
    processingEvidence > 0 ? 'processing' :
    completedEvidence > 0 ? 'completed' :
    totalEvidence > 0 ? 'pending' : 'pending';

  const structuringStatus: PipelineStatus =
    hasRelations ? 'completed' :
    completedEvidence > 0 ? 'processing' : 'pending';

  const generationStatus: PipelineStatus =
    hasDraft ? 'completed' :
    structuringStatus === 'completed' ? 'pending' : 'pending';

  return [
    {
      id: 'collection',
      label: '수집',
      description: '증거 업로드',
      status: collectionStatus,
    },
    {
      id: 'analysis',
      label: '분석',
      description: 'AI 분석',
      status: analysisStatus,
    },
    {
      id: 'structuring',
      label: '구조화',
      description: '데이터 정리',
      status: structuringStatus,
    },
    {
      id: 'generation',
      label: '생성',
      description: '초안 작성',
      status: generationStatus,
    },
  ];
}

const stageIcons: Record<PipelineStage, typeof Upload> = {
  collection: Upload,
  analysis: Brain,
  structuring: Network,
  generation: FileText,
};

const statusColors: Record<PipelineStatus, { bg: string; text: string; border: string }> = {
  pending: {
    bg: 'bg-gray-100 dark:bg-neutral-800',
    text: 'text-gray-400 dark:text-neutral-500',
    border: 'border-gray-200 dark:border-neutral-700',
  },
  processing: {
    bg: 'bg-primary-light dark:bg-primary-light/10',
    text: 'text-primary dark:text-primary',
    border: 'border-primary-light dark:border-primary-light/30',
  },
  completed: {
    bg: 'bg-success-light dark:bg-success-light/10',
    text: 'text-success dark:text-success',
    border: 'border-success-light dark:border-success-light/30',
  },
  error: {
    bg: 'bg-error-light dark:bg-error-light/10',
    text: 'text-error dark:text-error',
    border: 'border-error-light dark:border-error-light/30',
  },
};

function StageIcon({ stage, status }: { stage: PipelineStage; status: PipelineStatus }) {
  const IconComponent = stageIcons[stage];
  const colors = statusColors[status];

  if (status === 'processing') {
    return (
      <div className="relative flex items-center justify-center">
        <Loader2 className={`w-4 h-4 ${colors.text} animate-spin`} />
        <div className={`absolute w-4 h-4 rounded-full ${colors.bg} animate-pulse-premium opacity-50`} />
      </div>
    );
  }

  if (status === 'completed') {
    return <CheckCircle2 className={`w-4 h-4 ${colors.text}`} />;
  }

  return <IconComponent className={`w-4 h-4 ${colors.text}`} />;
}

export function PipelineProgressIndicator(props: PipelineProgressIndicatorProps) {
  const { compact = false } = props;

  const stages = useMemo(() => calculatePipelineStatus(props), [props]);

  const completedCount = stages.filter(s => s.status === 'completed').length;
  const progressPercent = Math.round((completedCount / stages.length) * 100);

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        {stages.map((stage, index) => {
          const colors = statusColors[stage.status];
          return (
            <div key={stage.id} className="flex items-center">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center ${colors.bg} ${colors.border} border`}
                title={`${stage.label}: ${stage.description}`}
              >
                <StageIcon stage={stage.id} status={stage.status} />
              </div>
              {index < stages.length - 1 && (
                <div
                  className={`w-4 h-0.5 ${
                    stage.status === 'completed' ? 'bg-green-400' : 'bg-gray-200 dark:bg-neutral-700'
                  }`}
                />
              )}
            </div>
          );
        })}
        <span className="text-xs text-[var(--color-text-secondary)] ml-1">
          {progressPercent}%
        </span>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-neutral-800 rounded-lg border border-gray-200 dark:border-neutral-700 p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-[var(--color-text-primary)]">
          AI 처리 파이프라인
        </h3>
        <span className="text-xs text-[var(--color-text-secondary)]">
          {completedCount}/{stages.length} 완료
        </span>
      </div>

      {/* Progress Bar */}
      <div className="w-full h-2 bg-gray-200 dark:bg-neutral-700 rounded-full mb-4">
        <div
          className="h-2 bg-gradient-to-r from-blue-500 to-green-500 rounded-full transition-all duration-500"
          style={{ width: `${progressPercent}%` }}
        />
      </div>

      {/* Stage Cards */}
      <div className="grid grid-cols-4 gap-3">
        {stages.map((stage) => {
          const colors = statusColors[stage.status];
          return (
            <div
              key={stage.id}
              className={`p-3 rounded-lg border ${colors.bg} ${colors.border}`}
            >
              <div className="flex items-center gap-2 mb-1">
                <StageIcon stage={stage.id} status={stage.status} />
                <span className={`text-sm font-medium ${colors.text}`}>
                  {stage.label}
                </span>
              </div>
              <p className="text-xs text-[var(--color-text-secondary)]">
                {stage.description}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default PipelineProgressIndicator;
