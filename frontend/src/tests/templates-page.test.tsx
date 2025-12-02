import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TemplateManagerPage from '@/app/templates/page';

jest.mock('next/navigation', () => ({
    useRouter: () => ({
        push: jest.fn(),
        replace: jest.fn(),
        back: jest.fn(),
    }),
    usePathname: () => '/templates',
    useSearchParams: () => new URLSearchParams(),
}));

describe('Plan 3.13 - 변호사 전용 템플릿 관리', () => {
    test('템플릿 업로드 폼에는 양식 이름 입력과 파일 업로드 필드가 있어야 한다', async () => {
        const user = userEvent.setup();
        render(<TemplateManagerPage />);

        expect(screen.getByRole('heading', { name: /템플릿 관리/i })).toBeInTheDocument();

        const nameInput = screen.getByLabelText(/양식 이름/i);
        const fileInput = screen.getByLabelText(/템플릿 파일/i);
        const uploadButton = screen.getByRole('button', { name: /템플릿 업로드/i });

        await user.type(nameInput, '가사이혼 답변서');
        const file = new File(['dummy'], 'template.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });
        await user.upload(fileInput, file);

        expect(uploadButton).not.toBeDisabled();
    });

    test('업로드된 템플릿 목록에서 각 템플릿에 적용/삭제 액션이 제공되어야 한다', () => {
        render(<TemplateManagerPage />);

        const templateTable = screen.getByRole('table', { name: /템플릿 목록/i });
        expect(templateTable).toBeInTheDocument();

        const applyButtons = screen.getAllByRole('button', { name: /적용/i });
        const deleteButtons = screen.getAllByRole('button', { name: /삭제/i });

        expect(applyButtons.length).toBeGreaterThan(0);
        expect(deleteButtons.length).toBeGreaterThan(0);
    });
});
