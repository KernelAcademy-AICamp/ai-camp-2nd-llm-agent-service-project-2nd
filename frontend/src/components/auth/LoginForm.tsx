'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api/auth';

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
            <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                    이메일
                </label>
                <input
                    id="email"
                    type="email"
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-accent focus:border-accent sm:text-sm"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                />
            </div>

            <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                    비밀번호
                </label>
                <input
                    id="password"
                    type="password"
                    required
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-accent focus:border-accent sm:text-sm"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                />
            </div>

            {error && (
                <div className="text-sm text-semantic-error text-center">
                    {error}
                </div>
            )}

            <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-accent hover:bg-accent-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent disabled:opacity-50"
            >
                {loading ? '로그인 중...' : '로그인'}
            </button>
        </form>
    );
}
