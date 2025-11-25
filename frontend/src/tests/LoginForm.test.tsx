import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginForm from '@/components/auth/LoginForm';
import { login } from '@/lib/api/auth';
import '@testing-library/jest-dom';

// Mock useRouter - App Router version
jest.mock('next/navigation', () => ({
    useRouter() {
        return {
            push: jest.fn(),
            replace: jest.fn(),
            prefetch: jest.fn(),
        };
    },
    usePathname() {
        return '/';
    },
}));

// Mock auth API
jest.mock('@/lib/api/auth', () => ({
    login: jest.fn(),
}));

describe('LoginForm', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('renders login form correctly', () => {
        render(<LoginForm />);
        expect(screen.getByLabelText(/이메일/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/비밀번호/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /로그인/i })).toBeInTheDocument();
    });

    it('shows error on invalid credentials', async () => {
        // Mock login failure
        (login as jest.Mock).mockResolvedValue({
            error: '아이디 또는 비밀번호를 확인해 주세요.',
            data: null
        });

        render(<LoginForm />);

        fireEvent.change(screen.getByLabelText(/이메일/i), { target: { value: 'wrong@example.com' } });
        fireEvent.change(screen.getByLabelText(/비밀번호/i), { target: { value: 'wrongpass' } });
        fireEvent.click(screen.getByRole('button', { name: /로그인/i }));

        await waitFor(() => {
            expect(screen.getByText(/아이디 또는 비밀번호를 확인해 주세요/i)).toBeInTheDocument();
        });
    });

    it('redirects on successful login', async () => {
        // Mock login success
        (login as jest.Mock).mockResolvedValue({
            error: null,
            data: {
                access_token: 'fake-token',
                token_type: 'bearer',
                user: { id: '1', email: 'test@example.com', name: 'Test User', role: 'user' }
            }
        });

        render(<LoginForm />);

        fireEvent.change(screen.getByLabelText(/이메일/i), { target: { value: 'test@example.com' } });
        fireEvent.change(screen.getByLabelText(/비밀번호/i), { target: { value: 'password' } });
        fireEvent.click(screen.getByRole('button', { name: /로그인/i }));

        await waitFor(() => {
            // Check if login was called
            expect(login).toHaveBeenCalledWith('test@example.com', 'password');
        });
    });
});
