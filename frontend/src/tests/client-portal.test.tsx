import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ClientEvidencePortal from '@/pages/portal';

jest.mock('next/router', () => ({
    useRouter: () => ({
        query: {
            firm: 'LEH 로펌',
            case: '김 vs 박 사건',
        },
    }),
}));

describe('Plan 3.7 - Client Evidence Submission Portal', () => {
    test('renders only the required portal elements: logo, guidance, single upload zone, and feedback area', () => {
        render(<ClientEvidencePortal />);

        expect(screen.getByText(/Legal Evidence Hub/i)).toBeInTheDocument();
        expect(screen.getByText(/안내/)).toBeInTheDocument();

        const uploadZones = screen.getAllByTestId('client-upload-zone');
        expect(uploadZones).toHaveLength(1);

        const feedback = screen.getByTestId('upload-feedback');
        expect(feedback).toBeInTheDocument();
        expect(feedback).toHaveTextContent(/준비/i);
    });

    test('shows success green confirmation after files are uploaded', async () => {
        render(<ClientEvidencePortal />);

        const fileInput = screen.getByLabelText('증거 파일 업로드') as HTMLInputElement;
        const files = [
            new File(['dummy'], 'chat-log.txt', { type: 'text/plain' }),
            new File(['dummy'], 'photo.jpg', { type: 'image/jpeg' }),
        ];

        fireEvent.change(fileInput, { target: { files } });

        await waitFor(() => {
            const successMessage = screen.getByText(/파일 2개가 안전하게 전송되었습니다\./);
            expect(successMessage).toHaveClass('text-success-green');
        });
    });

    test('reveals the uploaded file names to reassure the client after selection', async () => {
        render(<ClientEvidencePortal />);

        const fileInput = screen.getByLabelText('증거 파일 업로드') as HTMLInputElement;
        const files = [
            new File(['dummy'], 'contract.pdf', { type: 'application/pdf' }),
            new File(['dummy'], 'evidence-photo.png', { type: 'image/png' }),
        ];

        fireEvent.change(fileInput, { target: { files } });

        await waitFor(() => {
            expect(screen.getByText('contract.pdf')).toBeInTheDocument();
            expect(screen.getByText('evidence-photo.png')).toBeInTheDocument();
        });
    });

    test('shows an uploading indicator before the success confirmation is rendered', async () => {
        jest.useFakeTimers();
        render(<ClientEvidencePortal />);

        const fileInput = screen.getByLabelText('증거 파일 업로드') as HTMLInputElement;
        const files = [new File(['dummy'], 'timeline.xlsx', { type: 'application/vnd.ms-excel' })];

        fireEvent.change(fileInput, { target: { files } });

        const uploadingStatus = screen.getByRole('status');
        expect(uploadingStatus).toHaveTextContent(/업로드 중/i);

        act(() => {
            jest.advanceTimersByTime(1500);
        });

        await waitFor(() => {
            expect(screen.getByText(/파일 1개가 안전하게 전송되었습니다\./)).toBeInTheDocument();
        });

        jest.useRealTimers();
    });

    test('personalizes the guidance copy with firm and case names plus encryption reassurance', () => {
        render(<ClientEvidencePortal />);

        expect(
            screen.getByText(/LEH 로펌의 '김 vs 박 사건'을 위한 증거 제출 페이지입니다./),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/모든 파일은 종단간 암호화되어 담당 변호사에게만 안전하게 전송됩니다./),
        ).toBeInTheDocument();
    });
});
