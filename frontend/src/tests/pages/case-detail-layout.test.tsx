/**
 * Plan 3.20.3 - Case Detail Page Layout Tests
 *
 * Tests for layout structure:
 * - Left sidebar layout (256px)
 * - Tab navigation in sidebar
 * - Main content area
 * - Tab switching behavior
 *
 * TDD Approach:
 * These tests validate the UI/UX fixes applied to src/pages/cases/[id].tsx
 */

import { render, screen, fireEvent } from '@testing-library/react';
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

describe('Plan 3.20.3 - Case Detail Page Layout', () => {
    describe('Left Sidebar Structure', () => {
        test('should have left sidebar with fixed width', () => {
            const { container } = render(<CaseDetailPage />);
            const aside = container.querySelector('aside');
            expect(aside).toBeInTheDocument();
            expect(aside).toHaveClass('w-64');
            expect(aside).toHaveClass('flex-shrink-0');
        });

        test('sidebar should be sticky positioned', () => {
            const { container } = render(<CaseDetailPage />);
            const nav = container.querySelector('aside nav');
            expect(nav).toHaveClass('sticky');
            expect(nav).toHaveClass('top-24');
        });

        test('sidebar should contain action buttons section', () => {
            render(<CaseDetailPage />);
            const actionsHeading = screen.getByText('작업');
            expect(actionsHeading).toBeInTheDocument();
        });

        test('sidebar should contain view tabs section', () => {
            render(<CaseDetailPage />);
            const viewHeading = screen.getByText('보기');
            expect(viewHeading).toBeInTheDocument();
        });

        test('sidebar sections should be separated by dividers', () => {
            const { container } = render(<CaseDetailPage />);
            const dividers = container.querySelectorAll('nav .border-t');
            expect(dividers.length).toBeGreaterThanOrEqual(2); // At least 2 dividers
        });
    });

    describe('Main Content Area', () => {
        test('should have main content area with flex-1', () => {
            const { container } = render(<CaseDetailPage />);
            const main = container.querySelector('main');
            expect(main).toBeInTheDocument();
            expect(main).toHaveClass('flex-1');
            expect(main).toHaveClass('min-w-0');
        });

        test('should display stats cards in grid layout', () => {
            const { container } = render(<CaseDetailPage />);
            const statsGrid = container.querySelector('.grid.grid-cols-3');
            expect(statsGrid).toBeInTheDocument();
        });

        test('should display 3 stat cards', () => {
            render(<CaseDetailPage />);
            const clientCard = screen.getByText('의뢰인');
            const evidenceCard = screen.getByText('증거 현황');
            const draftCard = screen.getByText('Draft 상태');

            expect(clientCard).toBeInTheDocument();
            expect(evidenceCard).toBeInTheDocument();
            expect(draftCard).toBeInTheDocument();
        });
    });

    describe('Flex Layout Structure', () => {
        test('should use flexbox for sidebar and main layout', () => {
            const { container } = render(<CaseDetailPage />);
            const layoutWrapper = container.querySelector('.flex.gap-6');
            expect(layoutWrapper).toBeInTheDocument();
        });

        test('sidebar and main should have correct gap', () => {
            const { container } = render(<CaseDetailPage />);
            const layoutWrapper = container.querySelector('.flex.gap-6');
            expect(layoutWrapper).toHaveClass('gap-6');
        });
    });

    describe('Action Buttons in Sidebar', () => {
        test('should have upload button', () => {
            render(<CaseDetailPage />);
            const uploadButton = screen.getByRole('button', { name: /증거 업로드/i });
            expect(uploadButton).toBeInTheDocument();
        });

        test('should have draft generation button', () => {
            render(<CaseDetailPage />);
            const draftButton = screen.getByRole('button', { name: /Draft 생성/i });
            expect(draftButton).toBeInTheDocument();
        });

        test('should have share button', () => {
            render(<CaseDetailPage />);
            const shareButton = screen.getByRole('button', { name: /공유하기/i });
            expect(shareButton).toBeInTheDocument();
        });

        test('should have settings button', () => {
            render(<CaseDetailPage />);
            const settingsButton = screen.getByLabelText('케이스 설정 열기');
            expect(settingsButton).toBeInTheDocument();
        });
    });

    describe('Tab Navigation', () => {
        test('should have 4 tabs', () => {
            render(<CaseDetailPage />);
            const tabs = screen.getAllByRole('tab');
            expect(tabs).toHaveLength(4);
        });

        test('tabs should have correct labels', () => {
            render(<CaseDetailPage />);
            expect(screen.getByRole('tab', { name: /증거/i })).toBeInTheDocument();
            expect(screen.getByRole('tab', { name: /상대방 주장/i })).toBeInTheDocument();
            expect(screen.getByRole('tab', { name: /타임라인/i })).toBeInTheDocument();
            expect(screen.getByRole('tab', { name: /Draft/i })).toBeInTheDocument();
        });

        test('draft tab should be active by default', () => {
            render(<CaseDetailPage />);
            const draftTab = screen.getByRole('tab', { name: /Draft/i });
            expect(draftTab).toHaveAttribute('aria-selected', 'true');
        });
    });

    describe('Tab Content Switching', () => {
        test('clicking evidence tab should show evidence content', () => {
            render(<CaseDetailPage />);
            const evidenceTab = screen.getByRole('tab', { name: /증거/i });
            fireEvent.click(evidenceTab);

            // Check for section headings in the evidence tab content
            expect(screen.getByRole('heading', { name: /증거 업로드/i })).toBeInTheDocument();
            expect(screen.getByRole('heading', { name: /증거 목록/i })).toBeInTheDocument();
        });

        test('clicking opponent tab should show opponent content', () => {
            render(<CaseDetailPage />);
            const opponentTab = screen.getByRole('tab', { name: /상대방 주장/i });
            fireEvent.click(opponentTab);

            expect(screen.getByText('상대방 주장 & AI 추천 증거')).toBeInTheDocument();
        });

        test('clicking timeline tab should show timeline content', () => {
            render(<CaseDetailPage />);
            const timelineTab = screen.getByRole('tab', { name: /타임라인/i });
            fireEvent.click(timelineTab);

            expect(screen.getByText('사건 타임라인')).toBeInTheDocument();
        });

        test('clicking draft tab should show draft content', () => {
            const { container } = render(<CaseDetailPage />);
            // First switch to another tab
            const evidenceTab = screen.getByRole('tab', { name: /증거/i });
            fireEvent.click(evidenceTab);

            // Then switch back to draft
            const draftTab = screen.getByRole('tab', { name: /Draft/i });
            fireEvent.click(draftTab);

            // Check for warning banner in draft tab
            const warningBanner = container.querySelector('.bg-warning-light');
            expect(warningBanner).toBeInTheDocument();
        });
    });

    describe('Header Layout', () => {
        test('header should be sticky', () => {
            const { container } = render(<CaseDetailPage />);
            const header = container.querySelector('header');
            expect(header).toHaveClass('sticky');
            expect(header).toHaveClass('top-0');
            expect(header).toHaveClass('z-40');
        });

        test('header should have back navigation', () => {
            render(<CaseDetailPage />);
            const backLink = screen.getByLabelText('케이스 목록으로 돌아가기');
            expect(backLink).toHaveAttribute('href', '/cases');
        });

        test('header should display case title', () => {
            render(<CaseDetailPage />);
            expect(screen.getByText('김철수 이혼 소송')).toBeInTheDocument();
        });

        test('header should display case ID', () => {
            render(<CaseDetailPage />);
            expect(screen.getByText(/Case ID:/)).toBeInTheDocument();
        });

        test('header should have security badge', () => {
            render(<CaseDetailPage />);
            expect(screen.getByText('데이터 암호화 보호')).toBeInTheDocument();
        });
    });

    describe('Page Container', () => {
        test('should have max-width constraint', () => {
            const { container } = render(<CaseDetailPage />);
            const contentWrapper = container.querySelector('.max-w-screen-2xl');
            expect(contentWrapper).toBeInTheDocument();
        });

        test('should have horizontal padding', () => {
            const { container } = render(<CaseDetailPage />);
            const mainLayout = container.querySelector('.max-w-screen-2xl.mx-auto.px-6');
            expect(mainLayout).toBeInTheDocument();
        });
    });

    describe('Evidence Tab Action Button', () => {
        test('clicking upload button should switch to evidence tab', () => {
            render(<CaseDetailPage />);
            const uploadButton = screen.getByRole('button', { name: /증거 업로드/i });
            fireEvent.click(uploadButton);

            // Should show evidence content
            const evidenceTab = screen.getByRole('tab', { name: /증거/i });
            expect(evidenceTab).toHaveAttribute('aria-selected', 'true');
        });
    });

    describe('Draft Generation Modal', () => {
        test('clicking draft generation button should open modal', async () => {
            render(<CaseDetailPage />);
            const draftButton = screen.getByRole('button', { name: /Draft 생성/i });
            fireEvent.click(draftButton);

            // Modal should appear - look for modal dialog
            const modal = await screen.findByRole('dialog');
            expect(modal).toBeInTheDocument();
        });
    });
});
