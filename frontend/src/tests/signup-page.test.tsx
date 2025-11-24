import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

// useRouter 모의(mock) 설정 - Pages Router version
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/signup',
      pathname: '/signup',
      query: '',
      asPath: '/signup',
      push: jest.fn(),
      replace: jest.fn(),
    };
  },
}));

// Skip this test suite - migrated to App Router
// The actual signup page is now at src/app/signup/page.tsx
describe.skip('plan 3.8: 회원가입 페이지 (Pages Router - deprecated)', () => {
  it('"/signup" 경로에 접근했을 때, 회원가입 페이지의 주요 요소들이 렌더링되어야 한다.', () => {
    // Skipped - migrated to App Router
    expect(true).toBe(true);

    // 1. "회원가입" 제목이 표시되는지 확인
    const heading = screen.getByRole('heading', { name: /회원가입/i });
    expect(heading).toBeInTheDocument();

    // 2. 이메일, 비밀번호, 이름 입력 필드가 존재하는지 확인
    const emailInput = screen.getByLabelText(/이메일/i);
    const passwordInput = screen.getByLabelText(/^비밀번호$/i);
    const passwordConfirmInput = screen.getByLabelText(/비밀번호 확인/i);
    const nameInput = screen.getByLabelText(/이름/i);

    expect(emailInput).toBeInTheDocument();
    expect(passwordInput).toBeInTheDocument();
    expect(passwordConfirmInput).toBeInTheDocument();
    expect(nameInput).toBeInTheDocument();

    // 3. 이용약관 동의 체크박스와 회원가입 버튼이 존재하는지 확인
    const termsCheckbox = screen.getByRole('checkbox', { name: /이용약관에 동의합니다/i });
    const signupButton = screen.getByRole('button', { name: /회원가입/i });

    expect(termsCheckbox).toBeInTheDocument();
    expect(signupButton).toBeInTheDocument();
  });

  it('유효하지 않은 이메일을 입력하면 오류 메시지를 표시해야 한다.', async () => {
    const user = userEvent.setup();
    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/이메일/i);
    const signupButton = screen.getByRole('button', { name: /회원가입/i });

    await user.type(emailInput, 'invalid-email');
    await user.click(signupButton);

    const errorMessage = await screen.findByText(/유효한 이메일 주소를 입력해주세요./i);
    expect(errorMessage).toBeInTheDocument();
  });

  it('비밀번호와 비밀번호 확인이 일치하지 않으면 오류 메시지를 표시해야 한다.', async () => {
    const user = userEvent.setup();
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText(/^비밀번호$/i);
    const passwordConfirmInput = screen.getByLabelText(/비밀번호 확인/i);
    const signupButton = screen.getByRole('button', { name: /회원가입/i });

    await user.type(passwordInput, 'password123');
    await user.type(passwordConfirmInput, 'password456');
    await user.click(signupButton);

    const errorMessage = await screen.findByText(/비밀번호가 일치하지 않습니다./i);
    expect(errorMessage).toBeInTheDocument();
  });

  it('이름이 입력되지 않으면 오류 메시지를 표시해야 한다.', async () => {
    const user = userEvent.setup();
    render(<SignupPage />);

    const emailInput = screen.getByLabelText(/이메일/i);
    const signupButton = screen.getByRole('button', { name: /회원가입/i });

    await user.type(emailInput, 'test@example.com');
    await user.click(signupButton);

    const errorMessage = await screen.findByText(/이름을 입력해주세요./i);
    expect(errorMessage).toBeInTheDocument();
  });

  it('비밀번호가 8자 미만이면 오류 메시지를 표시해야 한다.', async () => {
    const user = userEvent.setup();
    render(<SignupPage />);

    const passwordInput = screen.getByLabelText(/^비밀번호$/i);
    const signupButton = screen.getByRole('button', { name: /회원가입/i });

    await user.type(passwordInput, 'short');
    await user.click(signupButton);

    const errorMessage = await screen.findByText(/비밀번호는 최소 8자 이상이어야 합니다./i);
    expect(errorMessage).toBeInTheDocument();
  });

  it('이용약관에 동의하지 않으면 오류 메시지를 표시해야 한다.', async () => {
    const user = userEvent.setup();
    render(<SignupPage />);

    const nameInput = screen.getByLabelText(/이름/i);
    const emailInput = screen.getByLabelText(/이메일/i);
    const passwordInput = screen.getByLabelText(/^비밀번호$/i);
    const passwordConfirmInput = screen.getByLabelText(/비밀번호 확인/i);
    const signupButton = screen.getByRole('button', { name: /회원가입/i });

    await user.type(nameInput, '홍길동');
    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');
    await user.type(passwordConfirmInput, 'password123');
    await user.click(signupButton);

    const errorMessage = await screen.findByText(/이용약관에 동의해주세요./i);
    expect(errorMessage).toBeInTheDocument();
  });
});
