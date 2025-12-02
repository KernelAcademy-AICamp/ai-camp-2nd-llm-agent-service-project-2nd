/**
 * CasesPage Tests (TDD Red Phase)
 * Tests for /cases page improvements:
 * 1. Display user name in header
 * 2. Case creation button works
 * 3. Show mock example cases when empty
 * 4. Distinguish API error vs empty state
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';

// Mock Next.js navigation
const mockPush = jest.fn();
const mockReplace = jest.fn();
jest.mock('next/navigation', () => ({
    useRouter: () => ({
        push: mockPush,
        replace: mockReplace,
        back: jest.fn(),
    }),
    usePathname: () => '/cases',
    useSearchParams: () => new URLSearchParams(),
}));

// Mock cases API
jest.mock('@/lib/api/cases', () => ({
    getCases: jest.fn(),
    Case: {},
}));

// Import after mocks
import CasesPage from '@/app/cases/page';
import { getCases } from '@/lib/api/cases';

const mockGetCases = getCases as jest.MockedFunction<typeof getCases>;

// Mock localStorage
const localStorageMock = (() => {
    let store: Record<string, string> = {};
    return {
        getItem: (key: string) => store[key] || null,
        setItem: (key: string, value: string) => { store[key] = value; },
        removeItem: (key: string) => { delete store[key]; },
        clear: () => { store = {}; },
    };
})();
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('CasesPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorageMock.clear();
        // Set up authenticated user
        localStorageMock.setItem('authToken', 'test-token');
        localStorageMock.setItem('appVersion', '0.2.0');
    });

    describe('1. User Name Display', () => {
        it('should display user name in header when logged in', async () => {
            // Set user info in localStorage (as saved during login)
            localStorageMock.setItem('user', JSON.stringify({
                id: '1',
                email: 'asdf@example.com',
                name: '김진만',
                role: 'lawyer',
            }));

            mockGetCases.mockResolvedValue({
                data: { cases: [], total: 0 },
                status: 200,
            });

            render(<CasesPage />);

            // Wait for loading to finish
            await waitFor(() => {
                expect(screen.queryByText('로딩 중...')).not.toBeInTheDocument();
            });

            // Should display user name instead of generic greeting
            expect(screen.getByText(/김진만/)).toBeInTheDocument();
        });

        it('should show generic greeting when user name is not available', async () => {
            // No user info in localStorage
            mockGetCases.mockResolvedValue({
                data: { cases: [], total: 0 },
                status: 200,
            });

            render(<CasesPage />);

            await waitFor(() => {
                expect(screen.queryByText('로딩 중...')).not.toBeInTheDocument();
            });

            // Should show fallback greeting
            expect(screen.getByText(/환영합니다/)).toBeInTheDocument();
        });
    });

    describe('2. Case Creation Button', () => {
        it('should open modal when "새 사건 등록" button is clicked', async () => {
            localStorageMock.setItem('user', JSON.stringify({
                id: '1',
                email: 'test@example.com',
                name: 'Test User',
                role: 'lawyer',
            }));

            mockGetCases.mockResolvedValue({
                data: { cases: [], total: 0 },
                status: 200,
            });

            render(<CasesPage />);

            await waitFor(() => {
                expect(screen.queryByText('로딩 중...')).not.toBeInTheDocument();
            });

            // Find and click the button (use role button with exact name)
            const addButton = screen.getByRole('button', { name: /새 사건 등록/i });
            expect(addButton).toBeInTheDocument();
            expect(addButton).not.toBeDisabled();

            fireEvent.click(addButton);

            // Modal should be open - check for modal dialog role or backdrop
            // The AddCaseModal should render when isModalOpen is true
            await waitFor(() => {
                // Check that the modal is rendered (AddCaseModal isOpen prop becomes true)
                const buttons = screen.getAllByRole('button');
                // When modal is open, there should be more buttons (cancel, submit in modal)
                expect(buttons.length).toBeGreaterThan(2);
            });
        });
    });

    describe('3. Mock Example Cases', () => {
        it('should show example mock cases when no cases exist', async () => {
            localStorageMock.setItem('user', JSON.stringify({
                id: '1',
                email: 'test@example.com',
                name: 'Test User',
                role: 'lawyer',
            }));

            // Return empty cases (not an error)
            mockGetCases.mockResolvedValue({
                data: { cases: [], total: 0 },
                status: 200,
            });

            render(<CasesPage />);

            await waitFor(() => {
                expect(screen.queryByText('로딩 중...')).not.toBeInTheDocument();
            });

            // Should show example cases section
            expect(screen.getByText(/예시 사건/i)).toBeInTheDocument();
            // Should show at least one example case
            expect(screen.getByText(/이혼 소송 예시/i)).toBeInTheDocument();
        });

        it('should indicate example cases are for demonstration only', async () => {
            localStorageMock.setItem('user', JSON.stringify({
                id: '1',
                email: 'test@example.com',
                name: 'Test User',
                role: 'lawyer',
            }));

            mockGetCases.mockResolvedValue({
                data: { cases: [], total: 0 },
                status: 200,
            });

            render(<CasesPage />);

            await waitFor(() => {
                expect(screen.queryByText('로딩 중...')).not.toBeInTheDocument();
            });

            // Should show disclaimer about example data
            // Use getAllBy since there are multiple "예시" elements
            const exampleIndicators = screen.getAllByText(/예시|데모/i);
            expect(exampleIndicators.length).toBeGreaterThan(0);
            // Should have description text about the examples
            expect(screen.getByText(/LEH 플랫폼 사용 예시/i)).toBeInTheDocument();
        });
    });

    describe('4. Error vs Empty State', () => {
        it('should show error message when API fails', async () => {
            localStorageMock.setItem('user', JSON.stringify({
                id: '1',
                email: 'test@example.com',
                name: 'Test User',
                role: 'lawyer',
            }));

            // Return error
            mockGetCases.mockResolvedValue({
                error: '서버 오류가 발생했습니다.',
                status: 500,
            });

            render(<CasesPage />);

            await waitFor(() => {
                expect(screen.queryByText('로딩 중...')).not.toBeInTheDocument();
            });

            // Should show specific error message
            expect(screen.getByText(/서버 오류|불러오는데 실패/i)).toBeInTheDocument();
            // Should show retry button
            expect(screen.getByRole('button', { name: /다시 시도/i })).toBeInTheDocument();
        });

        it('should show empty state message when no cases exist (not an error)', async () => {
            localStorageMock.setItem('user', JSON.stringify({
                id: '1',
                email: 'test@example.com',
                name: 'Test User',
                role: 'lawyer',
            }));

            // Return empty cases successfully
            mockGetCases.mockResolvedValue({
                data: { cases: [], total: 0 },
                status: 200,
            });

            render(<CasesPage />);

            await waitFor(() => {
                expect(screen.queryByText('로딩 중...')).not.toBeInTheDocument();
            });

            // Should show empty state message (not error)
            expect(screen.getByText(/등록된 사건이 없습니다/i)).toBeInTheDocument();
            // Should NOT show error styling or retry button
            expect(screen.queryByRole('button', { name: /다시 시도/i })).not.toBeInTheDocument();
        });

        it('should show network error message when network fails', async () => {
            localStorageMock.setItem('user', JSON.stringify({
                id: '1',
                email: 'test@example.com',
                name: 'Test User',
                role: 'lawyer',
            }));

            // Simulate network error
            mockGetCases.mockRejectedValue(new Error('Network error'));

            render(<CasesPage />);

            await waitFor(() => {
                expect(screen.queryByText('로딩 중...')).not.toBeInTheDocument();
            });

            // Should show network error message
            expect(screen.getByText(/네트워크|연결/i)).toBeInTheDocument();
        });
    });

    describe('Real Cases Display', () => {
        it('should display actual cases when they exist', async () => {
            localStorageMock.setItem('user', JSON.stringify({
                id: '1',
                email: 'test@example.com',
                name: 'Test User',
                role: 'lawyer',
            }));

            mockGetCases.mockResolvedValue({
                data: {
                    cases: [
                        {
                            id: '1',
                            title: '김OO vs 박OO 이혼소송',
                            client_name: '김OO',
                            status: 'active',
                            evidence_count: 5,
                            draft_status: 'not_started',
                            created_at: '2025-01-01T00:00:00Z',
                            updated_at: '2025-01-01T00:00:00Z',
                        },
                    ],
                    total: 1,
                },
                status: 200,
            });

            render(<CasesPage />);

            await waitFor(() => {
                expect(screen.queryByText('로딩 중...')).not.toBeInTheDocument();
            });

            // Should display the case
            expect(screen.getByText('김OO vs 박OO 이혼소송')).toBeInTheDocument();
            // Should NOT show example cases when real cases exist
            expect(screen.queryByText(/예시 사건/i)).not.toBeInTheDocument();
        });
    });
});
