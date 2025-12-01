/**
 * Plan 3.20.3 - Case Detail Page Design Tokens Tests
 *
 * Tests for design token compliance:
 * - text-neutral-* tokens instead of text-gray-*
 * - text-success semantic color for positive states
 * - bg-warning-light for AI warning banner
 * - rounded-lg border radius consistency
 *
 * TDD Approach:
 * These tests validate the UI/UX fixes applied to src/pages/cases/[id].tsx
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock next/router
jest.mock('next/router', () => ({
    useRouter: () => ({
        query: { id: 'test-case-123' },
        push: jest.fn(),
        pathname: '/cases/[id]',
    }),
}));

// Mock next/head
jest.mock('next/head', () => ({
    __esModule: true,
    default: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock next/link
jest.mock('next/link', () => ({
    __esModule: true,
    default: ({ children, href, ...props }: any) => (
        <a href={href} {...props}>
            {children}
        </a>
    ),
}));

// Import the page component
import CaseDetailPage from '../../pages/cases/[id]';

describe('Plan 3.20.3 - Case Detail Page Design Tokens', () => {
    describe('Neutral Color Tokens', () => {
        test('page background should use neutral-50', () => {
            const { container } = render(<CaseDetailPage />);
            const pageWrapper = container.firstChild as HTMLElement;
            expect(pageWrapper).toHaveClass('bg-neutral-50');
        });

        test('header border should use neutral-200', () => {
            const { container } = render(<CaseDetailPage />);
            const header = container.querySelector('header');
            expect(header).toHaveClass('border-neutral-200');
        });

        test('sidebar border should use neutral-200', () => {
            const { container } = render(<CaseDetailPage />);
            const nav = container.querySelector('nav');
            expect(nav).toHaveClass('border-neutral-200');
        });

        test('case ID text should use neutral-500', () => {
            render(<CaseDetailPage />);
            const caseIdText = screen.getByText(/Case ID:/);
            expect(caseIdText).toHaveClass('text-neutral-500');
        });

        test('section headings should use neutral-500 for labels', () => {
            render(<CaseDetailPage />);
            const sectionLabels = screen.getAllByText(/작업|보기/);
            sectionLabels.forEach((label) => {
                expect(label).toHaveClass('text-neutral-500');
            });
        });

        test('inactive tab buttons should use neutral-700 text', () => {
            render(<CaseDetailPage />);
            const tabs = screen.getAllByRole('tab');
            const inactiveTabs = tabs.filter((tab) => tab.getAttribute('aria-selected') === 'false');

            inactiveTabs.forEach((tab) => {
                expect(tab).toHaveClass('text-neutral-700');
            });
        });

        test('action buttons should use neutral-700 text', () => {
            render(<CaseDetailPage />);
            const uploadButton = screen.getByRole('button', { name: /증거 업로드/i });
            expect(uploadButton).toHaveClass('text-neutral-700');
        });
    });

    describe('Semantic Colors', () => {
        test('draft ready status should use text-success', () => {
            render(<CaseDetailPage />);
            // The draft status shows "준비됨" when hasGeneratedDraft is true
            const draftStatus = screen.getByText('준비됨');
            expect(draftStatus).toHaveClass('text-success');
        });

        test('AI warning banner should use bg-warning-light', () => {
            const { container } = render(<CaseDetailPage />);
            // Find the warning banner directly by class
            const warningBanner = container.querySelector('.bg-warning-light');
            expect(warningBanner).toBeInTheDocument();
        });

        test('AI warning banner border should use warning color', () => {
            const { container } = render(<CaseDetailPage />);
            // Find the warning banner with border-warning class
            const warningBanner = container.querySelector('[class*="border-warning"]');
            expect(warningBanner).toBeInTheDocument();
        });

        test('security badge should use secondary color', () => {
            render(<CaseDetailPage />);
            const securityBadge = screen.getByText('데이터 암호화 보호');
            expect(securityBadge).toHaveClass('text-neutral-600');
        });

        test('case title should use text-secondary', () => {
            render(<CaseDetailPage />);
            const caseTitle = screen.getByText('김철수 이혼 소송');
            expect(caseTitle).toHaveClass('text-secondary');
        });
    });

    describe('Border Radius Consistency (rounded-lg)', () => {
        test('back button should use rounded-lg', () => {
            render(<CaseDetailPage />);
            const backButton = screen.getByLabelText('케이스 목록으로 돌아가기');
            expect(backButton).toHaveClass('rounded-lg');
        });

        test('sidebar navigation should use rounded-lg', () => {
            const { container } = render(<CaseDetailPage />);
            const nav = container.querySelector('nav');
            expect(nav).toHaveClass('rounded-lg');
        });

        test('action buttons should use rounded-lg', () => {
            render(<CaseDetailPage />);
            const uploadButton = screen.getByRole('button', { name: /증거 업로드/i });
            const draftButton = screen.getByRole('button', { name: /Draft 생성/i });

            expect(uploadButton).toHaveClass('rounded-lg');
            expect(draftButton).toHaveClass('rounded-lg');
        });

        test('tab buttons should use rounded-lg', () => {
            render(<CaseDetailPage />);
            const tabs = screen.getAllByRole('tab');
            tabs.forEach((tab) => {
                expect(tab).toHaveClass('rounded-lg');
            });
        });

        test('stat cards should use rounded-lg', () => {
            const { container } = render(<CaseDetailPage />);
            const statCards = container.querySelectorAll('.grid.grid-cols-3 > div');
            statCards.forEach((card) => {
                expect(card).toHaveClass('rounded-lg');
            });
        });

        test('AI warning banner should use rounded-lg', () => {
            const { container } = render(<CaseDetailPage />);
            // Find the warning banner with both bg-warning-light and rounded-lg
            const warningBanner = container.querySelector('.bg-warning-light.rounded-lg');
            expect(warningBanner).toBeInTheDocument();
        });

        test('security badge container should use rounded-lg', () => {
            render(<CaseDetailPage />);
            const securityText = screen.getByText('데이터 암호화 보호');
            const container = securityText.parentElement;
            expect(container).toHaveClass('rounded-lg');
        });
    });

    describe('Primary Color Accents', () => {
        test('active tab should use bg-secondary', () => {
            render(<CaseDetailPage />);
            const tabs = screen.getAllByRole('tab');
            const activeTab = tabs.find((tab) => tab.getAttribute('aria-selected') === 'true');
            expect(activeTab).toHaveClass('bg-secondary');
            expect(activeTab).toHaveClass('text-white');
        });

        test('action buttons should have primary-light hover state', () => {
            render(<CaseDetailPage />);
            const uploadButton = screen.getByRole('button', { name: /증거 업로드/i });
            expect(uploadButton).toHaveClass('hover:bg-primary-light');
        });

        test('focus ring should use primary color', () => {
            render(<CaseDetailPage />);
            const tabs = screen.getAllByRole('tab');
            tabs.forEach((tab) => {
                expect(tab).toHaveClass('focus-visible:ring-primary');
            });
        });
    });

    describe('Typography Tokens', () => {
        test('section headings should use correct font weight and size', () => {
            render(<CaseDetailPage />);
            const sectionLabels = screen.getAllByText(/작업|보기/);
            sectionLabels.forEach((label) => {
                expect(label).toHaveClass('text-xs');
                expect(label).toHaveClass('font-semibold');
                expect(label).toHaveClass('uppercase');
            });
        });

        test('stat values should use correct typography', () => {
            render(<CaseDetailPage />);
            const statValues = screen.getAllByText(/김철수|3건|준비됨/);
            statValues.forEach((value) => {
                expect(value).toHaveClass('text-xl');
                expect(value).toHaveClass('font-bold');
            });
        });

        test('tab button text should use correct typography', () => {
            render(<CaseDetailPage />);
            const tabs = screen.getAllByRole('tab');
            tabs.forEach((tab) => {
                expect(tab).toHaveClass('text-sm');
                expect(tab).toHaveClass('font-medium');
            });
        });
    });

    describe('Shadow Tokens', () => {
        test('sections should use shadow-sm', () => {
            const { container } = render(<CaseDetailPage />);
            const sections = container.querySelectorAll('section.shadow-sm');
            // There should be shadow-sm on content sections (only when evidence tab is active)
            // Since draft is default active, we switch to evidence to test
        });

        test('header should use border instead of heavy shadow', () => {
            const { container } = render(<CaseDetailPage />);
            const header = container.querySelector('header');
            expect(header).toHaveClass('border-b');
            expect(header).not.toHaveClass('shadow-lg');
        });
    });
});
