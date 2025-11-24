/**
 * Signup Page
 * Plan 3.19.2 - Routing Structure
 *
 * Features:
 * - Signup form for new users
 * - 14-day free trial emphasis
 */

'use client';

export default function SignupPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-calm-grey">
      <div className="w-full max-w-md bg-white rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-deep-trust-blue mb-2">
            무료로 시작하기
          </h1>
          <p className="text-gray-600">14일 무료 체험, 신용카드 필요 없음</p>
        </div>

        <form className="space-y-6">
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              이름
            </label>
            <input
              id="name"
              name="name"
              type="text"
              required
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
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="8자 이상"
            />
          </div>

          <button
            type="submit"
            className="btn-primary w-full py-3"
          >
            무료 체험 시작
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
