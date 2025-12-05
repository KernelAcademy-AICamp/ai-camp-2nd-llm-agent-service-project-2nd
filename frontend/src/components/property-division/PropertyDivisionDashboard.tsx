'use client';

import { useState, useCallback, useEffect } from 'react';
import { Scale, AlertCircle, RefreshCw, Loader2, Info, ChevronDown, ChevronUp } from 'lucide-react';
import {
  DivisionPrediction,
  ConfidenceLevel,
  CONFIDENCE_COLORS,
  CONFIDENCE_LABELS,
} from '@/types/property';
import { analyzeImpact } from '@/lib/api/properties';
import DivisionGauge from './DivisionGauge';
import EvidenceImpactList from './EvidenceImpactList';

interface PropertyDivisionDashboardProps {
  /** 사건 ID */
  caseId: string;
  /** 증거 목록 (분석용) */
  evidences?: Array<{ id: string; type: string; content?: string }>;
  /** 초기 예측 결과 (있는 경우) */
  initialPrediction?: DivisionPrediction;
  /** 증거 클릭 핸들러 */
  onEvidenceClick?: (evidenceId: string) => void;
}

export default function PropertyDivisionDashboard({
  caseId,
  evidences = [],
  initialPrediction,
  onEvidenceClick,
}: PropertyDivisionDashboardProps) {
  const [prediction, setPrediction] = useState<DivisionPrediction | null>(
    initialPrediction || null
  );
  const [isLoading, setIsLoading] = useState(!initialPrediction);
  const [error, setError] = useState<string | null>(null);
  const [isImpactsExpanded, setIsImpactsExpanded] = useState(true);
  const [isSimilarCasesExpanded, setIsSimilarCasesExpanded] = useState(false);

  const fetchPrediction = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await analyzeImpact({
        case_id: caseId,
        evidences: evidences,
      });

      if (response.error) {
        setError(response.error);
        setPrediction(null);
      } else if (response.data) {
        setPrediction(response.data);
      }
    } catch (err) {
      console.error('Failed to fetch prediction:', err);
      setError('재산분할 예측을 불러오는데 실패했습니다.');
      setPrediction(null);
    } finally {
      setIsLoading(false);
    }
  }, [caseId, evidences]);

  useEffect(() => {
    if (!initialPrediction) {
      fetchPrediction();
    }
  }, [fetchPrediction, initialPrediction]);

  // 로딩 상태
  if (isLoading) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 flex flex-col items-center justify-center">
        <Loader2 className="w-8 h-8 text-accent animate-spin mb-4" />
        <p className="text-gray-500">재산분할 예측을 분석하고 있습니다...</p>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-700">{error}</p>
            <button
              onClick={fetchPrediction}
              className="text-sm text-red-600 hover:text-red-800 underline mt-1"
            >
              다시 시도
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 데이터 없음
  if (!prediction) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 flex flex-col items-center justify-center">
        <Scale className="w-12 h-12 text-gray-300 mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">
          분석 데이터 없음
        </h3>
        <p className="text-sm text-gray-500 text-center max-w-md">
          증거 자료가 부족하여 재산분할 예측을 할 수 없습니다.
          더 많은 증거를 업로드해 주세요.
        </p>
      </div>
    );
  }

  const confidenceColor = CONFIDENCE_COLORS[prediction.confidence_level];
  const confidenceLabel = CONFIDENCE_LABELS[prediction.confidence_level];

  return (
    <div className="space-y-6">
      {/* 메인 카드: 분할 비율 */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-3">
            <Scale className="w-6 h-6 text-accent" />
            <h2 className="text-lg font-bold text-gray-900">재산분할 예측</h2>
          </div>
          <div className="flex items-center space-x-3">
            {/* 신뢰도 뱃지 */}
            <div
              className="flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium"
              style={{ backgroundColor: `${confidenceColor}20`, color: confidenceColor }}
            >
              <Info className="w-3 h-3" />
              <span>신뢰도: {confidenceLabel}</span>
            </div>
            {/* 새로고침 버튼 */}
            <button
              onClick={fetchPrediction}
              disabled={isLoading}
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* 분할 게이지 */}
        <DivisionGauge
          plaintiffRatio={prediction.plaintiff_ratio}
          defendantRatio={prediction.defendant_ratio}
          plaintiffAmount={prediction.plaintiff_amount}
          defendantAmount={prediction.defendant_amount}
          animated
        />
      </div>

      {/* 증거 영향도 섹션 */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <button
          onClick={() => setIsImpactsExpanded(!isImpactsExpanded)}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center space-x-2">
            <h3 className="text-base font-semibold text-gray-900">
              증거별 영향도
            </h3>
            <span className="text-sm text-gray-400">
              ({prediction.evidence_impacts.length}개)
            </span>
          </div>
          {isImpactsExpanded ? (
            <ChevronUp className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </button>
        {isImpactsExpanded && (
          <div className="px-6 pb-6">
            <EvidenceImpactList
              impacts={prediction.evidence_impacts}
              onEvidenceClick={onEvidenceClick}
            />
          </div>
        )}
      </div>

      {/* 유사 판례 섹션 (있는 경우) */}
      {prediction.similar_cases && prediction.similar_cases.length > 0 && (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <button
            onClick={() => setIsSimilarCasesExpanded(!isSimilarCasesExpanded)}
            className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center space-x-2">
              <h3 className="text-base font-semibold text-gray-900">
                유사 판례
              </h3>
              <span className="text-sm text-gray-400">
                ({prediction.similar_cases.length}개)
              </span>
            </div>
            {isSimilarCasesExpanded ? (
              <ChevronUp className="w-5 h-5 text-gray-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-400" />
            )}
          </button>
          {isSimilarCasesExpanded && (
            <div className="px-6 pb-6 space-y-3">
              {prediction.similar_cases.map((similarCase) => (
                <div
                  key={similarCase.case_id}
                  className="p-4 bg-gray-50 rounded-lg border border-gray-200"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900">
                        {similarCase.case_name}
                      </h4>
                      <p className="text-sm text-gray-600 mt-1">
                        {similarCase.summary}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {similarCase.plaintiff_ratio}:{similarCase.defendant_ratio}
                      </div>
                      <div className="text-xs text-gray-400">
                        유사도: {Math.round(similarCase.similarity_score * 100)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 안내 문구 */}
      <div className="bg-blue-50 rounded-xl p-4 flex items-start space-x-3">
        <Info className="w-5 h-5 text-blue-500 mt-0.5" />
        <div>
          <p className="text-sm text-blue-700">
            이 예측은 AI 분석을 기반으로 한 참고 자료입니다.
            실제 재산분할 결과는 법원의 판단에 따라 달라질 수 있습니다.
          </p>
        </div>
      </div>
    </div>
  );
}
