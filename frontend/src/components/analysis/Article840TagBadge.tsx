/**
 * Article 840 Tag Badge Component
 * 민법 840조 이혼 사유 태그를 시각화하는 컴포넌트
 */

import { Article840Category } from '@/types/evidence';

interface Article840TagBadgeProps {
  category: Article840Category;
  size?: 'sm' | 'md' | 'lg';
}

// 카테고리별 설정
const categoryConfig: Record<
  Article840Category,
  { label: string; shortLabel: string; className: string; description: string }
> = {
  adultery: {
    label: '부정행위',
    shortLabel: '부정',
    className: 'bg-red-100 text-red-700 border-red-200',
    description: '제1호: 배우자의 부정행위',
  },
  desertion: {
    label: '악의의 유기',
    shortLabel: '유기',
    className: 'bg-orange-100 text-orange-700 border-orange-200',
    description: '제2호: 악의의 유기',
  },
  mistreatment_by_inlaws: {
    label: '시가 부당대우',
    shortLabel: '시가',
    className: 'bg-amber-100 text-amber-700 border-amber-200',
    description: '제3호: 배우자 직계존속의 부당대우',
  },
  harm_to_own_parents: {
    label: '친가 피해',
    shortLabel: '친가',
    className: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    description: '제4호: 자기 직계존속 피해',
  },
  unknown_whereabouts: {
    label: '생사불명',
    shortLabel: '생사',
    className: 'bg-purple-100 text-purple-700 border-purple-200',
    description: '제5호: 생사불명 3년',
  },
  irreconcilable_differences: {
    label: '혼인 지속 곤란',
    shortLabel: '곤란',
    className: 'bg-blue-100 text-blue-700 border-blue-200',
    description: '제6호: 혼인 지속 곤란사유',
  },
  general: {
    label: '일반 증거',
    shortLabel: '일반',
    className: 'bg-gray-100 text-gray-600 border-gray-200',
    description: '특정 조항에 해당하지 않는 일반 증거',
  },
};

const sizeClasses = {
  sm: 'text-xs px-1.5 py-0.5',
  md: 'text-sm px-2 py-1',
  lg: 'text-base px-3 py-1.5',
};

export function Article840TagBadge({
  category,
  size = 'md',
}: Article840TagBadgeProps) {
  const config = categoryConfig[category];

  return (
    <span
      className={`inline-flex items-center font-medium rounded-md border ${config.className} ${sizeClasses[size]}`}
      title={config.description}
    >
      {size === 'sm' ? config.shortLabel : config.label}
    </span>
  );
}

// 여러 태그를 표시하는 컴포넌트
interface Article840TagListProps {
  categories: Article840Category[];
  size?: 'sm' | 'md' | 'lg';
  maxVisible?: number;
}

export function Article840TagList({
  categories,
  size = 'md',
  maxVisible = 3,
}: Article840TagListProps) {
  const visibleCategories = categories.slice(0, maxVisible);
  const hiddenCount = categories.length - maxVisible;

  return (
    <div className="flex flex-wrap gap-1.5">
      {visibleCategories.map((category) => (
        <Article840TagBadge key={category} category={category} size={size} />
      ))}
      {hiddenCount > 0 && (
        <span
          className={`inline-flex items-center font-medium rounded-md bg-gray-100 text-gray-500 border border-gray-200 ${sizeClasses[size]}`}
          title={`${hiddenCount}개 더 보기`}
        >
          +{hiddenCount}
        </span>
      )}
    </div>
  );
}
