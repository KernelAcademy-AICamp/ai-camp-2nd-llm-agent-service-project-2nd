/**
 * TestimonialsSection Component
 * Plan 3.19.1 - Testimonials (실제 후기)
 *
 * Features:
 * - Section title: "이미 사용 중인 변호사님들의 평가"
 * - 3 testimonial cards with profile, name, org, rating, quote
 * - Star ratings display
 * - Profile initials in circular badges
 * - Responsive grid layout
 */

import { Star } from 'lucide-react';

export default function TestimonialsSection() {
  const testimonials = [
    {
      id: 1,
      name: '김현수 변호사',
      organization: '법무법인 정의',
      rating: 5,
      initials: '김',
      quote: '증거 정리 시간이 1/10로 줄었습니다. AI 분석 덕분에 핵심 증거를 놓치지 않게 되었어요.',
    },
    {
      id: 2,
      name: '박지영 변호사',
      organization: '서울 가정법률 사무소',
      rating: 5,
      initials: '박',
      quote: '초안 생성 기능이 정말 효율적입니다. 이제 의뢰인 상담에 더 많은 시간을 할애할 수 있어요.',
    },
    {
      id: 3,
      name: '이준호 변호사',
      organization: '법무법인 한결',
      rating: 5,
      initials: '이',
      quote: '카톡 대화 분석이 놀랍도록 정확합니다. 유책사유 자동 태깅으로 케이스 파악이 빨라졌어요.',
    },
  ];

  return (
    <section
      className="py-20 px-6 bg-neutral-50"
      aria-label="고객 후기"
    >
      <div className="max-w-7xl mx-auto">
        <div className="space-y-12">
          {/* Section Title */}
          <h2 className="text-4xl font-bold text-secondary text-center">
            이미 사용 중인 변호사님들의 평가
          </h2>

          {/* Testimonials Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {testimonials.map((testimonial) => (
              <div
                key={testimonial.id}
                className="bg-white rounded-xl shadow-lg p-8 space-y-4 hover:shadow-xl transition-shadow"
              >
                {/* Profile & Rating */}
                <div className="flex items-center justify-between">
                  {/* Profile Initial Badge */}
                  <div className="w-12 h-12 bg-accent rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-lg">
                      {testimonial.initials}
                    </span>
                  </div>

                  {/* Star Rating */}
                  <div className="flex items-center space-x-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <Star
                        key={star}
                        className={`w-4 h-4 ${
                          star <= testimonial.rating
                            ? 'fill-accent text-accent'
                            : 'fill-gray-300 text-gray-300'
                        }`}
                        aria-label={`별 ${star}`}
                      />
                    ))}
                  </div>
                </div>

                {/* Reviewer Info */}
                <div>
                  <h3 className="text-lg font-bold text-secondary">
                    {testimonial.name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {testimonial.organization}
                  </p>
                </div>

                {/* Testimonial Quote */}
                <p className="text-neutral-600 leading-relaxed">
                  "{testimonial.quote}"
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
