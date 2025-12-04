'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Plus,
  RefreshCw,
  Trash2,
  Edit2,
  Building2,
  Wallet,
  TrendingUp,
  Car,
  Shield,
  CreditCard,
  HelpCircle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  Property,
  PropertyCreate,
  PropertyListResponse,
  DivisionPrediction,
  PropertyType,
  PROPERTY_TYPE_LABELS,
  PROPERTY_OWNER_LABELS,
} from '@/types/property';
import {
  getProperties,
  createProperty,
  deleteProperty,
  getDivisionPrediction,
  calculateDivisionPrediction,
} from '@/lib/api/properties';
import DivisionGauge from './DivisionGauge';
import PropertyInputForm from './PropertyInputForm';

interface PropertyDivisionDashboardProps {
  caseId: string;
}

// Icons for property types
const PROPERTY_TYPE_ICONS: Record<PropertyType, React.ReactNode> = {
  real_estate: <Building2 className="w-4 h-4" />,
  savings: <Wallet className="w-4 h-4" />,
  stocks: <TrendingUp className="w-4 h-4" />,
  retirement: <Shield className="w-4 h-4" />,
  vehicle: <Car className="w-4 h-4" />,
  insurance: <Shield className="w-4 h-4" />,
  debt: <CreditCard className="w-4 h-4" />,
  other: <HelpCircle className="w-4 h-4" />,
};

/**
 * PropertyDivisionDashboard - Main dashboard for property division visualization
 *
 * Features:
 * - Property list with CRUD operations
 * - Division prediction gauge with animation
 * - Summary statistics
 * - Evidence impact display
 * - Similar cases reference
 */
