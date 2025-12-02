import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdminUsersPage from '@/app/admin/users/page';

// Mock API responses
const MOCK_USERS = [
  { id: 'user-1', name: '홍길동', email: 'hong@example.com', role: 'admin' as const, status: 'active' as const },
  { id: 'user-2', name: '이영희', email: 'lee@example.com', role: 'lawyer' as const, status: 'active' as const },
  { id: 'user-3', name: '김철수', email: 'kim@example.com', role: 'staff' as const, status: 'invited' as const },
];

jest.mock('@/lib/api/admin', () => ({
  getAdminUsers: jest.fn(() =>
    Promise.resolve({
      data: { users: MOCK_USERS, total: 3 },
      error: null,
    })
  ),
  deleteUser: jest.fn(() =>
    Promise.resolve({
      data: { message: '사용자가 삭제되었습니다.', user_id: 'user-1' },
      error: null,
    })
  ),
}));

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
  it('관리자 사용자 목록 테이블과 검색 입력, 사용자 초대 버튼을 렌더링한다.', async () => {
    render(<AdminUsersPage />);

    expect(
      screen.getByRole('heading', { name: /사용자 및 역할 관리/i }),
    ).toBeInTheDocument();

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/불러오는 중/)).not.toBeInTheDocument();
    });

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

    // Wait for loading to complete and data to render
    await waitFor(() => {
      expect(screen.getByRole('row', { name: /홍길동/i })).toBeInTheDocument();
    });

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

    // Wait for delete to complete
    await waitFor(() => {
      expect(
        screen.queryByRole('row', { name: /홍길동/i }),
      ).not.toBeInTheDocument();
    });

    const inviteButton = screen.getByRole('button', { name: /사용자 초대/i });
    await user.click(inviteButton);
    expect(
      await screen.findByText(/초대 기능은 준비 중입니다\./i),
    ).toBeInTheDocument();
  });
});

