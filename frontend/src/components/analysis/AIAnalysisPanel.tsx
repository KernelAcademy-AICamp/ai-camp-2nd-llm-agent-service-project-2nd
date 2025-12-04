/**
 * AI Analysis Panel Component
 * 증거의 AI 분석 결과를 종합적으로 표시하는 패널 컴포넌트
 */

import { Brain, Tags, FileText, AlertCircle } from 'lucide-react';
import { Evidence, Article840Tags, AIInsight } from '@/types/evidence';
import { Article840TagList } from './Article840TagBadge';
import { ConfidenceScore, CircularConfidence } from './ConfidenceScore';
import { InsightList } from './InsightCard';

interface AIAnalysisPanelProps {
  evidence: Evidence;
  isLoading?: boolean;
}

export function AIAnalysisPanel({ evidence, isLoading = false }: AIAnalysisPanelProps) {
  const hasAnalysis = evidence.article840Tags || evidence.insights?.length;

  if (isLoading) {
    return <AIAnalysisPanelSkeleton />;
  }

  if (evidence.status !== 'completed' && evidence.status !== 'review_needed') {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center">
        <Brain className="w-10 h-10 mx-auto mb-3 text-gray-400" />
        <h3 className="font-medium text-gray-700 mb-1">AI 분석 대기 중</h3>
        <p className="text-sm text-gray-500">
          증거가 처리되면 분석 결과가 표시됩니다.
        </p>
      </div>
    );
  }

  if (!hasAnalysis) {
    return (
      <div className="bg-gray-50 rounded-lg p-6 text-center">
        <AlertCircle className="w-10 h-10 mx-auto mb-3 text-gray-400" />
        <h3 className="font-medium text-gray-700 mb-1">분석 결과 없음</h3>
        <p className="text-sm text-gray-500">
          이 증거에 대한 AI 분석 결과가 없습니다.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Article 840 태그 섹션 */}
      {evidence.article840Tags && (
        <Article840Section tags={evidence.article840Tags} />
      )}

      {/* AI Summary 섹션 */}
      {evidence.summary && (
        <SummarySection summary={evidence.summary} />
      )}

      {/* AI Insights 섹션 */}
      {evidence.insights && evidence.insights.length > 0 && (
        <InsightsSection insights={evidence.insights} />
      )}

      {/* 키워드/라벨 섹션 */}
      {evidence.labels && evidence.labels.length > 0 && (
        <LabelsSection labels={evidence.labels} />
      )}
    </div>
  );
}

// Article 840 분석 섹션
function Article840Section({ tags }: { tags: Article840Tags }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Tags className="w-5 h-5 text-primary" />
          <h3 className="font-semibold text-gray-800">민법 840조 분류</h3>
        </div>
        <ConfidenceScore score={tags.confidence} size="sm" />
      </div>

      {tags.categories.length > 0 ? (
        <div className="space-y-3">
          <Article840TagList categories={tags.categories} size="md" />

          {tags.matchedKeywords.length > 0 && (
            <div className="pt-2 border-t border-gray-100">
              <p className="text-xs text-gray-500 mb-1">매칭된 키워드</p>
              <div className="flex flex-wrap gap-1">
                {tags.matchedKeywords.map((keyword, idx) => (
                  <span
                    key={idx}
                    className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <p className="text-sm text-gray-500">
          특정 이혼 사유에 해당하지 않는 일반 증거입니다.
        </p>
      )}
    </div>
  );
}

// 요약 섹션
function SummarySection({ summary }: { summary: string }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-3">
        <FileText className="w-5 h-5 text-blue-600" />
        <h3 className="font-semibold text-gray-800">AI 요약</h3>
      </div>
      <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
        {summary}
      </p>
    </div>
  );
}

// 인사이트 섹션
function InsightsSection({ insights }: { insights: AIInsight[] }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Brain className="w-5 h-5 text-purple-600" />
        <h3 className="font-semibold text-gray-800">AI 인사이트</h3>
        <span className="text-xs px-2 py-0.5 bg-purple-100 text-purple-600 rounded-full">
          {insights.length}개
        </span>
      </div>
      <InsightList insights={insights} expandable groupByType />
    </div>
  );
}

// 라벨 섹션
function LabelsSection({ labels }: { labels: string[] }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div className="flex items-center gap-2 mb-3">
        <Tags className="w-5 h-5 text-teal-600" />
        <h3 className="font-semibold text-gray-800">분석 라벨</h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {labels.map((label, idx) => (
          <span
            key={idx}
            className="text-sm px-3 py-1 bg-teal-50 text-teal-700 border border-teal-200 rounded-full"
          >
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

// 로딩 스켈레톤
function AIAnalysisPanelSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {/* Article 840 skeleton */}
      <div className="bg-gray-100 rounded-lg p-4">
        <div className="h-5 bg-gray-200 rounded w-32 mb-3" />
        <div className="flex gap-2">
          <div className="h-6 bg-gray-200 rounded w-20" />
          <div className="h-6 bg-gray-200 rounded w-24" />
        </div>
      </div>

      {/* Summary skeleton */}
      <div className="bg-gray-100 rounded-lg p-4">
        <div className="h-5 bg-gray-200 rounded w-24 mb-3" />
        <div className="space-y-2">
          <div className="h-4 bg-gray-200 rounded w-full" />
          <div className="h-4 bg-gray-200 rounded w-3/4" />
        </div>
      </div>

      {/* Insights skeleton */}
      <div className="bg-gray-100 rounded-lg p-4">
        <div className="h-5 bg-gray-200 rounded w-28 mb-3" />
        <div className="space-y-2">
          <div className="h-16 bg-gray-200 rounded" />
          <div className="h-16 bg-gray-200 rounded" />
        </div>
      </div>
    </div>
  );
}

// 컴팩트 버전 (목록에서 사용)
interface AIAnalysisBadgeProps {
  evidence: Evidence;
}

export function AIAnalysisBadge({ evidence }: AIAnalysisBadgeProps) {
  if (!evidence.article840Tags && !evidence.insights?.length) {
    return null;
  }

  const hasHighConfidence =
    (evidence.article840Tags?.confidence ?? 0) >= 0.7 ||
    evidence.insights?.some((i) => i.confidence >= 0.7);

  return (
    <div className="flex items-center gap-2">
      {evidence.article840Tags && evidence.article840Tags.categories.length > 0 && (
        <Article840TagList
          categories={evidence.article840Tags.categories}
          size="sm"
          maxVisible={2}
        />
      )}
      {hasHighConfidence && (
        <span className="flex items-center text-xs text-green-600">
          <Brain className="w-3 h-3 mr-0.5" />
          AI
        </span>
      )}
    </div>
  );
}
