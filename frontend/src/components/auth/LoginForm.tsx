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

      // Authentication token is now handled via HTTP-only cookie (set by backend)
      // We only store display info locally, NOT the auth token

      // Store user info for display purposes only (not for auth)
      if (response.data.user) {
        // Set user_data cookie for middleware and portal layouts
        const userData = {
          name: response.data.user.name,
          email: response.data.user.email,
          role: response.data.user.role,
        };
        document.cookie = `user_data=${encodeURIComponent(JSON.stringify(userData))}; path=/; max-age=${7 * 24 * 60 * 60}`;

        // Cache user info for display (useAuth will verify via API)
        localStorage.setItem('userCache', JSON.stringify(userData));
      }

      // Redirect based on user role
      const userRole = response.data.user?.role as UserRole || 'lawyer';
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
