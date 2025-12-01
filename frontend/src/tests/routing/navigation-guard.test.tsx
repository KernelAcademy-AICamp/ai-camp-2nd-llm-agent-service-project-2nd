/**
 * Plan 3.19.2 - Navigation Guard Tests
 *
 * Tests for automatic redirection of authenticated users to /cases
 * Ensures proper routing behavior based on authentication state.
 *
 * Test Strategy:
 * 1. RED: Write failing tests for navigation guard
 * 2. GREEN: Implement minimal code to pass
 * 3. REFACTOR: Clean up while keeping tests green
 */

import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useRouter } from 'next/navigation';

// We'll need to test the pages that should have navigation guards
import HomePage from '../../app/page';
import LoginPage from '../../app/login/page';

// Mock the router
jest.mock('next/navigation', () => ({
    useRouter: jest.fn(),
}));

// Mock IntersectionObserver
const mockIntersectionObserver = jest.fn();
mockIntersectionObserver.mockReturnValue({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
});
window.IntersectionObserver = mockIntersectionObserver as any;

describe('Plan 3.19.2 - Navigation Guard', () => {
    let mockPush: jest.Mock;
    let mockReplace: jest.Mock;

    beforeEach(() => {
        // Clear localStorage before each test
        localStorage.clear();

        mockPush = jest.fn();
        mockReplace = jest.fn();
        (useRouter as jest.Mock).mockReturnValue({
            push: mockPush,
            replace: mockReplace,
        });
    });

    afterEach(() => {
        jest.clearAllMocks();
        localStorage.clear();
    });

    describe('Landing Page (/) - Unauthenticated Access', () => {
        test('Unauthenticated user should see landing page content', () => {
            // No authToken in localStorage
            render(<HomePage />);

            // Landing page should be visible - check for main heading
            expect(screen.getByText(/Legal Evidence Hub가 해결합니다/i)).toBeInTheDocument();
        });

        test('Unauthenticated user should NOT be redirected from landing page', () => {
            // No authToken in localStorage
            render(<HomePage />);

            // Should not redirect
            expect(mockPush).not.toHaveBeenCalled();
        });
    });

    describe('Landing Page (/) - Authenticated Access', () => {
        test('Authenticated user accessing landing page should be redirected to /cases', async () => {
            // Set authToken in localStorage
            localStorage.setItem('authToken', 'fake-jwt-token');

            render(<HomePage />);

            // Should redirect to /cases
            await waitFor(() => {
                expect(mockPush).toHaveBeenCalledWith('/cases');
            });
        });

        test('Landing page redirect should happen in useEffect', async () => {
            localStorage.setItem('authToken', 'fake-jwt-token');

            render(<HomePage />);

            // Redirect should happen quickly
            await waitFor(() => {
                expect(mockPush).toHaveBeenCalled();
            }, { timeout: 500 });
        });
    });

    describe('Login Page (/login) - Unauthenticated Access', () => {
        test('Unauthenticated user should see login page content', () => {
            // No authToken in localStorage
            render(<LoginPage />);

            // Login form heading should be visible
            expect(screen.getByRole('heading', { name: /Legal Evidence Hub/i })).toBeInTheDocument();
        });

        test('Unauthenticated user should NOT be redirected from login page', () => {
            // No authToken in localStorage
            render(<LoginPage />);

            // Should not redirect
            expect(mockPush).not.toHaveBeenCalled();
        });
    });

    describe('Login Page (/login) - Authenticated Access', () => {
        test('Authenticated user accessing login page should be redirected to /cases', async () => {
            // Set authToken in localStorage
            localStorage.setItem('authToken', 'fake-jwt-token');

            render(<LoginPage />);

            // Should redirect to /cases
            await waitFor(() => {
                expect(mockPush).toHaveBeenCalledWith('/cases');
            });
        });

        test('Login page navigation guard should check localStorage on mount', async () => {
            localStorage.setItem('authToken', 'fake-jwt-token');

            const getItemSpy = jest.spyOn(Storage.prototype, 'getItem');

            render(<LoginPage />);

            // Should check for authToken
            await waitFor(() => {
                expect(getItemSpy).toHaveBeenCalledWith('authToken');
            });

            getItemSpy.mockRestore();
        });
    });

    describe('Edge Cases', () => {
        test('Should handle empty string token gracefully', () => {
            localStorage.setItem('authToken', '');

            render(<HomePage />);

            // Empty string is falsy, should not redirect
            expect(mockPush).not.toHaveBeenCalled();
        });

        test('Should handle null token gracefully', () => {
            // Explicitly set to null
            localStorage.removeItem('authToken');

            render(<LoginPage />);

            // Should not redirect
            expect(mockPush).not.toHaveBeenCalled();
        });

        test('Both pages should have consistent navigation guard behavior', async () => {
            localStorage.setItem('authToken', 'valid-token');

            const { unmount: unmountHome } = render(<HomePage />);

            await waitFor(() => {
                expect(mockPush).toHaveBeenCalledWith('/cases');
            });

            mockPush.mockClear();
            unmountHome();

            render(<LoginPage />);

            await waitFor(() => {
                expect(mockPush).toHaveBeenCalledWith('/cases');
            });
        });
    });

    describe('Navigation Guard Consistency', () => {
        test('Landing page should check authToken on mount', async () => {
            const getItemSpy = jest.spyOn(Storage.prototype, 'getItem');
            localStorage.setItem('authToken', 'test-token');

            render(<HomePage />);

            await waitFor(() => {
                expect(getItemSpy).toHaveBeenCalledWith('authToken');
            });

            getItemSpy.mockRestore();
        });

        test('Redirect should happen before content flash', async () => {
            localStorage.setItem('authToken', 'test-token');

            render(<HomePage />);

            // Redirect should be initiated immediately in useEffect
            await waitFor(() => {
                expect(mockPush).toHaveBeenCalled();
            }, { timeout: 100 });
        });
    });
});
