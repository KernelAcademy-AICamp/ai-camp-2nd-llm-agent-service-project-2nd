'use client';

/**
 * PropertyDivisionDashboard - Simplified Property Division Dashboard
 * 014-ui-settings-completion Feature
 *
 * Simplified version:
 * - Property list with CRUD operations
 * - Summary statistics (total assets, debts, net worth)
 * - Manual ratio input (no AI prediction)
 *
 * Removed:
 * - DivisionGauge (AI prediction gauge)
 * - Evidence impacts section
 * - Similar cases section
 * - AI prediction calculation
 */

import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import {
  Plus,
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
} from 'lucide-react';
import {
  Property,
  PropertyCreate,
  PropertyType,
  PROPERTY_TYPE_LABELS,
  PROPERTY_OWNER_LABELS,
} from '@/types/property';
import {
  getProperties,
  createProperty,
  deleteProperty,
} from '@/lib/api/properties';
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
  const [isLoading, setIsLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 014-ui-settings-completion: Manual ratio input state
  const [plaintiffRatio, setPlaintiffRatio] = useState('');
  const [defendantRatio, setDefendantRatio] = useState('');

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
      const propertiesRes = await getProperties(caseId);

      if (propertiesRes.data) {
        setProperties(propertiesRes.data.properties);
        setSummary({
          total_assets: propertiesRes.data.total_assets,
          total_debts: propertiesRes.data.total_debts,
          net_value: propertiesRes.data.net_value,
        });
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
        toast.error(`재산 추가 실패: ${response.error}`);
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
        toast.error(`삭제 실패: ${response.error}`);
        return;
      }
      await loadData();
    } catch {
      toast.error('삭제 중 오류가 발생했습니다.');
    }
  };

  // Owner color styles
  const getOwnerStyle = (owner: string) => {
    switch (owner) {
      case 'plaintiff':
        return 'bg-info-light text-info';
      case 'defendant':
        return 'bg-error-light text-error';
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
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow p-5">
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-1">총 자산</p>
          <p className="text-2xl font-bold text-green-600 dark:text-green-500">
            {formatAmount(summary.total_assets)}
          </p>
        </div>
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow p-5">
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-1">총 부채</p>
          <p className="text-2xl font-bold text-red-600 dark:text-red-500">
            {formatAmount(summary.total_debts)}
          </p>
        </div>
        <div className="bg-white dark:bg-neutral-800 rounded-xl shadow p-5">
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-1">순재산</p>
          <p className="text-2xl font-bold text-primary dark:text-primary-light">
            {formatAmount(summary.net_value)}
          </p>
        </div>
      </div>

      {/* 014-ui-settings-completion: Manual Ratio Input */}
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow p-5">
        <h3 className="font-bold text-neutral-800 dark:text-neutral-200 mb-4">예상 분할 비율</h3>
        <p className="text-sm text-neutral-500 dark:text-neutral-400 mb-4">
          재산분할 협상 또는 판결에서 예상되는 비율을 직접 입력하세요.
        </p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              원고 예상 비율
            </label>
            <div className="relative">
              <input
                type="text"
                value={plaintiffRatio}
                onChange={(e) => setPlaintiffRatio(e.target.value)}
                placeholder="예: 50%"
                className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg
                         bg-white dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <span className="px-2 py-0.5 text-xs bg-info-light text-info rounded">
                  원고
                </span>
              </div>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              피고 예상 비율
            </label>
            <div className="relative">
              <input
                type="text"
                value={defendantRatio}
                onChange={(e) => setDefendantRatio(e.target.value)}
                placeholder="예: 50%"
                className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg
                         bg-white dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200
                         focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <span className="px-2 py-0.5 text-xs bg-warning-light text-warning rounded">
                  피고
                </span>
              </div>
            </div>
          </div>
        </div>
        {(plaintiffRatio || defendantRatio) && (
          <div className="mt-4 p-3 bg-neutral-50 dark:bg-neutral-700/50 rounded-lg">
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              예상 분할: 원고 <span className="font-bold text-info">{plaintiffRatio || '-'}</span>
              {' : '}
              피고 <span className="font-bold text-warning">{defendantRatio || '-'}</span>
            </p>
          </div>
        )}
      </div>

      {/* Property List */}
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold text-neutral-800 dark:text-neutral-200">
            재산 목록 ({properties.length}건)
          </h3>
          <div className="flex gap-2">
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
          <div className="text-center py-12 text-neutral-500 dark:text-neutral-400">
            <Building2 className="w-12 h-12 mx-auto mb-3 text-neutral-300 dark:text-neutral-600" />
            <p>등록된 재산이 없습니다</p>
            <p className="text-sm mt-1">재산을 추가하여 목록을 관리하세요</p>
          </div>
        ) : (
          <div className="divide-y divide-neutral-100 dark:divide-neutral-700">
            {properties.map((property) => (
              <div
                key={property.id}
                className="flex items-center justify-between py-4"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-neutral-100 dark:bg-neutral-700 rounded-lg text-neutral-600 dark:text-neutral-300">
                    {PROPERTY_TYPE_ICONS[property.property_type]}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-neutral-800 dark:text-neutral-200">
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
                        <span className="text-xs px-2 py-0.5 rounded-full bg-warning-light text-warning">
                          특유재산
                        </span>
                      )}
                    </div>
                    {property.description && (
                      <p className="text-sm text-neutral-500 dark:text-neutral-400">{property.description}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <span
                    className={`font-bold ${
                      property.property_type === 'debt'
                        ? 'text-red-600 dark:text-red-500'
                        : 'text-neutral-800 dark:text-neutral-200'
                    }`}
                  >
                    {property.property_type === 'debt' && '-'}
                    {formatAmount(property.estimated_value)}
                  </span>
                  <div className="flex gap-1">
                    <button
                      type="button"
                      className="p-2 text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-200 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
                      aria-label="수정"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteProperty(property.id)}
                      className="p-2 text-neutral-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
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
