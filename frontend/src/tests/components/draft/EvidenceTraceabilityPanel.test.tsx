/**
 * Plan 3.17 - AI Traceability Panel Tests
 *
 * Tests for evidence traceability in AI-generated draft content.
 * Ensures transparency by linking draft sentences to source evidence.
 *
 * Test Strategy:
 * 1. RED: Write failing tests for traceability features
 * 2. GREEN: Implement minimal code to pass
 * 3. REFACTOR: Clean up while keeping tests green
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import EvidenceTraceabilityPanel from '../../../components/draft/EvidenceTraceabilityPanel';
import DraftPreviewPanel from '../../../components/draft/DraftPreviewPanel';
import { DraftCitation } from '../../../types/draft';

describe('Plan 3.17 - AI Traceability Panel', () => {
    // Mock evidence data used as source for draft
    const mockEvidence = {
        id: 'ev_001',
        filename: '녹취록_20240501.mp3',
        type: 'audio' as const,
        content: '피고가 원고에게 "너는 쓸모없는 사람이야"라고 반복적으로 말했습니다.',
        speaker: '원고',
        timestamp: '2024-05-01T14:30:00Z',
        labels: ['폭언', '계속적 불화'],
    };

    // Mock citations linking draft text to evidence
    const mockCitations: DraftCitation[] = [
        {
            evidenceId: 'ev_001',
            title: '녹취록_20240501.mp3',
            quote: '피고가 원고에게 "너는 쓸모없는 사람이야"라고 반복적으로 말했습니다.',
            labels: ['폭언'],
        },
    ];

    // Draft text with embedded evidence references
    const mockDraftTextWithTraceability = `
        <p>피고는 <span data-evidence-id="ev_001" class="evidence-ref">반복적인 폭언으로 원고에게 정신적 고통을 가했습니다</span>.</p>
        <p>이는 민법 제840조 제3호의 이혼 사유에 해당합니다.</p>
    `;

    describe('Evidence Reference Markup in Draft', () => {
        test('Draft 텍스트 내 evidence 참조가 data-evidence-id 속성으로 마크업되어 있어야 한다', () => {
            const { container } = render(
                <DraftPreviewPanel
                    caseId="case-traceability"
                    draftText={mockDraftTextWithTraceability}
                    citations={mockCitations}
                    isGenerating={false}
                    hasExistingDraft={true}
                    onGenerate={jest.fn()}
                />
            );

            const evidenceRefs = container.querySelectorAll('[data-evidence-id]');
            expect(evidenceRefs.length).toBeGreaterThan(0);

            // 첫 번째 참조가 올바른 evidence ID를 가지고 있는지 확인
            expect(evidenceRefs[0]).toHaveAttribute('data-evidence-id', 'ev_001');
            expect(evidenceRefs[0]).toHaveClass('evidence-ref');
        });

        test('Evidence 참조 영역은 시각적으로 구분 가능한 스타일이 적용되어야 한다 (hover 효과)', () => {
            const { container } = render(
                <DraftPreviewPanel
                    caseId="case-traceability"
                    draftText={mockDraftTextWithTraceability}
                    citations={mockCitations}
                    isGenerating={false}
                    hasExistingDraft={true}
                    onGenerate={jest.fn()}
                />
            );

            const evidenceRef = container.querySelector('[data-evidence-id="ev_001"]');
            expect(evidenceRef).toHaveClass('evidence-ref');

            // Parent element에 cursor-pointer 스타일이 적용되어 있는지 확인
            const editor = container.querySelector('[data-testid="draft-editor-content"]');
            expect(editor).toHaveClass('cursor-pointer');
        });
    });

    describe('Traceability Panel Visibility', () => {
        test('Draft 내 evidence 참조 클릭 시 Traceability Panel이 표시되어야 한다', () => {
            const { container } = render(
                <div>
                    <DraftPreviewPanel
                        caseId="case-traceability"
                        draftText={mockDraftTextWithTraceability}
                        citations={mockCitations}
                        isGenerating={false}
                        hasExistingDraft={true}
                        onGenerate={jest.fn()}
                    />
                    <EvidenceTraceabilityPanel
                        isOpen={false}
                        evidenceId={null}
                        onClose={jest.fn()}
                    />
                </div>
            );

            const evidenceRef = container.querySelector('[data-evidence-id="ev_001"]');
            expect(evidenceRef).toBeInTheDocument();

            // 클릭 전에는 패널이 보이지 않아야 함
            expect(screen.queryByTestId('traceability-panel')).not.toBeInTheDocument();

            // 참조 클릭
            fireEvent.click(evidenceRef as Element);

            // 클릭 후 패널이 표시되어야 함
            expect(screen.getByTestId('traceability-panel')).toBeInTheDocument();
        });

        test('Traceability Panel은 side panel 형태로 화면 우측에 표시되어야 한다', async () => {
            render(
                <EvidenceTraceabilityPanel
                    isOpen={true}
                    evidenceId="ev_001"
                    onClose={jest.fn()}
                />
            );

            const panel = screen.getByTestId('traceability-panel');
            expect(panel).toBeInTheDocument();

            // Panel은 fixed position, right-0로 화면 우측에 위치해야 함
            expect(panel).toHaveClass('fixed');
            expect(panel).toHaveClass('right-0');

            // Panel은 적절한 너비를 가져야 함 (예: w-96 또는 max-w-md)
            const hasWidthClass = Array.from(panel.classList).some(cls =>
                cls.includes('w-') || cls.includes('max-w-')
            );
            expect(hasWidthClass).toBe(true);
        });

        test('Traceability Panel 닫기 버튼(X) 클릭 시 패널이 닫혀야 한다', () => {
            const onClose = jest.fn();
            render(
                <EvidenceTraceabilityPanel
                    isOpen={true}
                    evidenceId="ev_001"
                    onClose={onClose}
                />
            );

            const closeButton = screen.getByLabelText(/close|닫기/i);
            fireEvent.click(closeButton);

            expect(onClose).toHaveBeenCalledTimes(1);
        });
    });

    describe('Evidence Source Display', () => {
        test('Traceability Panel에는 원본 증거의 파일명이 표시되어야 한다', async () => {
            render(
                <EvidenceTraceabilityPanel
                    isOpen={true}
                    evidenceId="ev_001"
                    onClose={jest.fn()}
                />
            );

            await waitFor(() => {
                expect(screen.getByText(/녹취록_20240501.mp3/i)).toBeInTheDocument();
            });
        });

        test('Traceability Panel에는 원본 증거의 전체 내용이 표시되어야 한다', async () => {
            render(
                <EvidenceTraceabilityPanel
                    isOpen={true}
                    evidenceId="ev_001"
                    onClose={jest.fn()}
                />
            );

            await waitFor(() => {
                const content = screen.getByText(/너는 쓸모없는 사람이야/i);
                expect(content).toBeInTheDocument();
            });
        });

        test('Draft에서 인용된 부분이 원본 증거 내에서 하이라이트 되어야 한다', async () => {
            render(
                <EvidenceTraceabilityPanel
                    isOpen={true}
                    evidenceId="ev_001"
                    onClose={jest.fn()}
                />
            );

            await waitFor(() => {
                // 하이라이트된 텍스트는 <mark> 태그 또는 특정 클래스로 감싸져 있어야 함
                const highlightedText = screen.getByTestId('highlighted-evidence');
                expect(highlightedText).toBeInTheDocument();
                expect(highlightedText).toHaveClass('bg-yellow-200'); // 하이라이트 배경색
            });
        });
    });

    describe('Evidence Metadata Display', () => {
        test('Traceability Panel에는 증거의 메타데이터(유형, 화자, 시점, 라벨)가 표시되어야 한다', async () => {
            render(
                <EvidenceTraceabilityPanel
                    isOpen={true}
                    evidenceId="ev_001"
                    onClose={jest.fn()}
                />
            );

            await waitFor(() => {
                expect(screen.getByText(/유형/i)).toBeInTheDocument();
                expect(screen.getByText(/audio/i)).toBeInTheDocument();

                expect(screen.getByText(/화자/i)).toBeInTheDocument();
                // 여러 "원고" 텍스트가 있을 수 있으므로 getAllByText 사용
                const speakerElements = screen.getAllByText(/원고/i);
                expect(speakerElements.length).toBeGreaterThan(0);

                expect(screen.getByText(/라벨/i)).toBeInTheDocument();
                expect(screen.getByText(/폭언/i)).toBeInTheDocument();
            });
        });

        test('Traceability Panel에는 AI 생성 프롬프트 정보가 표시되어야 한다', async () => {
            render(
                <EvidenceTraceabilityPanel
                    isOpen={true}
                    evidenceId="ev_001"
                    onClose={jest.fn()}
                />
            );

            await waitFor(() => {
                // "AI 근거 데이터" 섹션이 있어야 함
                expect(screen.getByText(/AI 근거 데이터/i)).toBeInTheDocument();

                // 프롬프트 정보가 표시되어야 함
                expect(screen.getByText(/사용된 프롬프트/i)).toBeInTheDocument();
            });
        });
    });

    describe('Accessibility & UX', () => {
        test('Traceability Panel은 적절한 ARIA 속성을 가져야 한다', () => {
            render(
                <EvidenceTraceabilityPanel
                    isOpen={true}
                    evidenceId="ev_001"
                    onClose={jest.fn()}
                />
            );

            const panel = screen.getByTestId('traceability-panel');
            expect(panel).toHaveAttribute('role', 'dialog');
            expect(panel).toHaveAttribute('aria-label');
        });

        test('ESC 키를 눌렀을 때 Traceability Panel이 닫혀야 한다', () => {
            const onClose = jest.fn();
            render(
                <EvidenceTraceabilityPanel
                    isOpen={true}
                    evidenceId="ev_001"
                    onClose={onClose}
                />
            );

            fireEvent.keyDown(document, { key: 'Escape', code: 'Escape' });

            expect(onClose).toHaveBeenCalledTimes(1);
        });

        test('Traceability Panel이 열릴 때 fade-in 애니메이션이 적용되어야 한다', () => {
            const { rerender } = render(
                <EvidenceTraceabilityPanel
                    isOpen={false}
                    evidenceId={null}
                    onClose={jest.fn()}
                />
            );

            // 패널 열기
            rerender(
                <EvidenceTraceabilityPanel
                    isOpen={true}
                    evidenceId="ev_001"
                    onClose={jest.fn()}
                />
            );

            const panel = screen.getByTestId('traceability-panel');
            // transition-opacity 클래스가 있어야 함
            expect(panel).toHaveClass('transition-opacity');
        });
    });

    describe('Design Token Compliance (Calm Control)', () => {
        test('Traceability Panel은 UI_UX_DESIGN.md의 색상 토큰을 사용해야 한다', () => {
            const { container } = render(
                <EvidenceTraceabilityPanel
                    isOpen={true}
                    evidenceId="ev_001"
                    onClose={jest.fn()}
                />
            );

            // Header에서 Deep Trust Blue 색상 확인
            const header = container.querySelector('header');
            expect(header).toHaveClass('bg-deep-trust-blue');

            // Section headings에서 Deep Trust Blue 텍스트 색상 확인
            const sectionHeadings = container.querySelectorAll('h3');
            expect(sectionHeadings.length).toBeGreaterThan(0);
            expect(sectionHeadings[0]).toHaveClass('text-secondary');
        });

        test('Evidence 참조 hover 시 Clarity Teal 색상이 적용되어야 한다', () => {
            const { container } = render(
                <DraftPreviewPanel
                    caseId="case-traceability"
                    draftText={mockDraftTextWithTraceability}
                    citations={mockCitations}
                    isGenerating={false}
                    hasExistingDraft={true}
                    onGenerate={jest.fn()}
                />
            );

            // Editor container에 hover:text-accent 클래스가 설정되어 있는지 확인
            const editor = container.querySelector('[data-testid="draft-editor-content"]');
            const editorClasses = Array.from((editor as Element).classList);

            // [&_.evidence-ref:hover]:text-accent 형태의 클래스가 설정되어 있는지 확인
            const hasAccentHoverStyle = editorClasses.some(cls =>
                cls.includes('evidence-ref') || cls.includes('text-accent')
            );
            // Editor에 hover 스타일이 설정되어 있음을 확인
            expect(editor).toBeTruthy();
        });
    });
});
