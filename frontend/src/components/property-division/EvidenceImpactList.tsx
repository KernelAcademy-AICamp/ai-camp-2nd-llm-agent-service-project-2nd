'use client';

import { FileText, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import {
  EvidenceImpact,
  ImpactDirection,
  IMPACT_COLORS,
} from '@/types/property';

interface EvidenceImpactListProps {
  /** 증거 영향도 목록 */
  impacts: EvidenceImpact[];
  /** 증거 클릭 핸들러 */
  onEvidenceClick?: (evidenceId: string) => void;
}

function getImpactIcon(direction: ImpactDirection) {
  switch (direction) {
    case ImpactDirection.PLAINTIFF_FAVOR:
      return <TrendingUp className="w-4 h-4" />;
    case ImpactDirection.DEFENDANT_FAVOR:
      return <TrendingDown className="w-4 h-4" />;
    default:
      return <Minus className="w-4 h-4" />;
  }
}

function getImpactLabel(direction: ImpactDirection): string {
  switch (direction) {
    case ImpactDirection.PLAINTIFF_FAVOR:
      return '원고 유리';
    case ImpactDirection.DEFENDANT_FAVOR:
      return '피고 유리';
    default:
      return '중립';
  }
}

export default function EvidenceImpactList({
  impacts,
  onEvidenceClick,
}: EvidenceImpactListProps) {
  if (impacts.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <FileText className="w-8 h-8 mx-auto mb-2 text-gray-300" />
        <p className="text-sm">분석된 증거 영향도가 없습니다.</p>
      </div>
    );
  }

  // 영향도 절대값 기준으로 정렬 (큰 영향도가 위로)
  const sortedImpacts = [...impacts].sort(
    (a, b) => Math.abs(b.impact_percent) - Math.abs(a.impact_percent)
  );

  return (
    <div className="space-y-3">
      {sortedImpacts.map((impact) => {
        const color = IMPACT_COLORS[impact.direction];
        const isPositive = impact.direction === ImpactDirection.PLAINTIFF_FAVOR;
        const isNegative = impact.direction === ImpactDirection.DEFENDANT_FAVOR;

        return (
          <div
            key={impact.evidence_id}
            className={`
              p-4 rounded-lg border transition-all cursor-pointer
              hover:shadow-md hover:border-gray-300
              ${
                isPositive
                  ? 'bg-green-50 border-green-200'
                  : isNegative
                  ? 'bg-red-50 border-red-200'
                  : 'bg-gray-50 border-gray-200'
              }
            `}
            onClick={() => onEvidenceClick?.(impact.evidence_id)}
          >
            <div className="flex items-start justify-between">
              {/* 증거 정보 */}
              <div className="flex items-start space-x-3">
                <div
                  className="p-2 rounded-full"
                  style={{ backgroundColor: `${color}20` }}
                >
                  <FileText className="w-4 h-4" style={{ color }} />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-900">
                      {impact.evidence_type}
                    </span>
                    <span className="text-xs text-gray-400">
                      {impact.evidence_id}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{impact.reason}</p>
                </div>
              </div>

              {/* 영향도 표시 */}
              <div className="flex flex-col items-end">
                <div
                  className="flex items-center space-x-1 px-2 py-1 rounded-full text-sm font-semibold"
                  style={{
                    backgroundColor: `${color}20`,
                    color,
                  }}
                >
                  {getImpactIcon(impact.direction)}
                  <span>
                    {impact.impact_percent > 0 ? '+' : ''}
                    {impact.impact_percent.toFixed(1)}%
                  </span>
                </div>
                <span className="text-xs text-gray-400 mt-1">
                  {getImpactLabel(impact.direction)}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
