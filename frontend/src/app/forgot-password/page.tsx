/**
 * Forgot Password Page
 * Request password reset email
 */

'use client';

import { useState } from 'react';
import Link from 'next/link';
import { forgotPassword } from '@/lib/api/auth';
import { Button, Input } from '@/components/primitives';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await forgotPassword(email);

      if (response.error) {
        setError(response.error);
        return;
      }

      setSuccess(true);
    } catch (err) {
      console.error('Forgot password error:', err);
      setError('요청 처리 중 오류가 발생했습니다.');
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
                    d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-bold text-neutral-800 mb-2">
                이메일을 확인해주세요
              </h2>
              <p className="text-neutral-600 text-sm">
                <strong>{email}</strong>로 비밀번호 재설정 링크를 발송했습니다.
                <br />
                이메일이 도착하지 않으면 스팸 폴더를 확인해주세요.
              </p>
            </div>
            <Link
              href="/login"
              className="text-deep-trust-blue hover:underline text-sm"
            >
              로그인 페이지로 돌아가기
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
            비밀번호 찾기
          </h1>
          <p className="text-neutral-600 text-sm">
            가입한 이메일 주소를 입력하시면
            <br />
            비밀번호 재설정 링크를 보내드립니다.
          </p>
        </div>

        <div className="bg-white p-8 rounded-lg shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-6">
            <Input
              id="email"
              type="email"
              label="이메일"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="example@email.com"
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
              loadingText="전송 중..."
              fullWidth
            >
              재설정 링크 받기
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
