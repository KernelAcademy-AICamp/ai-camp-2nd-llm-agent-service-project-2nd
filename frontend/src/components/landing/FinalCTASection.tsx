/**
 * FinalCTASection Component
 * Plan 3.19.1 - Final CTA (전환 유도)
 *
 * Features:
 * - Section title: "지금 바로 시작하세요"
 * - Subtext: "14일 무료 체험, 신용카드 필요 없음"
 * - Large primary CTA button: "무료로 시작하기"
 * - Secondary button: "영업팀과 상담하기"
 * - Center-aligned, conversion-focused design
 */

import Link from 'next/link';
import { Button } from '@/components/primitives';

export default function FinalCTASection() {
  return (
    <section className="py-20 px-6 bg-neutral-50" aria-label="최종 행동 유도">
      <div className="max-w-4xl mx-auto">
        <div className="text-center space-y-8">
          {/* Section Title */}
          <h2 className="text-4xl font-bold text-secondary">
            지금 바로 시작하세요
          </h2>

          {/* Subtext */}
          <p className="text-xl text-neutral-600">
            14일 무료 체험, 신용카드 필요 없음
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            {/* Primary CTA */}
            <Link
              href="/signup"
              aria-label="무료로 시작하기 - 14일 무료 체험, 신용카드 필요 없음"
            >
              <Button
                variant="primary"
                size="lg"
                className="text-lg px-8 py-4 shadow-lg hover:shadow-xl"
              >
                무료로 시작하기
              </Button>
            </Link>

            {/* Secondary CTA */}
            <Link
              href="mailto:sales@legalevidence.hub"
              aria-label="영업팀과 상담하기 - 이메일 문의"
            >
              <Button
                variant="ghost"
                size="lg"
                className="text-lg px-8 py-4 bg-neutral-100 hover:bg-neutral-200"
              >
                영업팀과 상담하기
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
