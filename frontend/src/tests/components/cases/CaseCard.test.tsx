import { render, screen } from '@testing-library/react';
import { RouterContext } from 'next/dist/shared/lib/router-context';
import { NextRouter } from 'next/router';
import CaseCard from '@/components/cases/CaseCard';
import { Case } from '@/types/case';

const mockCase: Case = {
    id: 'case-card-test',
    title: '홍길동 정비팀 증거 수집',
    clientName: '홍길동',
    status: 'open',
    evidenceCount: 12,
    draftStatus: 'ready',
    lastUpdated: '2024-09-17T14:45:00Z',
};

const mockRouter: NextRouter = {
    basePath: '',
    pathname: '/',
    route: '/',
    query: {},
    asPath: '/',
    back: jest.fn(),
    beforePopState: jest.fn(),
    prefetch: jest.fn().mockResolvedValue(undefined),
    push: jest.fn(),
    reload: jest.fn(),
    replace: jest.fn(),
    events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn(),
    },
    isFallback: false,
    isReady: true,
    isPreview: false,
    locale: undefined,
    locales: [],
    defaultLocale: undefined,
} as unknown as NextRouter;

describe('CaseCard (plan 3.3)', () => {
    it('renders case details and follows Calm Control tokens for layout', () => {
        render(
            <RouterContext.Provider value={mockRouter}>
                <CaseCard caseData={mockCase} />
            </RouterContext.Provider>
        );

        const title = screen.getByRole('heading', { name: mockCase.title });
        expect(title).toHaveClass('text-deep-trust-blue');

        expect(screen.getByText(`증거 ${mockCase.evidenceCount}건`)).toBeInTheDocument();
        expect(screen.getByText(/최근 업데이트:/)).toBeInTheDocument();
        expect(screen.getByText(/Draft 상태:/)).toBeInTheDocument();

        const card = title.closest('div.card');
        expect(card).not.toBeNull();
        expect(card).toHaveClass('bg-calm-grey');
    });
});
