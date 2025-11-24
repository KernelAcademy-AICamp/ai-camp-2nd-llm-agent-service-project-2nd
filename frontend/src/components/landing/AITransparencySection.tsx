/**
 * AITransparencySection Component
 * Plan 3.19.1 - AI Transparency & Security (법률 컴플라이언스 준수)
 *
 * Features:
 * - Section title: "법률 컴플라이언스 준수"
 * - 2-column layout: AI Transparency + Security & Compliance
 * - Trust badge icons (CheckCircle, Shield, Lock)
 * - Responsive grid layout
 */

import { CheckCircle, Shield } from 'lucide-react';

export default function AITransparencySection() {
  const transparencyFeatures = [
    {
      id: 1,
      icon: CheckCircle,
      text: '모든 AI 결과는 근거 증거 표시',
      ariaLabel: '체크 아이콘',
    },
    {
      id: 2,
      icon: CheckCircle,
      text: '최종 결정은 변호사님께',
      ariaLabel: '체크 아이콘',
    },
  ];

  const securityFeatures = [
    {
      id: 1,
      icon: Shield,
      text: 'AES-256 암호화',
      ariaLabel: '방패 아이콘',
    },
    {
      id: 2,
      icon: Shield,
      text: 'PIPA(개인정보보호법) 준수',
      ariaLabel: '방패 아이콘',
    },
    {
      id: 3,
      icon: Shield,
      text: 'ISO 27001 인증 (준비 중)',
      ariaLabel: '방패 아이콘',
    },
  ];

  return (
    <section
      className="py-20 px-6 bg-calm-grey"
      aria-label="AI 투명성 및 보안"
    >
      <div className="max-w-7xl mx-auto">
        <div className="space-y-12">
          {/* Section Title */}
          <h2 className="text-4xl font-bold text-deep-trust-blue text-center">
            법률 컴플라이언스 준수
          </h2>

          {/* 2-Column Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
            {/* Left Column: AI Transparency */}
            <div className="space-y-6">
              <h3 className="text-2xl font-bold text-deep-trust-blue">
                AI 투명성
              </h3>

              <div className="space-y-4">
                {transparencyFeatures.map((feature) => {
                  const IconComponent = feature.icon;
                  return (
                    <div key={feature.id} className="flex items-start space-x-3">
                      <IconComponent
                        className="w-6 h-6 text-accent flex-shrink-0 mt-1"
                        aria-label={feature.ariaLabel}
                      />
                      <p className="text-gray-600 leading-relaxed">
                        {feature.text}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right Column: Security & Compliance */}
            <div className="space-y-6">
              <h3 className="text-2xl font-bold text-deep-trust-blue">
                보안 및 규정 준수
              </h3>

              <div className="space-y-4">
                {securityFeatures.map((feature) => {
                  const IconComponent = feature.icon;
                  return (
                    <div key={feature.id} className="flex items-start space-x-3">
                      <IconComponent
                        className="w-6 h-6 text-accent flex-shrink-0 mt-1"
                        aria-label={feature.ariaLabel}
                      />
                      <p className="text-gray-600 leading-relaxed">
                        {feature.text}
                      </p>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
