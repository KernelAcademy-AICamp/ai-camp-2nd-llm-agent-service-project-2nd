'use client';

import { useEffect, useState } from 'react';
import { formatAmount } from '@/types/property';

interface DivisionGaugeProps {
  /** 원고 분할 비율 (%) */
  plaintiffRatio: number;
  /** 피고 분할 비율 (%) */
  defendantRatio: number;
  /** 원고 예상 금액 (선택) */
  plaintiffAmount?: number;
  /** 피고 예상 금액 (선택) */
  defendantAmount?: number;
  /** 애니메이션 활성화 여부 */
  animated?: boolean;
  /** 원고 라벨 (기본: 원고) */
  plaintiffLabel?: string;
  /** 피고 라벨 (기본: 피고) */
  defendantLabel?: string;
}

export default function DivisionGauge({
  plaintiffRatio,
  defendantRatio,
  plaintiffAmount,
  defendantAmount,
  animated = true,
  plaintiffLabel = '원고',
  defendantLabel = '피고',
}: DivisionGaugeProps) {
  const [displayRatio, setDisplayRatio] = useState(animated ? 50 : plaintiffRatio);

  useEffect(() => {
    if (animated) {
      // 애니메이션: 50%에서 실제 비율로 전환
      const timer = setTimeout(() => {
        setDisplayRatio(plaintiffRatio);
      }, 100);
      return () => clearTimeout(timer);
    } else {
      setDisplayRatio(plaintiffRatio);
    }
  }, [plaintiffRatio, animated]);

  return (
    <div className="w-full">
      {/* 라벨 및 비율 */}
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-sm font-medium text-gray-700">{plaintiffLabel}</span>
          <span className="text-lg font-bold text-green-600">
            {plaintiffRatio.toFixed(1)}%
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-lg font-bold text-red-600">
            {defendantRatio.toFixed(1)}%
          </span>
          <span className="text-sm font-medium text-gray-700">{defendantLabel}</span>
          <div className="w-3 h-3 rounded-full bg-red-500" />
        </div>
      </div>

      {/* 게이지 바 */}
      <div className="relative h-8 bg-gray-100 rounded-full overflow-hidden shadow-inner">
        {/* 원고 영역 (왼쪽, 초록) */}
        <div
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-green-500 to-green-400 transition-all duration-700 ease-out"
          style={{ width: `${displayRatio}%` }}
        />
        {/* 피고 영역 (오른쪽, 빨강) */}
        <div
          className="absolute top-0 right-0 h-full bg-gradient-to-l from-red-500 to-red-400 transition-all duration-700 ease-out"
          style={{ width: `${100 - displayRatio}%` }}
        />
        {/* 중앙 구분선 */}
        <div
          className="absolute top-0 h-full w-0.5 bg-white shadow-md transition-all duration-700 ease-out"
          style={{ left: `${displayRatio}%`, transform: 'translateX(-50%)' }}
        />
      </div>

      {/* 금액 표시 (있는 경우) */}
      {(plaintiffAmount !== undefined || defendantAmount !== undefined) && (
        <div className="flex justify-between items-center mt-2 text-sm">
          <div className="text-green-600 font-medium">
            {plaintiffAmount !== undefined ? formatAmount(plaintiffAmount) : '-'}
          </div>
          <div className="text-gray-400 text-xs">예상 분할 금액</div>
          <div className="text-red-600 font-medium">
            {defendantAmount !== undefined ? formatAmount(defendantAmount) : '-'}
          </div>
        </div>
      )}

      {/* 기준선 표시 */}
      <div className="relative mt-1">
        <div className="flex justify-between text-xs text-gray-400">
          <span>0%</span>
          <span className="absolute left-1/2 transform -translate-x-1/2">50%</span>
          <span>100%</span>
        </div>
      </div>
    </div>
  );
}