export default function PropertyDivisionDashboard({
  caseId,
}: PropertyDivisionDashboardProps) {
  const [properties, setProperties] = useState<Property[]>([]);
  const [summary, setSummary] = useState({
    total_assets: 0,
    total_debts: 0,
    net_value: 0,
  });
  const [prediction, setPrediction] = useState<DivisionPrediction | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isCalculating, setIsCalculating] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [expandedEvidence, setExpandedEvidence] = useState(false);
  const [expandedSimilar, setExpandedSimilar] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Format currency
  const formatAmount = (amount: number) => {
    if (amount >= 100000000) {
      return `${(amount / 100000000).toFixed(1)}억원`;
    }
    if (amount >= 10000) {
      return `${(amount / 10000).toFixed(0)}만원`;
    }
    return `${amount.toLocaleString()}원`;
  };

  // Load data
  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Load properties and prediction in parallel
      const [propertiesRes, predictionRes] = await Promise.all([
        getProperties(caseId),
        getDivisionPrediction(caseId),
      ]);

      if (propertiesRes.data) {
        setProperties(propertiesRes.data.properties);
        setSummary({
          total_assets: propertiesRes.data.total_assets,
          total_debts: propertiesRes.data.total_debts,
          net_value: propertiesRes.data.net_value,
        });
      }

      if (predictionRes.data) {
        setPrediction(predictionRes.data);
      }
    } catch {
      setError('데이터를 불러오는데 실패했습니다.');
    } finally {
      setIsLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Add property
  const handleAddProperty = async (data: PropertyCreate) => {
    setIsSubmitting(true);
    try {
      const response = await createProperty(caseId, data);
      if (response.error) {
        alert(`재산 추가 실패: ${response.error}`);
        return;
      }
      setShowAddForm(false);
      await loadData();
    } finally {
      setIsSubmitting(false);
    }
  };

  // Delete property
  const handleDeleteProperty = async (propertyId: string) => {
    if (!confirm('이 재산을 삭제하시겠습니까?')) return;

    try {
      const response = await deleteProperty(caseId, propertyId);
      if (response.error) {
        alert(`삭제 실패: ${response.error}`);
        return;
      }
      await loadData();
    } catch {
      alert('삭제 중 오류가 발생했습니다.');
    }
  };

  // Calculate prediction
  const handleCalculatePrediction = async () => {
    setIsCalculating(true);
    try {
      const response = await calculateDivisionPrediction(caseId, true);
      if (response.error) {
        alert(`예측 계산 실패: ${response.error}`);
        return;
      }
      if (response.data) {
        setPrediction(response.data);
      }
    } finally {
      setIsCalculating(false);
    }
  };

  // Owner color styles
  const getOwnerStyle = (owner: string) => {
    switch (owner) {
      case 'plaintiff':
        return 'bg-blue-100 text-blue-700';
      case 'defendant':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-purple-100 text-purple-700';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-sm text-neutral-500 mb-1">총 자산</p>
          <p className="text-2xl font-bold text-green-600">
            {formatAmount(summary.total_assets)}
          </p>
        </div>
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-sm text-neutral-500 mb-1">총 부채</p>
          <p className="text-2xl font-bold text-red-600">
            {formatAmount(summary.total_debts)}
          </p>
        </div>
        <div className="bg-white rounded-xl shadow p-5">
          <p className="text-sm text-neutral-500 mb-1">순재산</p>
          <p className="text-2xl font-bold text-primary">
            {formatAmount(summary.net_value)}
          </p>
        </div>
      </div>

      {/* Division Prediction Gauge */}
      {prediction ? (
        <DivisionGauge
          plaintiffRatio={prediction.plaintiff_ratio}
          defendantRatio={prediction.defendant_ratio}
          plaintiffAmount={prediction.plaintiff_amount}
          defendantAmount={prediction.defendant_amount}
          confidenceLevel={prediction.confidence_level}
          animated={true}
        />
      ) : (
        <div className="bg-white rounded-xl shadow-lg p-6 text-center">
          <p className="text-neutral-500 mb-4">아직 예측이 없습니다</p>
          <button
            type="button"
            onClick={handleCalculatePrediction}
            disabled={isCalculating || properties.length === 0}
            className="px-4 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary-dark transition-colors disabled:opacity-50 flex items-center gap-2 mx-auto"
          >
            {isCalculating ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                계산 중...
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                예측 계산하기
              </>
            )}
          </button>
        </div>
      )}

      {/* Evidence Impacts */}
      {prediction && prediction.evidence_impacts.length > 0 && (
        <div className="bg-white rounded-xl shadow p-5">
          <button
            type="button"
            onClick={() => setExpandedEvidence(!expandedEvidence)}
            className="w-full flex items-center justify-between"
          >
            <h3 className="font-bold text-neutral-800">
              증거 영향도 ({prediction.evidence_impacts.length}건)
            </h3>
            {expandedEvidence ? (
              <ChevronUp className="w-5 h-5 text-neutral-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-neutral-500" />
            )}
          </button>
          {expandedEvidence && (
            <div className="mt-4 space-y-3">
              {prediction.evidence_impacts.map((impact, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-neutral-800">{impact.evidence_type}</p>
                    <p className="text-sm text-neutral-500">{impact.reason}</p>
                  </div>
                  <div
                    className={`px-3 py-1 rounded-full text-sm font-medium ${
                      impact.direction === 'plaintiff'
                        ? 'bg-blue-100 text-blue-700'
                        : 'bg-red-100 text-red-700'
                    }`}
                  >
                    {impact.direction === 'plaintiff' ? '원고' : '피고'} +
                    {impact.impact_percent}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Similar Cases */}
      {prediction && prediction.similar_cases.length > 0 && (
        <div className="bg-white rounded-xl shadow p-5">
          <button
            type="button"
            onClick={() => setExpandedSimilar(!expandedSimilar)}
            className="w-full flex items-center justify-between"
          >
            <h3 className="font-bold text-neutral-800">
              유사 판례 ({prediction.similar_cases.length}건)
            </h3>
            {expandedSimilar ? (
              <ChevronUp className="w-5 h-5 text-neutral-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-neutral-500" />
            )}
          </button>
          {expandedSimilar && (
            <div className="mt-4 space-y-3">
              {prediction.similar_cases.map((sc, idx) => (
                <div key={idx} className="p-3 bg-neutral-50 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <p className="font-medium text-neutral-800">{sc.case_ref}</p>
                    <span className="text-sm text-neutral-500">
                      유사도: {(sc.similarity_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <p className="text-sm text-primary font-medium">분할비율: {sc.division_ratio}</p>
                  <div className="flex flex-wrap gap-1 mt-2">
                    {sc.key_factors.map((factor, i) => (
                      <span
                        key={i}
                        className="text-xs px-2 py-1 bg-neutral-200 text-neutral-700 rounded"
                      >
                        {factor}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Property List */}
      <div className="bg-white rounded-xl shadow p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-neutral-800">
            재산 목록 ({properties.length}건)
          </h3>
          <div className="flex gap-2">
            {prediction && (
              <button
                type="button"
                onClick={handleCalculatePrediction}
                disabled={isCalculating}
                className="px-3 py-2 text-sm border border-neutral-300 text-neutral-700 rounded-lg hover:bg-neutral-50 transition-colors flex items-center gap-1"
              >
                <RefreshCw className={`w-4 h-4 ${isCalculating ? 'animate-spin' : ''}`} />
                재계산
              </button>
            )}
            <button
              type="button"
              onClick={() => setShowAddForm(true)}
              className="px-3 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors flex items-center gap-1"
            >
              <Plus className="w-4 h-4" />
              재산 추가
            </button>
          </div>
        </div>

        {properties.length === 0 ? (
          <div className="text-center py-12 text-neutral-500">
            <Building2 className="w-12 h-12 mx-auto mb-3 text-neutral-300" />
            <p>등록된 재산이 없습니다</p>
            <p className="text-sm mt-1">재산을 추가하여 분할 예측을 시작하세요</p>
          </div>
        ) : (
          <div className="divide-y divide-neutral-100">
            {properties.map((property) => (
              <div
                key={property.id}
                className="flex items-center justify-between py-4"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-neutral-100 rounded-lg text-neutral-600">
                    {PROPERTY_TYPE_ICONS[property.property_type]}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-neutral-800">
                        {PROPERTY_TYPE_LABELS[property.property_type]}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${getOwnerStyle(
                          property.owner
                        )}`}
                      >
                        {PROPERTY_OWNER_LABELS[property.owner]}
                      </span>
                      {property.is_premarital && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700">
                          특유재산
                        </span>
                      )}
                    </div>
                    {property.description && (
                      <p className="text-sm text-neutral-500">{property.description}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span
                    className={`font-bold ${
                      property.property_type === 'debt'
                        ? 'text-red-600'
                        : 'text-neutral-800'
                    }`}
                  >
                    {property.property_type === 'debt' && '-'}
                    {formatAmount(property.estimated_value)}
                  </span>
                  <div className="flex gap-1">
                    <button
                      type="button"
                      className="p-2 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 rounded-lg transition-colors"
                      aria-label="수정"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteProperty(property.id)}
                      className="p-2 text-neutral-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      aria-label="삭제"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Property Form Modal */}
      {showAddForm && (
        <PropertyInputForm
          onSubmit={handleAddProperty}
          onCancel={() => setShowAddForm(false)}
          isSubmitting={isSubmitting}
        />
      )}
    </div>
  );
}
