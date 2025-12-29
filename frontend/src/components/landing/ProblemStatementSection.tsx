/**
 * ProblemStatementSection Component
 * Plan 3.19.1 - Problem Statement (이런 고민 있으셨나요?)
 *
 * Features:
 * - Empathetic problem statement targeting law firm pain points
 * - 4 pain points with icons
 * - Responsive grid layout (1 → 2 → 4 columns)
 * - Calm Control design system compliance
 */

import { FolderOpen, Clock, FileText, Search } from 'lucide-react';

export default function ProblemStatementSection() {
  const painPoints = [
    {
      id: 1,
      icon: FolderOpen,
      text: '수백 개 카톡 대화, 일일이 읽기 힘드시죠?',
      ariaLabel: '폴더 아이콘',
    },
    {
      id: 2,
      icon: Clock,
      text: '증거 정리에만 며칠씩 걸리시나요?',
      ariaLabel: '시계 아이콘',
    },
    {
      id: 3,
      icon: FileText,
      text: '초안 작성할 때마다 반복 작업에 지치셨나요?',
      ariaLabel: '문서 아이콘',
    },
    {
      id: 4,
      icon: Search,
      text: '중요한 증거를 놓칠까 불안하신가요?',
      ariaLabel: '검색 아이콘',
    },
  ];

  return (
    <section
      className="py-16 px-6 bg-white"
      aria-label="고객이 겪는 문제점"
    >
      <div className="max-w-7xl mx-auto">
        <div className="space-y-12">
          {/* Section Title */}
          <h2 className="text-4xl font-bold text-secondary text-center">
            이런 고민 있으셨나요?
          </h2>

          {/* Pain Points Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {painPoints.map((point) => {
              const IconComponent = point.icon;
              return (
                <div
                  key={point.id}
                  className="text-center space-y-4"
                >
                  {/* Icon */}
                  <div className="flex justify-center">
                    <IconComponent
                      className="w-12 h-12 text-accent"
                      aria-label={point.ariaLabel}
                    />
                  </div>

                  {/* Pain Point Text */}
                  <p className="text-neutral-700 leading-relaxed">
                    {point.text}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
