import { render, screen } from '@testing-library/react';
import EvidenceUpload from '@/components/evidence/EvidenceUpload';
import EvidenceTable from '@/components/evidence/EvidenceTable';
import { Evidence } from '@/types/evidence';

describe('Plan 3.4 - Evidence Upload & List Requirements', () => {
    describe('증거 업로드 영역', () => {
        test('"파일을 끌어다 놓거나 클릭하여 업로드" 문구를 포함해야 한다', () => {
            const mockOnUpload = jest.fn();
            render(<EvidenceUpload onUpload={mockOnUpload} />);

            // Check for the exact text or similar variation
            expect(screen.getByText(/파일을.*끌어다.*놓거나.*클릭.*업로드/i)).toBeInTheDocument();
        });

        test('큰 드래그 앤 드롭 영역을 보여야 한다', () => {
            const mockOnUpload = jest.fn();
            const { container } = render(<EvidenceUpload onUpload={mockOnUpload} />);

            // Check for drag and drop area with appropriate styling
            const dropZone = container.querySelector('[class*="border-2"][class*="border-dashed"]');
            expect(dropZone).toBeInTheDocument();
        });
    });

    describe('Evidence 테이블 필수 컬럼', () => {
        const mockEvidence: Evidence[] = [
            {
                id: 'ev-1',
                filename: 'test-document.pdf',
                type: 'pdf',
                size: 1024000,
                uploadDate: '2024-05-15T10:30:00Z',
                summary: 'AI generated summary of the document',
                status: 'completed',
                caseId: 'case-123',
            },
        ];

        test('유형 아이콘 컬럼이 있어야 한다', () => {
            render(<EvidenceTable items={mockEvidence} />);
            expect(screen.getByText('유형')).toBeInTheDocument();
        });

        test('파일명 컬럼이 있어야 한다', () => {
            render(<EvidenceTable items={mockEvidence} />);
            expect(screen.getByText('파일명')).toBeInTheDocument();
            expect(screen.getByText('test-document.pdf')).toBeInTheDocument();
        });

        test('업로드 날짜 컬럼이 있어야 한다', () => {
            render(<EvidenceTable items={mockEvidence} />);
            expect(screen.getByText('업로드 날짜')).toBeInTheDocument();
        });

        test('AI 요약 컬럼이 있어야 한다', () => {
            render(<EvidenceTable items={mockEvidence} />);
            expect(screen.getByText('AI 요약')).toBeInTheDocument();
            expect(screen.getByText('AI generated summary of the document')).toBeInTheDocument();
        });

        test('상태 컬럼이 있어야 한다', () => {
            render(<EvidenceTable items={mockEvidence} />);
            expect(screen.getByText('상태')).toBeInTheDocument();
        });

        test('작업 액션 컬럼이 있어야 한다', () => {
            const { container } = render(<EvidenceTable items={mockEvidence} />);
            // Check for action button (MoreVertical icon)
            const actionButton = container.querySelector('button');
            expect(actionButton).toBeInTheDocument();
        });
    });

    describe('상태 컬럼 표시', () => {
        test('업로드 중 상태를 표시할 수 있어야 한다', () => {
            const mockEvidence: Evidence[] = [{
                id: 'ev-1',
                filename: 'uploading.pdf',
                type: 'pdf',
                size: 1024000,
                uploadDate: '2024-05-15T10:30:00Z',
                status: 'uploading',
                caseId: 'case-123',
            }];

            render(<EvidenceTable items={mockEvidence} />);
            // Should display "업로드 중" or similar
            expect(screen.getByText(/업로드.*중/i) || screen.getByText(/uploading/i)).toBeInTheDocument();
        });

        test('처리 대기 상태를 표시할 수 있어야 한다', () => {
            const mockEvidence: Evidence[] = [{
                id: 'ev-2',
                filename: 'queued.pdf',
                type: 'pdf',
                size: 1024000,
                uploadDate: '2024-05-15T10:30:00Z',
                status: 'queued',
                caseId: 'case-123',
            }];

            render(<EvidenceTable items={mockEvidence} />);
            expect(screen.getByText(/대기.*중/i)).toBeInTheDocument();
        });

        test('분석 중 상태를 표시할 수 있어야 한다', () => {
            const mockEvidence: Evidence[] = [{
                id: 'ev-3',
                filename: 'processing.pdf',
                type: 'pdf',
                size: 1024000,
                uploadDate: '2024-05-15T10:30:00Z',
                status: 'processing',
                caseId: 'case-123',
            }];

            render(<EvidenceTable items={mockEvidence} />);
            expect(screen.getByText(/분석.*중/i)).toBeInTheDocument();
        });

        test('검토 필요 상태를 표시할 수 있어야 한다', () => {
            const mockEvidence: Evidence[] = [{
                id: 'ev-4',
                filename: 'review.pdf',
                type: 'pdf',
                size: 1024000,
                uploadDate: '2024-05-15T10:30:00Z',
                status: 'review_needed',
                caseId: 'case-123',
            }];

            render(<EvidenceTable items={mockEvidence} />);
            expect(screen.getByText(/검토.*필요/i) || screen.getByText(/review/i)).toBeInTheDocument();
        });

        test('완료 상태를 표시할 수 있어야 한다', () => {
            const mockEvidence: Evidence[] = [{
                id: 'ev-5',
                filename: 'completed.pdf',
                type: 'pdf',
                size: 1024000,
                uploadDate: '2024-05-15T10:30:00Z',
                status: 'completed',
                caseId: 'case-123',
            }];

            render(<EvidenceTable items={mockEvidence} />);
            expect(screen.getByText(/완료/i)).toBeInTheDocument();
        });
    });

    describe('Plan 3.11 - 증거 목록 인터랙션', () => {
        test('증거 유형별 필터링 컨트롤이 있어야 한다', () => {
            const mockEvidence: Evidence[] = [
                {
                    id: 'ev-1',
                    filename: 'test.pdf',
                    type: 'pdf',
                    size: 1024000,
                    uploadDate: '2024-05-15T10:30:00Z',
                    status: 'completed',
                    caseId: 'case-123',
                },
            ];

            render(<EvidenceTable items={mockEvidence} />);

            // 필터 컨트롤 확인
            expect(screen.getByLabelText(/유형.*필터/i) || screen.getByRole('combobox', { name: /유형/i })).toBeInTheDocument();
        });

        test('각 증거 항목에 수정/삭제 액션 버튼이 있어야 한다', async () => {
            const mockEvidence: Evidence[] = [
                {
                    id: 'ev-1',
                    filename: 'test.pdf',
                    type: 'pdf',
                    size: 1024000,
                    uploadDate: '2024-05-15T10:30:00Z',
                    status: 'completed',
                    caseId: 'case-123',
                },
            ];

            const { container } = render(<EvidenceTable items={mockEvidence} />);

            // 액션 버튼 확인 (MoreVertical 아이콘)
            const actionButtons = container.querySelectorAll('button');
            expect(actionButtons.length).toBeGreaterThan(0);
        });
    });
});
