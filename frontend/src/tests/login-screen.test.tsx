import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import LoginForm from '@/components/auth/LoginForm';

// Mock useRouter - App Router version
jest.mock('next/navigation', () => ({
    useRouter: jest.fn(() => ({
        push: jest.fn(),
        replace: jest.fn(),
        prefetch: jest.fn(),
    })),
    usePathname: jest.fn(() => '/'),
}));

describe('Login Screen Requirements', () => {
    test('로그인 화면에는 이메일 입력, 비밀번호 입력, 로그인 버튼만 존재해야 한다', () => {
        render(<LoginForm />);

        // 이메일 입력 필드 존재
        expect(screen.getByLabelText(/이메일/i)).toBeInTheDocument();

        // 비밀번호 입력 필드 존재
        expect(screen.getByLabelText(/비밀번호/i)).toBeInTheDocument();

        // 로그인 버튼 존재
        expect(screen.getByRole('button', { name: /로그인/i })).toBeInTheDocument();

        // 광고/마케팅 배너가 없어야 함 - 특정 키워드로 확인
        expect(screen.queryByText(/광고/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/마케팅/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/프로모션/i)).not.toBeInTheDocument();
    });

    test('잘못된 자격증명일 경우 일반적인 에러 메시지만 보여야 한다', async () => {
        render(<LoginForm />);

        const emailInput = screen.getByLabelText(/이메일/i);
        const passwordInput = screen.getByLabelText(/비밀번호/i);
        const submitButton = screen.getByRole('button', { name: /로그인/i });

        // 잘못된 자격증명 입력
        fireEvent.change(emailInput, { target: { value: 'wrong@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
        fireEvent.click(submitButton);

        // 일반적인 에러 메시지 확인
        await waitFor(() => {
            expect(screen.getByText(/아이디 또는 비밀번호를 확인해 주세요/i)).toBeInTheDocument();
        });

        // 어떤 정보가 틀렸는지 노출하지 않아야 함
        expect(screen.queryByText(/이메일이 틀렸습니다/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/비밀번호가 틀렸습니다/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/존재하지 않는 사용자/i)).not.toBeInTheDocument();
    });
});
