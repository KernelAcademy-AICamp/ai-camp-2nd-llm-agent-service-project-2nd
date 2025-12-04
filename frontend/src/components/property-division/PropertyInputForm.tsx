'use client';

import { useState } from 'react';
import { X, Plus, Building2, Wallet, TrendingUp, Car, Shield, CreditCard, HelpCircle } from 'lucide-react';
import {
  PropertyType,
  PropertyOwner,
  PropertyCreate,
  PROPERTY_TYPE_LABELS,
  PROPERTY_OWNER_LABELS,
} from '@/types/property';

interface PropertyInputFormProps {
  onSubmit: (data: PropertyCreate) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
}

// Icons for property types
const PROPERTY_TYPE_ICONS: Record<PropertyType, React.ReactNode> = {
  real_estate: <Building2 className="w-5 h-5" />,
  savings: <Wallet className="w-5 h-5" />,
  stocks: <TrendingUp className="w-5 h-5" />,
  retirement: <Shield className="w-5 h-5" />,
  vehicle: <Car className="w-5 h-5" />,
  insurance: <Shield className="w-5 h-5" />,
  debt: <CreditCard className="w-5 h-5" />,
  other: <HelpCircle className="w-5 h-5" />,
};

/**
 * PropertyInputForm - Form for adding new property
 *
 * Features:
 * - Property type selection with icons
 * - Owner selection (plaintiff/defendant/joint)
 * - Value input with Korean Won formatting
 * - Premarital property checkbox
 * - Optional description and notes
 */
export default function PropertyInputForm({
  onSubmit,
  onCancel,
  isSubmitting = false,
}: PropertyInputFormProps) {
  const [formData, setFormData] = useState<PropertyCreate>({
    property_type: 'real_estate',
    estimated_value: 0,
    owner: 'joint',
    description: '',
    is_premarital: false,
    notes: '',
  });

  const [valueInput, setValueInput] = useState('');

  const handleValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/[^0-9]/g, '');
    const numValue = parseInt(raw) || 0;
    setValueInput(numValue.toLocaleString());
    setFormData((prev) => ({ ...prev, estimated_value: numValue }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.estimated_value === 0) {
      alert('금액을 입력해주세요.');
      return;
    }
    await onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-neutral-100">
          <h2 className="text-xl font-bold text-neutral-800">재산 추가</h2>
          <button
            type="button"
            onClick={onCancel}
            className="p-2 hover:bg-neutral-100 rounded-full transition-colors"
            aria-label="닫기"
          >
            <X className="w-5 h-5 text-neutral-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Property Type Selection */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-3">
              재산 유형
            </label>
            <div className="grid grid-cols-4 gap-2">
              {(Object.keys(PROPERTY_TYPE_LABELS) as PropertyType[]).map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setFormData((prev) => ({ ...prev, property_type: type }))}
                  className={`flex flex-col items-center p-3 rounded-xl border-2 transition-all ${
                    formData.property_type === type
                      ? 'border-primary bg-primary-light text-primary'
                      : 'border-neutral-200 hover:border-primary/50 text-neutral-600'
                  }`}
                >
                  {PROPERTY_TYPE_ICONS[type]}
                  <span className="text-xs mt-1 font-medium">{PROPERTY_TYPE_LABELS[type]}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Owner Selection */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-3">
              소유자
            </label>
            <div className="flex gap-2">
              {(Object.keys(PROPERTY_OWNER_LABELS) as PropertyOwner[]).map((owner) => (
                <button
                  key={owner}
                  type="button"
                  onClick={() => setFormData((prev) => ({ ...prev, owner }))}
                  className={`flex-1 py-3 px-4 rounded-xl border-2 font-medium transition-all ${
                    formData.owner === owner
                      ? owner === 'plaintiff'
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : owner === 'defendant'
                        ? 'border-red-500 bg-red-50 text-red-700'
                        : 'border-purple-500 bg-purple-50 text-purple-700'
                      : 'border-neutral-200 hover:border-neutral-300 text-neutral-600'
                  }`}
                >
                  {PROPERTY_OWNER_LABELS[owner]}
                </button>
              ))}
            </div>
          </div>

          {/* Estimated Value */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              추정 가치 (원)
            </label>
            <div className="relative">
              <input
                type="text"
                value={valueInput}
                onChange={handleValueChange}
                placeholder="0"
                className="w-full px-4 py-3 pr-12 border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent text-right text-lg font-semibold"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-neutral-500">
                원
              </span>
            </div>
            {formData.estimated_value > 0 && (
              <p className="mt-1 text-sm text-neutral-500 text-right">
                {formData.estimated_value >= 100000000
                  ? `${(formData.estimated_value / 100000000).toFixed(1)}억원`
                  : formData.estimated_value >= 10000
                  ? `${(formData.estimated_value / 10000).toFixed(0)}만원`
                  : `${formData.estimated_value.toLocaleString()}원`}
              </p>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              설명 (선택)
            </label>
            <input
              type="text"
              value={formData.description || ''}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, description: e.target.value }))
              }
              placeholder="예: 서울 강남구 아파트 84m2"
              className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          {/* Premarital Checkbox */}
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_premarital"
              checked={formData.is_premarital}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, is_premarital: e.target.checked }))
              }
              className="w-5 h-5 rounded border-neutral-300 text-primary focus:ring-primary"
            />
            <label htmlFor="is_premarital" className="text-sm text-neutral-700">
              혼인 전 취득 재산 (특유재산)
            </label>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              메모 (선택)
            </label>
            <textarea
              value={formData.notes || ''}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, notes: e.target.value }))
              }
              placeholder="추가 메모..."
              rows={2}
              className="w-full px-4 py-3 border border-neutral-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
            />
          </div>

          {/* Submit Buttons */}
          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-3 px-4 border border-neutral-300 text-neutral-700 rounded-xl font-medium hover:bg-neutral-50 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isSubmitting || formData.estimated_value === 0}
              className="flex-1 py-3 px-4 bg-primary text-white rounded-xl font-medium hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                '추가 중...'
              ) : (
                <>
                  <Plus className="w-5 h-5" />
                  재산 추가
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
