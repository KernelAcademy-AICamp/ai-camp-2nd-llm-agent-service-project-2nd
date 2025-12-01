import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ClientCommunicationHub from '@/pages/communications';

jest.mock('next/router', () => ({
    useRouter: () => ({
        query: { caseId: 'case-comm-001', client: '홍길동' },
        push: jest.fn(),
    }),
}));

describe('Plan 3.14 - 의뢰인 소통 허브', () => {
    test('의뢰인 정보 폼: 이름/연락처/이메일/사건 메모 필드와 저장 버튼을 제공하고 필수 입력 전에 저장이 비활성화되어야 한다', async () => {
        const user = userEvent.setup();
        render(<ClientCommunicationHub />);

        const nameInput = screen.getByLabelText(/의뢰인 이름/i);
        const phoneInput = screen.getByLabelText(/연락처/i);
        const emailInput = screen.getByLabelText(/이메일/i);
        const notesInput = screen.getByLabelText(/사건 메모/i);
        const saveButton = screen.getByRole('button', { name: /정보 저장/i });

        expect(saveButton).toBeDisabled();

        await user.type(nameInput, '홍길동');
        await user.type(phoneInput, '010-1234-5678');
        await user.type(emailInput, 'client@example.com');
        await user.type(notesInput, '증거 업로드 안내 필요');

        expect(saveButton).toBeEnabled();

        await user.click(saveButton);

        expect(
            await screen.findByText(/의뢰인 정보가 저장되었습니다\. 고지사항을 확인해 주세요\./i),
        ).toBeInTheDocument();
    });

    test('증거 공유/고지 페이지: 읽기 전용 증거 목록과 법적 고지 텍스트를 보여주고 편집 액션을 노출하지 않는다', async () => {
        const user = userEvent.setup();
        render(<ClientCommunicationHub />);

        const shareTab = screen.getByRole('tab', { name: /증거 공유/i });
        await user.click(shareTab);

        expect(await screen.findByRole('heading', { name: /증거 목록 공유/i })).toBeInTheDocument();

        const evidenceRows = screen.getAllByRole('row');
        expect(evidenceRows.length).toBeGreaterThan(1);

        expect(
            screen.getByText(/제공된 증거는 열람용이며 수정할 수 없습니다\./i),
        ).toBeInTheDocument();

        expect(screen.queryByRole('button', { name: /삭제/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /편집/i })).not.toBeInTheDocument();
    });
});
