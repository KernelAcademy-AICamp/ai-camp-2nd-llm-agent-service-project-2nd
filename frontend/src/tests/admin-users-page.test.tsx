import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdminUsersPage from '@/app/admin/users/page';

jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      back: jest.fn(),
    };
  },
  usePathname() {
    return '/admin/users';
  },
  useSearchParams() {
    return new URLSearchParams();
  },
}));

describe('plan 3.15: 사용자 목록 페이지 (/admin/users)', () => {
  it('관리자 사용자 목록 테이블과 검색 입력, 사용자 초대 버튼을 렌더링한다.', () => {
    render(<AdminUsersPage />);

    expect(
      screen.getByRole('heading', { name: /사용자 및 역할 관리/i }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole('columnheader', { name: /이름/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('columnheader', { name: /이메일/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('columnheader', { name: /역할/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('columnheader', { name: /상태/i }),
    ).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText(/이름 또는 이메일으로 검색/i);
    expect(searchInput).toBeInTheDocument();

    const inviteButton = screen.getByRole('button', { name: /사용자 초대/i });
    expect(inviteButton).toBeInTheDocument();
  });

  it('검색어로 사용자 테이블을 필터링하고, 사용자 삭제 및 초대 피드백을 제공한다.', async () => {
    const user = userEvent.setup();
    render(<AdminUsersPage />);

    const hongRowBefore = screen.getByRole('row', { name: /홍길동/i });
    const leeRowBefore = screen.getByRole('row', { name: /이영희/i });
    expect(hongRowBefore).toBeInTheDocument();
    expect(leeRowBefore).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText(/이름 또는 이메일으로 검색/i);
    await user.type(searchInput, '홍길동');

    expect(screen.getByRole('row', { name: /홍길동/i })).toBeInTheDocument();
    expect(
      screen.queryByRole('row', { name: /이영희/i }),
    ).not.toBeInTheDocument();

    const deleteButton = screen.getByRole('button', { name: /홍길동 삭제/i });
    await user.click(deleteButton);
    expect(
      screen.queryByRole('row', { name: /홍길동/i }),
    ).not.toBeInTheDocument();

    const inviteButton = screen.getByRole('button', { name: /사용자 초대/i });
    await user.click(inviteButton);
    expect(
      await screen.findByText(/초대 링크가 전송되었습니다\./i),
    ).toBeInTheDocument();
  });
});

