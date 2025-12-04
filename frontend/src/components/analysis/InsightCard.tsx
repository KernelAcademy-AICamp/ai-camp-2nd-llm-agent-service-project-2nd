/**
 * Insight Card Component
 * AI 분석 결과 인사이트를 카드 형태로 표시하는 컴포넌트
 */

import {
  Lightbulb,
  Scale,
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import { useState } from 'react';
import { AIInsight } from '@/types/evidence';
import { ConfidenceScore } from './ConfidenceScore';

interface InsightCardProps {
  insight: AIInsight;
  expandable?: boolean;
  defaultExpanded?: boolean;
}

// 인사이트 타입별 설정
const insightTypeConfig: Record<
  AIInsight['type'],
  {
    icon: typeof Lightbulb;
    label: string;
    bgClass: string;
    borderClass: string;
    iconClass: string;
  }
> = {
  summary: {
    icon: Lightbulb,
    label: '요약',
    bgClass: 'bg-blue-50',
    borderClass: 'border-blue-200',
    iconClass: 'text-blue-600',
  },
  legal_relevance: {
    icon: Scale,
    label: '법적 관련성',
    bgClass: 'bg-purple-50',
    borderClass: 'border-purple-200',
    iconClass: 'text-purple-600',
  },
  risk_factor: {
    icon: AlertTriangle,
    label: '위험 요소',
    bgClass: 'bg-amber-50',
    borderClass: 'border-amber-200',
    iconClass: 'text-amber-600',
  },
  recommendation: {
    icon: CheckCircle,
    label: '권고사항',
    bgClass: 'bg-green-50',
    borderClass: 'border-green-200',
    iconClass: 'text-green-600',
  },
};

export function InsightCard({
  insight,
  expandable = false,
  defaultExpanded = true,
}: InsightCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const config = insightTypeConfig[insight.type];
  const Icon = config.icon;

  const toggleExpand = () => {
    if (expandable) {
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <div
      className={`rounded-lg border ${config.borderClass} ${config.bgClass} overflow-hidden`}
    >
      {/* Header */}
      <div
        className={`flex items-center justify-between p-3 ${expandable ? 'cursor-pointer hover:bg-opacity-80' : ''}`}
        onClick={toggleExpand}
      >
        <div className="flex items-center gap-2">
          <Icon className={`w-5 h-5 ${config.iconClass}`} />
          <span className="font-medium text-gray-800">{insight.title}</span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${config.bgClass} ${config.iconClass} border ${config.borderClass}`}
          >
            {config.label}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <ConfidenceScore score={insight.confidence} size="sm" showLabel={false} />
          {expandable && (
            <button className="text-gray-400 hover:text-gray-600">
              {isExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="px-3 pb-3 pt-0">
          <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
            {insight.content}
          </p>
          <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
            <span>
              신뢰도: <ConfidenceScore score={insight.confidence} size="sm" showBar={false} />
            </span>
            <span>
              생성: {new Date(insight.createdAt).toLocaleDateString('ko-KR')}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// 여러 인사이트를 표시하는 리스트 컴포넌트
interface InsightListProps {
  insights: AIInsight[];
  expandable?: boolean;
  groupByType?: boolean;
}

export function InsightList({
  insights,
  expandable = true,
  groupByType = false,
}: InsightListProps) {
  if (insights.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <Lightbulb className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p>분석 결과가 없습니다.</p>
      </div>
    );
  }

  if (groupByType) {
    const grouped = insights.reduce(
      (acc, insight) => {
        if (!acc[insight.type]) {
          acc[insight.type] = [];
        }
        acc[insight.type].push(insight);
        return acc;
      },
      {} as Record<AIInsight['type'], AIInsight[]>
    );

    return (
      <div className="space-y-6">
        {Object.entries(grouped).map(([type, typeInsights]) => (
          <div key={type}>
            <h4 className="text-sm font-medium text-gray-500 mb-2">
              {insightTypeConfig[type as AIInsight['type']].label}
            </h4>
            <div className="space-y-3">
              {typeInsights.map((insight) => (
                <InsightCard
                  key={insight.id}
                  insight={insight}
                  expandable={expandable}
                />
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {insights.map((insight) => (
        <InsightCard key={insight.id} insight={insight} expandable={expandable} />
      ))}
    </div>
  );
}
