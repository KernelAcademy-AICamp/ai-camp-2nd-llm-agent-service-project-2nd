/**
 * Signup Page
 * Plan 3.19.2 - Routing Structure
 *
 * Features:
 * - Signup form for new users
 * - 14-day free trial emphasis
 * - Mock signup for development (TODO: Replace with real API)
 */

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [lawFirm, setLawFirm] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // TODO: Replace with real API call when backend is ready
      // Mock signup for development
      await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay

      // Validate password length
      if (password.length < 8) {
        setError('비밀번호는 8자 이상이어야 합니다.');
        return;
      }

      // Mock: Create user and auto-login
      const mockToken = `mock-jwt-token-${Date.now()}`;
      localStorage.setItem('authToken', mockToken);
      localStorage.setItem('mockUser', JSON.stringify({ name, email, lawFirm }));

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
    <div className="min-h-screen flex items-center justify-center bg-calm-grey">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-deep-trust-blue mb-2">
            무료로 시작하기
          </h1>
          <p className="text-gray-600">14일 무료 체험, 신용카드 필요 없음</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
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
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
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
            <label htmlFor="law-firm" className="block text-sm font-medium text-gray-700 mb-2">
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
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
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
