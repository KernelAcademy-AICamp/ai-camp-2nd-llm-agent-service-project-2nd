import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdminRolesPage from '@/pages/admin/roles';

jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/admin/roles',
      pathname: '/admin/roles',
      query: {},
      asPath: '/admin/roles',
      push: jest.fn(),
    };
  },
}));

describe('plan 3.15: 권한 설정 페이지 (/admin/roles)', () => {
  it('역할별(Admin, Attorney, Staff) 권한 매트릭스 테이블을 렌더링한다.', () => {
    render(<AdminRolesPage />);

    expect(
      screen.getByRole('heading', { name: /권한 설정/i }),
    ).toBeInTheDocument();

    expect(
      screen.getByRole('columnheader', { name: /사건 보기/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('columnheader', { name: /사건 편집/i }),
    ).toBeInTheDocument();

    expect(screen.getAllByText(/Admin/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Attorney/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Staff/i).length).toBeGreaterThan(0);
  });

  it('권한 토글 변경 시 상태가 업데이트되고, 저장 알림을 표시한다.', async () => {
    const user = userEvent.setup();
    render(<AdminRolesPage />);

    const billingToggle = screen.getByRole('checkbox', {
      name: /Attorney Billing 관리/i,
    });

    expect(billingToggle).not.toBeChecked();

    await user.click(billingToggle);

    expect(billingToggle).toBeChecked();
    expect(
      await screen.findByText(/권한 설정이 저장되었습니다\./i),
    ).toBeInTheDocument();
  });
});
