import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CasesPage from '@/pages/cases';

// next/router 모의 설정
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/cases',
      pathname: '/cases',
      query: '',
      asPath: '/cases',
      replace: jest.fn(),
      push: jest.fn(),
    };
  },
}));

// useAuth 훅 모의 설정
jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    isAuthenticated: true,
    isLoading: false,
    logout: jest.fn(),
  }),
}));

// API 호출 모의 설정
jest.mock('@/lib/api/cases', () => ({
  getCases: jest.fn().mockResolvedValue({
    data: {
      cases: [
        {
          id: '1',
          title: '김철수 이혼 소송',
          client_name: '김철수',
          status: 'active',
          evidence_count: 128,
          draft_status: 'completed',
          created_at: '2024-05-20T09:00:00Z',
          updated_at: '2024-05-20T09:00:00Z',
        },
      ],
      total: 1,
    },
    status: 200,
  }),
}));

describe('plan 3.10: 사건 등록/관리', () => {
  beforeEach(() => {
    // Mock authToken for navigation guard
    localStorage.setItem('authToken', 'mock-test-token');
  });

  afterEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });
  it("대시보드에서 '새 사건 등록' 버튼을 클릭하면 사건 등록 모달이 열려야 한다.", async () => {
    const user = userEvent.setup();
    render(<CasesPage />);

    // 1. '새 사건 등록' 버튼을 찾는다. (API 로딩 후 버튼이 나타남)
    const addCaseButton = await screen.findByRole('button', { name: /새 사건 등록/i });
    expect(addCaseButton).toBeInTheDocument();

    // 2. 버튼을 클릭한다.
    await user.click(addCaseButton);

    // 3. 모달이 열리고 '새로운 사건 정보'라는 제목이 표시되는지 확인한다.
    // findBy는 요소가 나타날 때까지 기다린다.
    const modalTitle = await screen.findByRole('heading', { name: /새로운 사건 정보/i });
    expect(modalTitle).toBeInTheDocument();
  });

  it('사건 등록 모달에는 사건명, 의뢰인 이름, 설명 입력 필드가 포함되어야 한다.', async () => {
    const user = userEvent.setup();
    render(<CasesPage />);

    // 모달 열기 (API 로딩 후 버튼이 나타남)
    const addCaseButton = await screen.findByRole('button', { name: /새 사건 등록/i });
    await user.click(addCaseButton);

    // 모달이 열릴 때까지 대기
    await screen.findByRole('heading', { name: /새로운 사건 정보/i });

    // 필수 입력 필드 확인
    expect(screen.getByLabelText(/사건명/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/의뢰인 이름/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/사건 설명/i)).toBeInTheDocument();
  });

  it('사건 카드에서 진행 상황을 변경할 수 있는 드롭다운이 표시되어야 한다.', async () => {
    const user = userEvent.setup();
    render(<CasesPage />);

    // API 로딩 후 사건 카드가 나타날 때까지 대기
    await screen.findByRole('button', { name: /새 사건 등록/i });

    // 첫 번째 사건 카드에서 상태 변경 버튼 찾기
    const statusButtons = await screen.findAllByRole('button', { name: /상태 변경/i });
    expect(statusButtons.length).toBeGreaterThan(0);

    // 상태 변경 버튼 클릭
    await user.click(statusButtons[0]);

    // 드롭다운 옵션 확인
    expect(await screen.findByRole('option', { name: /진행 중/i })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: /종결/i })).toBeInTheDocument();
  });
});
