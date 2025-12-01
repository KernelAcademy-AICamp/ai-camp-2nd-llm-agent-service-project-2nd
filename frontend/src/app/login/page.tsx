/**
 * Login Page
 * Plan 3.19.2 - Routing Structure Change
 *
 * Features:
 * - Login form (moved from root `/`)
 * - Redirect to `/cases` if already authenticated
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import LoginForm from '@/components/auth/LoginForm';

export default function LoginPage() {
  const router = useRouter();

  useEffect(() => {
    // Navigation Guard: Check if already authenticated
    const token = localStorage.getItem('authToken');
    if (token) {
      router.push('/cases');
    }
  }, [router]);

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
