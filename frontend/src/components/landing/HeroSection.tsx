/**
 * HeroSection Component
 * Plan 3.19.1 - Hero Section
 *
 * Features:
 * - Compelling headline with 90% time savings claim
 * - Clear value proposition subheadline
 * - Prominent CTA button
 * - Hero image showcasing product UI
 */

import Link from 'next/link';
import Image from 'next/image';
import { Button } from '@/components/primitives';

export default function HeroSection() {
  return (
    <section className="py-20 px-6 bg-neutral-50" aria-label="Hero section">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Content */}
          <div className="space-y-8">
            <h1 className="text-5xl font-bold text-secondary leading-tight">
              증거 정리 시간 90% 단축
            </h1>

            <p className="text-xl text-neutral-600 leading-relaxed">
              AI가 이혼 소송 증거를 자동 분석하고 초안을 작성합니다
            </p>

            <div className="pt-4">
              <Link href="/signup">
                <Button
                  variant="primary"
                  size="lg"
                  className="text-lg px-8 py-4 shadow-lg hover:shadow-xl"
                  aria-label="무료로 시작하기 - 14일 무료 체험"
                >
                  무료로 시작하기
                </Button>
              </Link>
            </div>
          </div>

          {/* Hero Image */}
          <div className="relative">
            <div className="relative w-full h-96 bg-white rounded-2xl shadow-2xl overflow-hidden border border-neutral-100">
              <Image
                src="/images/hero-dashboard.png"
                alt="Legal Evidence Hub 제품 미리보기 - 증거 관리 대시보드"
                fill
                sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 40vw"
                className="object-cover"
                priority
                onError={(e) => {
                  // Fallback to placeholder
                  const target = e.target as HTMLImageElement;
                  target.src = '/images/placeholder-dashboard.svg';
                }}
              />
            </div>

            {/* Decorative element */}
            <div
              className="absolute -z-10 top-8 right-8 w-72 h-72 bg-primary opacity-10 rounded-full blur-3xl"
              aria-hidden="true"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
