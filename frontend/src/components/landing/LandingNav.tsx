/**
 * LandingNav Component
 * Plan 3.19.1 - Navigation Bar (고정 헤더)
 *
 * Features:
 * - Sticky navigation with logo and menu items
 * - Scroll-triggered backdrop blur and shadow
 * - Calm Control design system compliance
 */

import Link from 'next/link';

interface LandingNavProps {
  isScrolled?: boolean;
}

export default function LandingNav({ isScrolled = false }: LandingNavProps) {
  return (
    <nav
      className={`sticky top-0 z-50 px-6 py-4 transition-all duration-300 ${
        isScrolled ? 'backdrop-blur-md shadow-md bg-white/80' : ''
      }`}
      aria-label="메인 네비게이션"
    >
      {/* Skip Navigation Link for keyboard users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-accent focus:text-white focus:rounded-md focus:outline-none"
      >
        본문으로 건너뛰기
      </a>
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        {/* Logo */}
        <div className="flex items-center">
          <Link href="/" className="flex items-center space-x-2">
            <img
              src="/logo.svg"
              alt="Legal Evidence Hub"
              className="w-8 h-8"
              onError={(e) => {
                // Fallback to text logo if image fails
                e.currentTarget.style.display = 'none';
              }}
            />
            <span className="text-2xl font-bold text-secondary">LEH</span>
          </Link>
        </div>

        {/* Navigation Menu */}
        <div className="flex items-center space-x-8">
          <Link
            href="#features"
            className="text-sm font-medium text-neutral-700 hover:text-secondary transition-colors"
          >
            기능
          </Link>
          <Link
            href="#pricing"
            className="text-sm font-medium text-neutral-700 hover:text-secondary transition-colors"
          >
            가격
          </Link>
          <Link
            href="#testimonials"
            className="text-sm font-medium text-neutral-700 hover:text-secondary transition-colors"
          >
            고객사례
          </Link>
          <Link
            href="/login"
            className="text-sm font-medium text-neutral-700 hover:text-secondary transition-colors"
          >
            로그인
          </Link>
          <Link
            href="/signup"
            className="btn-primary text-sm px-4 py-2 focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:outline-none"
            aria-label="무료체험 시작하기"
          >
            무료체험
          </Link>
        </div>
      </div>
    </nav>
  );
}
