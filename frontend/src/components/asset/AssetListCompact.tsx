/**
 * AssetListCompact Component
 * Compact asset list for DataPanel sidebar
 * LDS2 Compact density applied
 */

'use client';

import { Building, Wallet, TrendingUp, Landmark, Car, Shield, CreditCard, Box } from 'lucide-react';
import type { LegacyAsset as Asset, AssetType } from '@/types/asset';

const ASSET_TYPE_ICONS: Record<AssetType, typeof Building> = {
  real_estate: Building,
  savings: Wallet,
  stocks: TrendingUp,
  retirement: Landmark,
  vehicle: Car,
  insurance: Shield,
  debt: CreditCard,
  other: Box,
  // Legacy types
  financial: Wallet,
  business: Building,
  personal: Box,
};

const ASSET_TYPE_COLORS: Record<AssetType, string> = {
  real_estate: 'text-emerald-500',
  savings: 'text-blue-500',
  stocks: 'text-purple-500',
  retirement: 'text-orange-500',
  vehicle: 'text-cyan-500',
  insurance: 'text-indigo-500',
  debt: 'text-red-500',
  other: 'text-gray-500',
  financial: 'text-blue-500',
  business: 'text-emerald-500',
  personal: 'text-gray-500',
};

// Format currency in compact Korean style
function formatCompact(value: number): string {
  if (value >= 100000000) {
    return `${(value / 100000000).toFixed(1)}억`;
  }
  if (value >= 10000) {
    return `${Math.floor(value / 10000).toLocaleString()}만`;
  }
  return `${value.toLocaleString()}원`;
}

interface AssetListCompactProps {
  assets: Asset[];
  onItemClick?: (asset: Asset) => void;
  maxItems?: number;
}

export function AssetListCompact({
  assets,
  onItemClick,
  maxItems = 5,
}: AssetListCompactProps) {
  const displayItems = assets.slice(0, maxItems);

  if (displayItems.length === 0) {
    return (
      <div className="text-xs text-[var(--color-text-secondary)] py-2">
        등록된 재산이 없습니다.
      </div>
    );
  }

  // Calculate totals
  const totalAssets = assets.reduce((sum, a) => a.asset_type !== 'debt' ? sum + a.current_value : sum, 0);
  const totalDebts = assets.reduce((sum, a) => a.asset_type === 'debt' ? sum + a.current_value : sum, 0);

  return (
    <div className="space-y-1">
      {/* Summary row */}
      <div className="flex items-center justify-between px-2 py-1 bg-gray-50 dark:bg-neutral-750 rounded text-[10px]">
        <span className="text-[var(--color-text-secondary)]">자산 {formatCompact(totalAssets)}</span>
        {totalDebts > 0 && (
          <span className="text-red-500">부채 -{formatCompact(totalDebts)}</span>
        )}
      </div>

      {/* Asset items */}
      {displayItems.map((asset) => {
        const Icon = ASSET_TYPE_ICONS[asset.asset_type] || ASSET_TYPE_ICONS.other;
        const iconColor = ASSET_TYPE_COLORS[asset.asset_type] || ASSET_TYPE_COLORS.other;
        const isDebt = asset.asset_type === 'debt';

        return (
          <div
            key={asset.id}
            onClick={() => onItemClick?.(asset)}
            className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-gray-100 dark:hover:bg-neutral-700 cursor-pointer transition-colors"
          >
            <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${iconColor}`} />
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-[var(--color-text-primary)] truncate">
                {asset.name}
              </p>
            </div>
            <span className={`text-xs font-medium ${isDebt ? 'text-red-500' : 'text-[var(--color-text-primary)]'}`}>
              {isDebt && '-'}{formatCompact(asset.current_value)}
            </span>
          </div>
        );
      })}
      {assets.length > maxItems && (
        <p className="text-[10px] text-[var(--color-text-secondary)] text-center py-1">
          +{assets.length - maxItems}건 더보기
        </p>
      )}
    </div>
  );
}

export default AssetListCompact;
