'use client';

import { useEffect, useState } from 'react';
import { ConfidenceLevel, CONFIDENCE_LEVEL_LABELS } from '@/types/property';

interface DivisionGaugeProps {
  plaintiffRatio: number;
  defendantRatio: number;
  plaintiffAmount: number;
  defendantAmount: number;
  confidenceLevel: ConfidenceLevel;
  animated?: boolean;
}

/**
 * DivisionGauge - Animated gauge component showing property division ratio
 *
 * Features:
 * - Animated bar showing plaintiff vs defendant ratio
 * - Amount display for each party
 * - Confidence level indicator
 */
export default function DivisionGauge({
  plaintiffRatio,
  defendantRatio,
  plaintiffAmount,
  defendantAmount,
  confidenceLevel,
  animated = true,
}: DivisionGaugeProps) {
  const [displayRatio, setDisplayRatio] = useState(animated ? 50 : plaintiffRatio);
  const [isAnimating, setIsAnimating] = useState(animated);

  useEffect(() => {
    if (animated) {
      // Start animation after mount
      const timer = setTimeout(() => {
        setDisplayRatio(plaintiffRatio);
        setIsAnimating(false);
      }, 100);

      return () => clearTimeout(timer);
    }
  }, [plaintiffRatio, animated]);

  // Format currency in Korean Won
  const formatAmount = (amount: number) => {
    if (amount >= 100000000) {
      return `${(amount / 100000000).toFixed(1)}억원`;
    }
    if (amount >= 10000) {
      return `${(amount / 10000).toFixed(0)}만원`;
    }
    return `${amount.toLocaleString()}원`;
  };

  // Confidence level colors
  const confidenceColors: Record<ConfidenceLevel, string> = {
    low: 'bg-yellow-100 text-yellow-700 border-yellow-300',
    medium: 'bg-blue-100 text-blue-700 border-blue-300',
    high: 'bg-green-100 text-green-700 border-green-300',
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-bold text-neutral-800">재산분할 예측</h3>
        <span
          className={`px-3 py-1 rounded-full text-xs font-medium border ${confidenceColors[confidenceLevel]}`}
        >
          신뢰도: {CONFIDENCE_LEVEL_LABELS[confidenceLevel]}
        </span>
      </div>

      {/* Ratio Display */}
      <div className="flex justify-between items-center mb-3">
        <div className="text-center">
          <span className="text-sm font-medium text-blue-600">원고</span>
          <p className="text-2xl font-bold text-blue-700">{plaintiffRatio}%</p>
        </div>
        <div className="text-center">
          <span className="text-sm font-medium text-red-600">피고</span>
          <p className="text-2xl font-bold text-red-700">{defendantRatio}%</p>
        </div>
      </div>

      {/* Gauge Bar */}
      <div className="relative h-10 bg-neutral-200 rounded-full overflow-hidden mb-4">
        {/* Plaintiff Side (Blue) */}
        <div
          className={`absolute left-0 top-0 h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-l-full ${
            isAnimating ? '' : 'transition-all duration-1000 ease-out'
          }`}
          style={{ width: `${displayRatio}%` }}
        >
          {displayRatio > 15 && (
            <span className="absolute right-2 top-1/2 -translate-y-1/2 text-white text-sm font-semibold">
              원고
            </span>
          )}
        </div>

        {/* Defendant Side (Red) - fills the rest */}
        <div
          className={`absolute right-0 top-0 h-full bg-gradient-to-l from-red-500 to-red-600 rounded-r-full ${
            isAnimating ? '' : 'transition-all duration-1000 ease-out'
          }`}
          style={{ width: `${100 - displayRatio}%` }}
        >
          {100 - displayRatio > 15 && (
            <span className="absolute left-2 top-1/2 -translate-y-1/2 text-white text-sm font-semibold">
              피고
            </span>
          )}
        </div>

        {/* Center Line */}
        <div className="absolute left-1/2 top-0 w-0.5 h-full bg-white opacity-50" />
      </div>

      {/* Amount Display */}
      <div className="flex justify-between items-center pt-4 border-t border-neutral-100">
        <div className="text-center flex-1">
          <p className="text-sm text-neutral-500 mb-1">원고 예상 수령액</p>
          <p className="text-xl font-bold text-blue-600">{formatAmount(plaintiffAmount)}</p>
        </div>
        <div className="w-px h-12 bg-neutral-200" />
        <div className="text-center flex-1">
          <p className="text-sm text-neutral-500 mb-1">피고 예상 수령액</p>
          <p className="text-xl font-bold text-red-600">{formatAmount(defendantAmount)}</p>
        </div>
      </div>
    </div>
  );
}
