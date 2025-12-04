/**
 * Evidence Card Component
 * Card-style display for evidence items with status and retry functionality
 *
 * Features:
 * - Visual status indicators (icons, colors)
 * - Progress display for processing items
 * - Retry button for failed items
 * - AI analysis summary preview
 */

import { useState } from 'react';
import {
  RefreshCw,
  FileText,
  Image,
  Music,
  Video,
  File,
  Sparkles,
  AlertTriangle,
  ExternalLink,
} from 'lucide-react';
import { Evidence, EvidenceType } from '@/types/evidence';
import { EvidenceStatusBadge } from './EvidenceStatusBadge';
import { retryEvidence } from '@/lib/api/evidence';

interface EvidenceCardProps {
  evidence: Evidence;
  onRetry?: (evidenceId: string) => void;
  onView?: (evidence: Evidence) => void;
  onViewAnalysis?: (evidence: Evidence) => void;
  showAnalysisPreview?: boolean;
}

// Icon mapping for evidence types
const typeIcons: Record<EvidenceType, React.ReactNode> = {
  text: <FileText className="w-8 h-8" />,
  image: <Image className="w-8 h-8" />,
  audio: <Music className="w-8 h-8" />,
  video: <Video className="w-8 h-8" />,
  pdf: <File className="w-8 h-8" />,
};

// Color classes for evidence types
const typeColors: Record<EvidenceType, string> = {
  text: 'text-blue-500 bg-blue-50',
  image: 'text-purple-500 bg-purple-50',
  audio: 'text-green-500 bg-green-50',
  video: 'text-red-500 bg-red-50',
  pdf: 'text-orange-500 bg-orange-50',
};

export function EvidenceCard({
  evidence,
  onRetry,
  onView,
  onViewAnalysis,
  showAnalysisPreview = true,
}: EvidenceCardProps) {
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryError, setRetryError] = useState<string | null>(null);

  const handleRetry = async () => {
    setIsRetrying(true);
    setRetryError(null);

    try {
      const result = await retryEvidence(evidence.id);
      if (result.error) {
        setRetryError(result.error);
      } else {
        onRetry?.(evidence.id);
      }
    } catch (err) {
      setRetryError('재시도에 실패했습니다.');
    } finally {
      setIsRetrying(false);
    }
  };

  const isFailed = evidence.status === 'failed';
  const isProcessing = evidence.status === 'processing' || evidence.status === 'queued';
  const isCompleted = evidence.status === 'completed' || evidence.status === 'review_needed';

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      {/* Header with type icon and status */}
      <div className="flex items-start justify-between p-4 border-b border-gray-100">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${typeColors[evidence.type]}`}>
            {typeIcons[evidence.type]}
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="text-sm font-semibold text-gray-900 truncate">
              {evidence.filename}
            </h3>
            <p className="text-xs text-gray-500">
              {formatFileSize(evidence.size)} &middot;{' '}
              {new Date(evidence.uploadDate).toLocaleDateString('ko-KR')}
            </p>
          </div>
        </div>
        <EvidenceStatusBadge status={evidence.status} />
      </div>

      {/* Content area */}
      <div className="p-4">
        {/* Processing indicator */}
        {isProcessing && (
          <div className="mb-4">
            <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>AI 분석 진행 중...</span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full animate-pulse"
                style={{ width: '60%' }}
              />
            </div>
          </div>
        )}

        {/* Failed state with retry */}
        {isFailed && (
          <div className="mb-4 p-3 bg-red-50 rounded-lg">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-700">분석 실패</p>
                <p className="text-xs text-red-600 mt-1">
                  AI 분석 중 오류가 발생했습니다.
                </p>
                {retryError && (
                  <p className="text-xs text-red-500 mt-1">{retryError}</p>
                )}
              </div>
            </div>
            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className="mt-3 w-full flex items-center justify-center gap-2 px-3 py-2 text-sm font-medium text-red-700 bg-white border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isRetrying ? 'animate-spin' : ''}`} />
              {isRetrying ? '재시도 중...' : '재시도'}
            </button>
          </div>
        )}

        {/* Analysis preview for completed items */}
        {isCompleted && showAnalysisPreview && evidence.summary && (
          <div className="mb-4">
            <div className="flex items-center gap-1.5 text-xs font-medium text-accent mb-2">
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI 요약</span>
            </div>
            <p className="text-sm text-gray-700 line-clamp-3">{evidence.summary}</p>
          </div>
        )}

        {/* Labels */}
        {evidence.labels && evidence.labels.length > 0 && (
          <div className="mb-4">
            <div className="flex flex-wrap gap-1.5">
              {evidence.labels.slice(0, 4).map((label, idx) => (
                <span
                  key={idx}
                  className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded-full"
                >
                  {label}
                </span>
              ))}
              {evidence.labels.length > 4 && (
                <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-500 rounded-full">
                  +{evidence.labels.length - 4}
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Actions footer */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-100 flex gap-2">
        {onView && (
          <button
            onClick={() => onView(evidence)}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            상세 보기
          </button>
        )}
        {onViewAnalysis && isCompleted && (
          <button
            onClick={() => onViewAnalysis(evidence)}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-sm font-medium text-accent bg-accent/10 rounded-lg hover:bg-accent/20 transition-colors"
          >
            <Sparkles className="w-4 h-4" />
            분석 결과
          </button>
        )}
      </div>
    </div>
  );
}

// Format file size helper
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Evidence Card Grid Component
 * Displays evidence items in a responsive grid layout
 */
interface EvidenceCardGridProps {
  evidence: Evidence[];
  onRetry?: (evidenceId: string) => void;
  onView?: (evidence: Evidence) => void;
  onViewAnalysis?: (evidence: Evidence) => void;
  emptyMessage?: string;
}

export function EvidenceCardGrid({
  evidence,
  onRetry,
  onView,
  onViewAnalysis,
  emptyMessage = '증거가 없습니다.',
}: EvidenceCardGridProps) {
  if (evidence.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {evidence.map((item) => (
        <EvidenceCard
          key={item.id}
          evidence={item}
          onRetry={onRetry}
          onView={onView}
          onViewAnalysis={onViewAnalysis}
        />
      ))}
    </div>
  );
}
