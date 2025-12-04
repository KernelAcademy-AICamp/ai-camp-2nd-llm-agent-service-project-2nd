/**
 * Login Page
 * Plan 3.19.2 - Routing Structure Change
 *
 * Features:
 * - Login form (moved from root `/`)
 * - Redirect to dashboard if already authenticated
 *
 * Security:
 * - Uses HTTP-only cookie for authentication
 * - Auth check via useAuth hook (calls /auth/me)
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import LoginForm from '@/components/auth/LoginForm';
import { useAuth } from '@/hooks/useAuth';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    // Navigation Guard: Redirect if already authenticated
    if (!isLoading && isAuthenticated) {
      router.push('/cases');
    }
  }, [isAuthenticated, isLoading, router]);

  // Show loading while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <div className="text-neutral-600">로딩 중...</div>
      </div>
    );
  }

  // If authenticated, don't render login form (redirect will happen)
  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-deep-trust-blue mb-2">
            Legal Evidence Hub
          </h1>
          <p className="text-neutral-600">로그인하여 시작하세요</p>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
