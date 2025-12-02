import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AdminRolesPage from '@/app/admin/roles/page';

const mockGetRoles = jest.fn();
const mockUpdateRolePermissions = jest.fn();

jest.mock('@/lib/api/admin', () => ({
  getRoles: (...args: unknown[]) => mockGetRoles(...args),
  updateRolePermissions: (...args: unknown[]) => mockUpdateRolePermissions(...args),
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
    return '/admin/roles';
  },
  useSearchParams() {
    return new URLSearchParams();
  },
}));

const ROLE_FIXTURES = [
  { role: 'admin', cases: 'full', evidence: 'full', admin: true, billing: true },
  { role: 'lawyer', cases: 'own', evidence: 'own', admin: false, billing: false },
  { role: 'staff', cases: 'none', evidence: 'none', admin: false, billing: false },
];

describe('plan 3.15: 권한 설정 페이지 (/admin/roles)', () => {
  beforeEach(() => {
    mockGetRoles.mockResolvedValue({
      data: { roles: ROLE_FIXTURES },
      error: null,
      status: 200,
    });

    mockUpdateRolePermissions.mockResolvedValue({
      data: ROLE_FIXTURES[1],
      error: null,
      status: 200,
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('역할별(Admin, Attorney, Staff) 권한 매트릭스 테이블을 렌더링한다.', async () => {
    render(<AdminRolesPage />);

    expect(screen.getByRole('heading', { name: /권한 설정/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /사건 보기/i })).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: /사건 편집/i })).toBeInTheDocument();

    // Wait for async role fetch to populate rows
    expect(
      await screen.findByRole('checkbox', { name: /Admin 사건 보기/i })
    ).toBeInTheDocument();
    expect(
      await screen.findByRole('checkbox', { name: /Attorney 사건 보기/i })
    ).toBeInTheDocument();
    expect(
      await screen.findByRole('checkbox', { name: /Staff 사건 보기/i })
    ).toBeInTheDocument();
  });

  it('권한 토글 변경 시 상태가 업데이트되고, 저장 알림을 표시한다.', async () => {
    const user = userEvent.setup();
    render(<AdminRolesPage />);

    await waitFor(() => expect(mockGetRoles).toHaveBeenCalled());

    const billingToggle = await screen.findByRole('checkbox', {
      name: /Attorney Billing 관리/i,
    });

    expect(billingToggle).not.toBeChecked();

    await user.click(billingToggle);

    await waitFor(() => {
      expect(billingToggle).toBeChecked();
      expect(mockUpdateRolePermissions).toHaveBeenCalledWith('lawyer', {
        cases: 'own',
        evidence: 'own',
        admin: false,
        billing: true,
      });
    });

    expect(await screen.findByText(/권한 설정이 저장되었습니다\./i)).toBeInTheDocument();
  });
});
