/**
 * LandingNav Component
 * Plan 3.19.1 - Navigation Bar (고정 헤더)
 *
 * Features:
 * - Sticky navigation with logo and menu items
 * - Scroll-triggered backdrop blur and shadow
 * - Calm Control design system compliance
 */

'use client';

import { useCallback, useState } from 'react';
import Link from 'next/link';
import { Logo } from '@/components/shared/Logo';
import { BRAND } from '@/config/brand';

interface LandingNavProps {
  isScrolled?: boolean;
  isAuthenticated?: boolean;
  authLoading?: boolean;
  onLogout?: () => Promise<void> | void;
}

export default function LandingNav({
  isScrolled = false,
  isAuthenticated = false,
  authLoading = false,
  onLogout,
}: LandingNavProps) {
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const scrollToSection = (e: React.MouseEvent<HTMLAnchorElement>, sectionId: string) => {
    e.preventDefault();
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleLogout = useCallback(async () => {
    if (!onLogout || isLoggingOut) return;
    setIsLoggingOut(true);
    try {
      await onLogout();
    } catch (error) {
      console.error('로그아웃 실패', error);
    } finally {
      setIsLoggingOut(false);
    }
  }, [isLoggingOut, onLogout]);

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
            <Logo size="sm" />
            <span className="text-2xl font-bold text-secondary">{BRAND.name}</span>
          </Link>
        </div>

        {/* Navigation Menu */}
        <div className="flex items-center space-x-8">
          <a
            href="#features"
            onClick={(e) => scrollToSection(e, 'features')}
            className="text-sm font-medium text-neutral-700 hover:text-secondary transition-colors cursor-pointer"
          >
            기능
          </a>
          <a
            href="#pricing"
            onClick={(e) => scrollToSection(e, 'pricing')}
            className="text-sm font-medium text-neutral-700 hover:text-secondary transition-colors cursor-pointer"
          >
            가격
          </a>
          <a
            href="#testimonials"
            onClick={(e) => scrollToSection(e, 'testimonials')}
            className="text-sm font-medium text-neutral-700 hover:text-secondary transition-colors cursor-pointer"
          >
            고객사례
          </a>
          {isAuthenticated ? (
            <>
              <Link
                href="/lawyer/dashboard"
                className="btn-primary text-sm px-4 py-2 focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:outline-none"
                aria-label="대시보드로 이동"
              >
                대시보드
              </Link>
              <button
                type="button"
                onClick={handleLogout}
                disabled={isLoggingOut || authLoading}
                className="text-sm px-4 py-2 font-medium text-neutral-700 hover:text-secondary transition-colors focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:outline-none disabled:opacity-60"
                aria-label="로그아웃"
              >
                {isLoggingOut ? '로그아웃 중...' : '로그아웃'}
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="text-sm px-4 py-2 font-medium text-neutral-700 hover:text-secondary transition-colors focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:outline-none"
                aria-label="로그인 페이지로 이동"
              >
                로그인
              </Link>
              <Link
                href="/signup"
                className="btn-primary text-sm px-4 py-2 focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:outline-none"
                aria-label="회원가입 페이지로 이동"
              >
                회원가입
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
