/**
 * PricingSection Component
 * Plan 3.19.1 - Pricing (명확한 가격 정책)
 *
 * Features:
 * - Section title: "투명한 가격, 숨은 비용 없음"
 * - 3-tier pricing: Basic, Professional (highlighted), Enterprise
 * - Feature lists with checkmarks
 * - 14-day free trial emphasis
 * - Responsive grid layout
 */

import { Check } from 'lucide-react';
import Link from 'next/link';

export default function PricingSection() {
  const plans = [
    {
      id: 1,
      name: 'Basic',
      price: '₩49,000',
      period: '월',
      target: '개인 변호사',
      popular: false,
      features: [
        '월 50건 증거 처리',
        '기본 AI 분석',
        '타임라인 정리',
        '초안 자동 생성',
        '이메일 지원',
      ],
    },
    {
      id: 2,
      name: 'Professional',
      price: '₩99,000',
      period: '월',
      target: '소형 로펌',
      popular: true,
      features: [
        '월 200건 증거 처리',
        '고급 AI 분석',
        '다중 케이스 관리',
        '우선 이메일 지원',
        '맞춤 템플릿',
        '팀 협업 기능',
      ],
    },
    {
      id: 3,
      name: 'Enterprise',
      price: '₩199,000',
      period: '월',
      target: '대형 로펌',
      customFeatures: '맞춤 기능',
      popular: false,
      features: [
        '무제한 증거 처리',
        '전담 AI 모델',
        '기업용 보안',
        '전화 지원',
        'API 연동',
        '온프레미스 옵션',
      ],
    },
  ];

  return (
    <section
      className="py-20 px-6 bg-white"
      aria-label="가격 플랜"
    >
      <div className="max-w-7xl mx-auto">
        <div className="space-y-12">
          {/* Section Title */}
          <div className="text-center space-y-4">
            <h2 className="text-4xl font-bold text-deep-trust-blue">
              투명한 가격, 숨은 비용 없음
            </h2>
            <p className="text-xl text-accent font-semibold">
              14일 무료 체험
            </p>
          </div>

          {/* Pricing Cards Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className={`bg-white rounded-xl shadow-lg p-8 text-center space-y-6 transition-transform hover:shadow-xl ${
                  plan.popular ? 'ring-2 ring-accent scale-105' : ''
                }`}
              >
                {/* Popular Badge */}
                {plan.popular && (
                  <div className="inline-block">
                    <span className="bg-accent text-white text-sm font-semibold px-4 py-1 rounded-full">
                      가장 인기
                    </span>
                  </div>
                )}

                {/* Plan Name */}
                <h3 className="text-2xl font-bold text-deep-trust-blue">
                  {plan.name}
                </h3>

                {/* Price */}
                <div className="space-y-1">
                  <div className="text-4xl font-bold text-deep-trust-blue">
                    {plan.price}
                    <span className="text-lg text-gray-600">/{plan.period}</span>
                  </div>
                  <p className="text-gray-600">
                    {plan.target}
                    {plan.customFeatures && `, ${plan.customFeatures}`}
                  </p>
                </div>

                {/* Features List */}
                <div className="space-y-3 text-left pt-4">
                  {plan.features.map((feature, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <Check
                        className="w-5 h-5 text-accent flex-shrink-0 mt-0.5"
                        aria-label="체크 아이콘"
                      />
                      <span className="text-gray-600">{feature}</span>
                    </div>
                  ))}
                </div>

                {/* CTA Button */}
                <div className="pt-4">
                  <Link
                    href="/signup"
                    className={`block w-full py-3 rounded-lg font-semibold transition-colors ${
                      plan.popular
                        ? 'btn-primary'
                        : 'bg-gray-100 text-deep-trust-blue hover:bg-gray-200'
                    }`}
                  >
                    시작하기
                  </Link>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
