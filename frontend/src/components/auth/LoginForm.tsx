'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api/auth';
import { Button, Input } from '@/components/primitives';

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

      // Store auth token in localStorage
      // TODO: Consider HTTP-only cookie for better security
      localStorage.setItem('authToken', response.data.access_token);

      // Store user info for display purposes
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }

      // Redirect to cases page
      router.push('/cases');
    } catch (err) {
      console.error('Login error:', err);
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

      <Input
        id="password"
        type="password"
        label="비밀번호"
        required
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        error={error && password === '' ? '비밀번호를 입력해주세요' : undefined}
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
        loadingText="로그인 중..."
        fullWidth
      >
        로그인
      </Button>
    </form>
  );
}
