'use client';

import { useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button, Input } from '@/components/primitives';
import { useAuth } from '@/hooks/useAuth';

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(email, password);

      if (!result.success) {
        setError(result.error || '아이디 또는 비밀번호를 확인해 주세요.');
        return;
      }

      // Redirect to returnUrl if provided, otherwise use default dashboard
      const returnUrl = searchParams.get('returnUrl');
      const redirectTo = returnUrl || result.redirectPath || '/';
      router.push(redirectTo);
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
            className="text-sm text-secondary hover:underline"
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
