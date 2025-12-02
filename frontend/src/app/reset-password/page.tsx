/**
 * Reset Password Page
 * Set new password using token from email
 */

'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { resetPassword } from '@/lib/api/auth';
import { Button, Input } from '@/components/primitives';

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams?.get('token') || null;

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      setError('유효하지 않은 비밀번호 재설정 링크입니다.');
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate password match
    if (password !== confirmPassword) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }

    // Validate password length
    if (password.length < 8) {
      setError('비밀번호는 8자 이상이어야 합니다.');
      return;
    }

    if (!token) {
      setError('유효하지 않은 비밀번호 재설정 링크입니다.');
      return;
    }

    setLoading(true);

    try {
      const response = await resetPassword(token, password);

      if (response.error) {
        setError(response.error);
        return;
      }

      setSuccess(true);

      // Redirect to login after 3 seconds
      setTimeout(() => {
        router.push('/login');
      }, 3000);
    } catch (err) {
      console.error('Reset password error:', err);
      setError('비밀번호 변경 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <div className="w-full max-w-md text-center">
          <div className="bg-white p-8 rounded-lg shadow-sm">
            <div className="mb-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-neutral-800 mb-2">
                비밀번호가 변경되었습니다
              </h2>
              <p className="text-neutral-600 text-sm">
                새 비밀번호로 로그인해주세요.
                <br />
                잠시 후 로그인 페이지로 이동합니다...
              </p>
            </div>
            <Link
              href="/login"
              className="text-deep-trust-blue hover:underline text-sm"
            >
              로그인 페이지로 이동
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <div className="w-full max-w-md text-center">
          <div className="bg-white p-8 rounded-lg shadow-sm">
            <div className="mb-6">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-neutral-800 mb-2">
                유효하지 않은 링크
              </h2>
              <p className="text-neutral-600 text-sm">
                비밀번호 재설정 링크가 유효하지 않거나 만료되었습니다.
                <br />
                다시 비밀번호 찾기를 시도해주세요.
              </p>
            </div>
            <Link
              href="/forgot-password"
              className="text-deep-trust-blue hover:underline text-sm"
            >
              비밀번호 찾기로 이동
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-deep-trust-blue mb-2">
            새 비밀번호 설정
          </h1>
          <p className="text-neutral-600 text-sm">
            새로운 비밀번호를 입력해주세요.
          </p>
        </div>

        <div className="bg-white p-8 rounded-lg shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-6">
            <Input
              id="password"
              type="password"
              label="새 비밀번호"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="8자 이상 입력"
            />

            <Input
              id="confirmPassword"
              type="password"
              label="비밀번호 확인"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="비밀번호 재입력"
            />

            {error && (
              <div className="text-sm text-error text-center" role="alert">
                {error}
              </div>
            )}

            <Button
              type="submit"
              variant="primary"
              isLoading={loading}
              loadingText="변경 중..."
              fullWidth
            >
              비밀번호 변경
            </Button>
          </form>

          <div className="mt-6 text-center">
            <Link
              href="/login"
              className="text-deep-trust-blue hover:underline text-sm"
            >
              로그인 페이지로 돌아가기
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center bg-neutral-50">
          <div className="text-neutral-600">로딩 중...</div>
        </div>
      }
    >
      <ResetPasswordForm />
    </Suspense>
  );
}
