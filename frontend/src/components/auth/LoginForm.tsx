'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { login } from '@/lib/api/auth';
import { Button, Input } from '@/components/primitives';
import { getDashboardPath, UserRole } from '@/types/user';

export default function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // Real API call to backend
      const response = await login(email, password);

      if (response.error || !response.data) {
        setError(response.error || '아이디 또는 비밀번호를 확인해 주세요.');
        return;
      }

      // Store auth token in localStorage and cookie
      // NOTE: See Issue #63 for HTTP-only cookie migration plan
      localStorage.setItem('authToken', response.data.access_token);

      // Set access_token cookie for middleware authentication check
      document.cookie = `access_token=${response.data.access_token}; path=/; max-age=${7 * 24 * 60 * 60}`;

      // Store user info for display purposes
      if (response.data.user) {
        // Normalize role to lowercase for frontend compatibility
        const normalizedRole = response.data.user.role.toLowerCase();
        const normalizedUser = { ...response.data.user, role: normalizedRole };

        localStorage.setItem('user', JSON.stringify(normalizedUser));

        // Set user_data cookie for middleware and portal layouts
        const userData = {
          name: response.data.user.name,
          email: response.data.user.email,
          role: normalizedRole,
        };
        document.cookie = `user_data=${encodeURIComponent(JSON.stringify(userData))}; path=/; max-age=${7 * 24 * 60 * 60}`;
      }

      // Redirect based on user role (normalized to lowercase)
      const userRole = (response.data.user?.role?.toLowerCase() || 'lawyer') as UserRole;
      const dashboardPath = getDashboardPath(userRole);
      router.push(dashboardPath);
    } catch {
      setError('로그인 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 w-full max-w-sm">
      <Input
        id="email"
        type="email"
        label="이메일"
        required
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        error={error && email === '' ? '이메일을 입력해주세요' : undefined}
      />

      <div>
        <Input
          id="password"
          type="password"
          label="비밀번호"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={error && password === '' ? '비밀번호를 입력해주세요' : undefined}
        />
        <div className="mt-1 text-right">
          <Link
            href="/forgot-password"
            className="text-sm text-deep-trust-blue hover:underline"
          >
            비밀번호를 잊으셨나요?
          </Link>
        </div>
      </div>

      {error && (
        <div className="text-sm text-error text-center" role="alert">
          {error}
        </div>
      )}

      <Button
        type="submit"
        variant="primary"
        isLoading={loading}
        loadingText="로그인 중..."
        fullWidth
      >
        로그인
      </Button>
    </form>
  );
}
