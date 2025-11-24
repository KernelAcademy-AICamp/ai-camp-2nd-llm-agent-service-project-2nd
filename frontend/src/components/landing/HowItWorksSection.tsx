/**
 * HowItWorksSection Component
 * Plan 3.19.1 - How It Works (4단계 프로세스)
 *
 * Features:
 * - Section title: "4단계로 완성되는 초안"
 * - 4-step process flow with numbered badges
 * - Each step: number, icon, title, description
 * - Responsive grid layout (1 → 2 → 4 columns)
 * - Visual flow representation
 */

import { Upload, Sparkles, ListChecks, Download } from 'lucide-react';

export default function HowItWorksSection() {
  const steps = [
    {
      number: 1,
      icon: Upload,
      title: '증거 업로드',
      description: '드래그 앤 드롭',
      ariaLabel: '업로드 아이콘',
    },
    {
      number: 2,
      icon: Sparkles,
      title: 'AI 자동 분석',
      description: 'OCR, STT, 감정 분석',
      ariaLabel: '스파클 아이콘 - AI 분석',
    },
    {
      number: 3,
      icon: ListChecks,
      title: '타임라인 검토',
      description: '증거 확인',
      ariaLabel: '체크리스트 아이콘',
    },
    {
      number: 4,
      icon: Download,
      title: '초안 다운로드',
      description: 'HWP/DOCX',
      ariaLabel: '다운로드 아이콘',
    },
  ];

  return (
    <section
      className="py-20 px-6 bg-white"
      aria-label="사용 방법 4단계"
    >
      <div className="max-w-7xl mx-auto">
        <div className="space-y-12">
          {/* Section Title */}
          <h2 className="text-4xl font-bold text-deep-trust-blue text-center">
            4단계로 완성되는 초안
          </h2>

          {/* Steps Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {steps.map((step) => {
              const IconComponent = step.icon;
              return (
                <div
                  key={step.number}
                  className="text-center space-y-4"
                >
                  {/* Step Number Badge */}
                  <div className="flex justify-center">
                    <div className="w-12 h-12 bg-accent rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-lg">
                        {step.number}
                      </span>
                    </div>
                  </div>

                  {/* Icon */}
                  <div className="flex justify-center">
                    <IconComponent
                      className="w-8 h-8 text-deep-trust-blue"
                      aria-label={step.ariaLabel}
                    />
                  </div>

                  {/* Step Title */}
                  <h3 className="text-xl font-bold text-deep-trust-blue">
                    {step.title}
                  </h3>

                  {/* Step Description */}
                  <p className="text-gray-600">
                    {step.description}
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
