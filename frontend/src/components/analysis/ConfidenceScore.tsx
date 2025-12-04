/**
 * Confidence Score Component
 * AI 분석 결과의 신뢰도 점수를 시각화하는 컴포넌트
 */

interface ConfidenceScoreProps {
  score: number; // 0.0 ~ 1.0
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  showBar?: boolean;
}

// 신뢰도 레벨별 색상 설정
function getConfidenceConfig(score: number): {
  label: string;
  colorClass: string;
  bgClass: string;
  barClass: string;
} {
  if (score >= 0.8) {
    return {
      label: '높음',
      colorClass: 'text-green-600',
      bgClass: 'bg-green-50',
      barClass: 'bg-green-500',
    };
  }
  if (score >= 0.6) {
    return {
      label: '보통',
      colorClass: 'text-blue-600',
      bgClass: 'bg-blue-50',
      barClass: 'bg-blue-500',
    };
  }
  if (score >= 0.4) {
    return {
      label: '낮음',
      colorClass: 'text-amber-600',
      bgClass: 'bg-amber-50',
      barClass: 'bg-amber-500',
    };
  }
  return {
    label: '매우 낮음',
    colorClass: 'text-red-600',
    bgClass: 'bg-red-50',
    barClass: 'bg-red-500',
  };
}

const sizeClasses = {
  sm: {
    text: 'text-xs',
    bar: 'h-1',
    width: 'w-16',
  },
  md: {
    text: 'text-sm',
    bar: 'h-1.5',
    width: 'w-24',
  },
  lg: {
    text: 'text-base',
    bar: 'h-2',
    width: 'w-32',
  },
};

export function ConfidenceScore({
  score,
  size = 'md',
  showLabel = true,
  showBar = true,
}: ConfidenceScoreProps) {
  const percentage = Math.round(score * 100);
  const config = getConfidenceConfig(score);
  const sizeConfig = sizeClasses[size];

  return (
    <div className="inline-flex items-center gap-2">
      {/* 퍼센트 표시 */}
      <span className={`font-medium ${sizeConfig.text} ${config.colorClass}`}>
        {percentage}%
      </span>

      {/* 프로그레스 바 */}
      {showBar && (
        <div
          className={`${sizeConfig.width} ${sizeConfig.bar} bg-gray-200 rounded-full overflow-hidden`}
        >
          <div
            className={`h-full ${config.barClass} rounded-full transition-all duration-300`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}

      {/* 레이블 */}
      {showLabel && (
        <span
          className={`${sizeConfig.text} px-1.5 py-0.5 rounded ${config.bgClass} ${config.colorClass}`}
        >
          {config.label}
        </span>
      )}
    </div>
  );
}

// 원형 신뢰도 표시 (대안적 UI)
interface CircularConfidenceProps {
  score: number;
  size?: number;
}

export function CircularConfidence({
  score,
  size = 48,
}: CircularConfidenceProps) {
  const percentage = Math.round(score * 100);
  const config = getConfidenceConfig(score);
  const circumference = 2 * Math.PI * 18; // radius = 18
  const offset = circumference - (score * circumference);

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="-rotate-90">
        {/* 배경 원 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={18}
          fill="none"
          stroke="currentColor"
          strokeWidth={4}
          className="text-gray-200"
        />
        {/* 진행 원 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={18}
          fill="none"
          stroke="currentColor"
          strokeWidth={4}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={config.colorClass}
        />
      </svg>
      <span
        className={`absolute text-xs font-bold ${config.colorClass}`}
      >
        {percentage}
      </span>
    </div>
  );
}
