/**
 * SolutionSection Component
 * Plan 3.19.1 - Solution (3가지 핵심 기능)
 *
 * Features:
 * - Section title: "Legal Evidence Hub가 해결합니다"
 * - 3-column layout showcasing core features
 * - Each feature: icon, heading, description
 * - Card-based design with shadows
 * - Responsive grid layout
 */

import { Brain, Clock, FileCheck } from 'lucide-react';

export default function SolutionSection() {
  const features = [
    {
      id: 1,
      icon: Brain,
      title: '자동 증거 분석',
      description: '이미지/음성/PDF를 AI가 자동 분류 및 요약',
      ariaLabel: '뇌 아이콘 - AI 분석',
    },
    {
      id: 2,
      icon: Clock,
      title: '스마트 타임라인',
      description: '시간순 증거 정리, 유책사유 자동 태깅',
      ariaLabel: '시계 아이콘 - 타임라인',
    },
    {
      id: 3,
      icon: FileCheck,
      title: '초안 자동 생성',
      description: 'RAG 기반 사실 인용, 답변서 초안 1분 생성',
      ariaLabel: '체크 문서 아이콘 - 자동 생성',
    },
  ];

  return (
    <section
      className="py-20 px-6 bg-calm-grey"
      aria-label="솔루션 핵심 기능"
    >
      <div className="max-w-7xl mx-auto">
        <div className="space-y-12">
          {/* Section Title */}
          <h2 className="text-4xl font-bold text-deep-trust-blue text-center">
            Legal Evidence Hub가 해결합니다
          </h2>

          {/* Features Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {features.map((feature) => {
              const IconComponent = feature.icon;
              return (
                <div
                  key={feature.id}
                  className="bg-white rounded-xl shadow-lg p-8 text-center space-y-4 hover:shadow-xl transition-shadow"
                >
                  {/* Icon */}
                  <div className="flex justify-center">
                    <IconComponent
                      className="w-12 h-12 text-accent"
                      aria-label={feature.ariaLabel}
                    />
                  </div>

                  {/* Feature Title */}
                  <h3 className="text-2xl font-bold text-deep-trust-blue">
                    {feature.title}
                  </h3>

                  {/* Feature Description */}
                  <p className="text-gray-600 leading-relaxed">
                    {feature.description}
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
