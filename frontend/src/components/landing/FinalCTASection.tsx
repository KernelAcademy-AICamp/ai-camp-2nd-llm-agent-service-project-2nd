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

export default function FinalCTASection() {
  return (
    <section
      className="py-20 px-6 bg-calm-grey"
      aria-label="최종 행동 유도"
    >
      <div className="max-w-4xl mx-auto">
        <div className="text-center space-y-8">
          {/* Section Title */}
          <h2 className="text-4xl font-bold text-deep-trust-blue">
            지금 바로 시작하세요
          </h2>

          {/* Subtext */}
          <p className="text-xl text-gray-600">
            14일 무료 체험, 신용카드 필요 없음
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            {/* Primary CTA */}
            <Link
              href="/signup"
              className="btn-primary text-lg px-8 py-4 shadow-lg hover:shadow-xl transition-shadow"
            >
              무료로 시작하기
            </Link>

            {/* Secondary CTA */}
            <Link
              href="mailto:sales@legalevidence.hub"
              className="bg-gray-100 text-deep-trust-blue text-lg px-8 py-4 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
            >
              영업팀과 상담하기
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
