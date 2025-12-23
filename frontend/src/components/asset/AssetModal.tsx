/**
 * AssetModal - Independent Asset Add/Edit Modal
 * Extracted from AssetSummaryTab for use anywhere in the app
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { X, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import type { LegacyAsset as Asset, AssetType, CreateAssetRequest } from '@/types/asset';
import { ASSET_TYPE_CONFIG, OWNERSHIP_CONFIG } from '@/types/asset';
import { createAsset, updateAsset } from '@/lib/api/assets';

interface AssetModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseId: string;
  asset?: Asset; // For editing
  onSuccess?: () => void;
}

export function AssetModal({
  isOpen,
  onClose,
  caseId,
  asset,
  onSuccess,
}: AssetModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<CreateAssetRequest>({
    asset_type: 'real_estate',
    name: '',
    current_value: 0,
    ownership: 'joint',
    division_ratio_plaintiff: 50,
    division_ratio_defendant: 50,
  });

  // Reset form when modal opens/closes or asset changes
  useEffect(() => {
    if (isOpen) {
      if (asset) {
        setFormData({
          asset_type: asset.asset_type,
          name: asset.name,
          current_value: asset.current_value,
          ownership: asset.ownership,
          division_ratio_plaintiff: asset.division_ratio_plaintiff,
          division_ratio_defendant: asset.division_ratio_defendant,
        });
      } else {
        setFormData({
          asset_type: 'real_estate',
          name: '',
          current_value: 0,
          ownership: 'joint',
          division_ratio_plaintiff: 50,
          division_ratio_defendant: 50,
        });
      }
    }
  }, [isOpen, asset]);

  const handleClose = useCallback(() => {
    setFormData({
      asset_type: 'real_estate',
      name: '',
      current_value: 0,
      ownership: 'joint',
      division_ratio_plaintiff: 50,
      division_ratio_defendant: 50,
    });
    onClose();
  }, [onClose]);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.name || formData.current_value <= 0) {
      toast.error('재산명과 가치를 입력해주세요.');
      return;
    }

    setIsSubmitting(true);

    try {
      if (asset) {
        // Update existing asset
        await updateAsset(caseId, asset.id, formData);
        toast.success('재산 정보가 수정되었습니다.');
        onSuccess?.();
        handleClose();
      } else {
        // Create new asset
        await createAsset(caseId, formData);
        toast.success('재산이 추가되었습니다.');
        onSuccess?.();
        handleClose();
      }
    } catch {
      toast.error('저장에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  }, [caseId, formData, asset, onSuccess, handleClose]);

  // Handle division ratio changes (keep total at 100%)
  const handlePlaintiffRatioChange = (value: number) => {
    const plaintiff = Math.max(0, Math.min(100, value));
    setFormData({
      ...formData,
      division_ratio_plaintiff: plaintiff,
      division_ratio_defendant: 100 - plaintiff,
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-neutral-800 rounded-xl shadow-xl w-full max-w-lg mx-4">
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-neutral-700">
          <h4 className="text-lg font-semibold text-[var(--color-text-primary)]">
            {asset ? '재산 정보 수정' : '재산 추가'}
          </h4>
          <button
            onClick={handleClose}
            className="p-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-700"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Type and Ownership */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1">
                재산 유형 <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.asset_type}
                onChange={(e) => setFormData({ ...formData, asset_type: e.target.value as AssetType })}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
              >
                {Object.entries(ASSET_TYPE_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1">
                소유권
              </label>
              <select
                value={formData.ownership}
                onChange={(e) => setFormData({ ...formData, ownership: e.target.value as 'plaintiff' | 'defendant' | 'joint' })}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
              >
                {Object.entries(OWNERSHIP_CONFIG).map(([key, config]) => (
                  <option key={key} value={key}>{config.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Name */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1">
              재산명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="예: 강남 아파트, 현대차 주식"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
              required
            />
          </div>

          {/* Current Value */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-1">
              현재 가치 (원) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={formData.current_value || ''}
              onChange={(e) => setFormData({ ...formData, current_value: parseInt(e.target.value, 10) || 0 })}
              placeholder="0"
              className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-neutral-600 bg-white dark:bg-neutral-700 text-[var(--color-text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)]"
              min="0"
              required
            />
          </div>

          {/* Division Ratio */}
          <div>
            <label className="block text-sm font-medium text-[var(--color-text-primary)] mb-2">
              분할 비율
            </label>
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <label className="block text-xs text-[var(--color-text-secondary)] mb-1">
                  원고 ({formData.division_ratio_plaintiff}%)
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={formData.division_ratio_plaintiff}
                  onChange={(e) => handlePlaintiffRatioChange(parseInt(e.target.value, 10))}
                  className="w-full h-2 bg-gray-200 dark:bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                />
              </div>
              <div className="text-sm text-[var(--color-text-secondary)] font-medium whitespace-nowrap">
                {formData.division_ratio_plaintiff} : {formData.division_ratio_defendant}
              </div>
              <div className="flex-1">
                <label className="block text-xs text-[var(--color-text-secondary)] mb-1 text-right">
                  피고 ({formData.division_ratio_defendant}%)
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={formData.division_ratio_defendant}
                  onChange={(e) => handlePlaintiffRatioChange(100 - parseInt(e.target.value, 10))}
                  className="w-full h-2 bg-gray-200 dark:bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                />
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] rounded-lg border border-gray-300 dark:border-neutral-600 hover:bg-gray-100 dark:hover:bg-neutral-700 transition-colors disabled:opacity-50"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] transition-colors disabled:opacity-50 flex items-center"
            >
              {isSubmitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {asset ? '수정' : '추가'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AssetModal;
