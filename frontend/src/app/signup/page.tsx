/**
 * Signup Page
 * Plan 3.19.2 - Routing Structure
 *
 * Features:
 * - Signup form for new users
 * - 14-day free trial emphasis
 * - Real API integration with backend
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { signup } from '@/lib/api/auth';

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [lawFirm, setLawFirm] = useState('');
  const [password, setPassword] = useState('');
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Client-side validation
    if (password.length < 8) {
      setError('비밀번호는 8자 이상이어야 합니다.');
      return;
    }

    if (!acceptTerms) {
      setError('이용약관에 동의해주세요.');
      return;
    }

    setLoading(true);

    try {
      // Real API call to backend
      const response = await signup({
        name,
        email,
        password,
        law_firm: lawFirm || undefined,
        accept_terms: acceptTerms,
      });

      if (response.error || !response.data) {
        setError(response.error || '회원가입 중 오류가 발생했습니다.');
        return;
      }

      // Authentication token is now handled via HTTP-only cookie (set by backend)
      // We only cache user display info locally, NOT the auth token

      // Cache user info for display purposes only (not for auth)
      if (response.data.user) {
        const userData = {
          name: response.data.user.name,
          email: response.data.user.email,
          role: response.data.user.role,
        };
        // Set user_data cookie for middleware
        document.cookie = `user_data=${encodeURIComponent(JSON.stringify(userData))}; path=/; max-age=${7 * 24 * 60 * 60}`;
        // Cache for display purposes
        localStorage.setItem('userCache', JSON.stringify(userData));
      }

      // Redirect to cases page
      router.push('/cases');
    } catch (err) {
      console.error('Signup error:', err);
      setError('회원가입 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-neutral-50">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-deep-trust-blue mb-2">
            무료로 시작하기
          </h1>
          <p className="text-neutral-600">14일 무료 체험, 신용카드 필요 없음</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-neutral-700 mb-2">
              이름
            </label>
            <input
              id="name"
              name="name"
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="홍길동"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-neutral-700 mb-2">
              이메일
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="your@email.com"
            />
          </div>

          <div>
            <label htmlFor="law-firm" className="block text-sm font-medium text-neutral-700 mb-2">
              소속 (선택)
            </label>
            <input
              id="law-firm"
              name="law-firm"
              type="text"
              value={lawFirm}
              onChange={(e) => setLawFirm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="법무법인 이름"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-neutral-700 mb-2">
              비밀번호
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="8자 이상"
            />
          </div>

          <div className="flex items-center">
            <input
              id="accept-terms"
              name="accept-terms"
              type="checkbox"
              checked={acceptTerms}
              onChange={(e) => setAcceptTerms(e.target.checked)}
              className="h-4 w-4 text-accent focus:ring-accent border-gray-300 rounded"
            />
            <label htmlFor="accept-terms" className="ml-2 block text-sm text-neutral-700">
              <a href="/terms" className="text-accent hover:underline">이용약관</a> 및{' '}
              <a href="/privacy" className="text-accent hover:underline">개인정보처리방침</a>에 동의합니다
            </label>
          </div>

          {error && (
            <div className="text-sm text-red-600 text-center">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full py-3 disabled:opacity-50"
          >
            {loading ? '처리 중...' : '무료 체험 시작'}
          </button>
        </form>

        <p className="text-sm text-gray-500 text-center mt-6">
          이미 계정이 있으신가요?{' '}
          <a href="/login" className="text-accent hover:underline">
            로그인
          </a>
        </p>
      </div>
    </div>
  );
}
