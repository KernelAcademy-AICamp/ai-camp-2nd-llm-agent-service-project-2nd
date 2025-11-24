/**
 * SocialProofSection Component
 * Plan 3.19.1 - Social Proof
 *
 * Features:
 * - Trust badge: "50개 로펌 사용 중"
 * - Average rating display with stars
 * - Logo slider for law firms
 */

import { Star } from 'lucide-react';

export default function SocialProofSection() {
  // Placeholder law firms (to be replaced with real data)
  const lawFirms = [
    { id: 1, name: '법무법인 A', logo: '/images/logos/firm-a.png' },
    { id: 2, name: '법무법인 B', logo: '/images/logos/firm-b.png' },
    { id: 3, name: '법무법인 C', logo: '/images/logos/firm-c.png' },
    { id: 4, name: '법무법인 D', logo: '/images/logos/firm-d.png' },
    { id: 5, name: '법무법인 E', logo: '/images/logos/firm-e.png' },
  ];

  return (
    <section
      className="py-12 px-6 bg-gray-50 text-center"
      aria-label="고객 신뢰도 및 실적"
    >
      <div className="max-w-7xl mx-auto">
        <div className="space-y-8">
          {/* Trust Badge */}
          <div className="space-y-2">
            <p className="text-lg text-gray-700">
              <span className="font-bold text-deep-trust-blue">50개</span> 로펌 사용 중
            </p>
            <p className="text-sm text-gray-500">신뢰받는 주요 로펌들이 선택한 솔루션</p>
          </div>

          {/* Rating */}
          <div className="flex flex-col items-center space-y-2">
            <div className="flex items-center space-x-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className="w-5 h-5 fill-accent text-accent"
                  aria-label={`별 ${star}`}
                />
              ))}
            </div>
            <p className="text-lg">
              <span className="font-bold text-accent">5.0</span>
              <span className="text-gray-600"> / 5.0 만점</span>
            </p>
          </div>

          {/* Logo Slider */}
          <div className="mt-8">
            <div className="overflow-hidden">
              <div className="flex items-center justify-center gap-8 flex-wrap">
                {lawFirms.map((firm) => (
                  <div
                    key={firm.id}
                    className="w-32 h-16 bg-white rounded-lg shadow-sm flex items-center justify-center p-4 border border-gray-100"
                  >
                    <img
                      src={firm.logo}
                      alt={`${firm.name} 로고`}
                      className="max-w-full max-h-full object-contain opacity-60 hover:opacity-100 transition-opacity"
                      onError={(e) => {
                        // Fallback to placeholder text
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        const parent = target.parentElement;
                        if (parent && !parent.querySelector('.fallback-text')) {
                          const span = document.createElement('span');
                          span.className = 'fallback-text text-xs text-gray-400 font-medium';
                          span.textContent = firm.name;
                          parent.appendChild(span);
                        }
                      }}
                    />
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
