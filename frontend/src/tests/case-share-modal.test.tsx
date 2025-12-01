import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import CaseShareModal from '@/components/cases/CaseShareModal';

describe('plan 3.15: 케이스 공유 모달', () => {
  it('팀원 검색 및 선택, 읽기/쓰기 권한 설정과 공유 피드백을 제공한다.', async () => {
    const user = userEvent.setup();

    render(
      <CaseShareModal
        isOpen={true}
        onClose={() => {}}
        caseTitle="김철수 이혼 소송"
      />,
    );

    expect(
      screen.getByRole('heading', { name: /케이스 공유/i }),
    ).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText(/팀원 검색/i);
    expect(searchInput).toBeInTheDocument();

    expect(screen.getAllByText(/홍길동/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/이영희/i).length).toBeGreaterThan(0);

    // 검색어 입력 시 필터링이 동작하는지(다른 팀원이 사라지는지)만 확인한다.
    await user.type(searchInput, '홍길동');
    expect(screen.queryByText(/이영희/i)).not.toBeInTheDocument();

    const memberCheckbox = screen.getByRole('checkbox', {
      name: /홍길동 선택/i,
    });
    expect(memberCheckbox).not.toBeChecked();

    await user.click(memberCheckbox);
    expect(memberCheckbox).toBeChecked();

    const permissionSelect = screen.getByLabelText(/홍길동 권한/i);
    expect(permissionSelect).toBeInTheDocument();

    await user.selectOptions(permissionSelect, 'read_write');

    const shareButton = screen.getByRole('button', { name: /공유하기/i });
    await user.click(shareButton);

    expect(
      await screen.findByText(/케이스가 선택한 팀원과 공유되었습니다\./i),
    ).toBeInTheDocument();
  });
});
