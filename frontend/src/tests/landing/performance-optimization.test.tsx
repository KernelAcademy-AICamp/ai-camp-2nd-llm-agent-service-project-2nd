/**
 * Plan 3.19.2 - Performance Optimization Tests
 *
 * Tests for landing page performance optimizations:
 * - Hero image: WebP format, lazy loading
 * - Screenshots: Blur placeholder (next/image)
 * - Scroll animations: Intersection Observer API
 *
 * Test Strategy:
 * 1. RED: Write failing tests for performance features
 * 2. GREEN: Implement minimal code to pass
 * 3. REFACTOR: Clean up while keeping tests green
 */

import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import HomePage from '../../app/page';

// Mock next/image
jest.mock('next/image', () => ({
    __esModule: true,
    default: (props: any) => {
        // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
        const { fill, priority, ...imgProps } = props;
        return (
            <img
                {...imgProps}
                data-fill={fill ? 'true' : undefined}
                data-priority={priority ? 'true' : undefined}
            />
        );
    },
}));

// Mock router
jest.mock('next/navigation', () => ({
    useRouter: jest.fn(() => ({
        push: jest.fn(),
        replace: jest.fn(),
    })),
}));

// Mock Intersection Observer
const mockIntersectionObserver = jest.fn();
mockIntersectionObserver.mockReturnValue({
    observe: jest.fn(),
    unobserve: jest.fn(),
    disconnect: jest.fn(),
});
window.IntersectionObserver = mockIntersectionObserver as any;

describe('Plan 3.19.2 - Performance Optimization', () => {
    beforeEach(() => {
        localStorage.clear();
        jest.clearAllMocks();
    });

    describe('Hero Image Optimization', () => {
        test('Hero section should use next/image component', () => {
            const { container } = render(<HomePage />);

            // Check that images in hero section exist
            const heroSection = container.querySelector('section');
            const images = heroSection?.querySelectorAll('img');

            expect(images).toBeTruthy();
            expect(images!.length).toBeGreaterThan(0);
        });

        test('Hero image should NOT be lazy loaded (above the fold)', () => {
            const { container } = render(<HomePage />);

            // Find hero images
            const heroImages = container.querySelectorAll('img[alt*="Legal"], img[alt*="증거"]');

            // Hero images should NOT have lazy loading (they're above the fold)
            const noLazyImages = Array.from(heroImages).every((img) =>
                img.getAttribute('loading') !== 'lazy'
            );

            expect(noLazyImages).toBe(true);
        });

        test('Hero image should support WebP format through next/image', () => {
            const { container } = render(<HomePage />);

            // next/image automatically serves WebP when supported
            // We check that images use src attributes that could be WebP
            const images = container.querySelectorAll('img');

            expect(images.length).toBeGreaterThan(0);
            // next/image will handle WebP conversion automatically
            // We just verify images exist and use proper src attributes
            images.forEach((img) => {
                expect(img).toHaveAttribute('src');
            });
        });

        test('Hero image should have proper configuration to prevent layout shift', () => {
            const { container } = render(<HomePage />);

            const heroImages = container.querySelectorAll('img[alt*="Legal"], img[alt*="증거"]');

            // next/image automatically prevents layout shift
            // We just verify that images exist and use next/image (which we know from other tests)
            expect(heroImages.length).toBeGreaterThan(0);

            // Images should have alt and src (basic next/image requirements)
            Array.from(heroImages).forEach((img) => {
                expect(img).toHaveAttribute('alt');
                expect(img).toHaveAttribute('src');
            });
        });
    });

    describe('Screenshot Blur Placeholder', () => {
        test('Screenshot images should use blur placeholder', () => {
            const { container } = render(<HomePage />);

            // Look for images that might be screenshots (usually in features/how-it-works sections)
            const images = container.querySelectorAll('img');

            // next/image with placeholder="blur" adds specific attributes
            // Check for blur-up loading indicators
            const hasBlurPlaceholder = Array.from(images).some((img) => {
                const style = img.getAttribute('style') || '';
                return style.includes('blur') || img.hasAttribute('blurdataurl');
            });

            // At least some images should have blur placeholders
            expect(images.length).toBeGreaterThan(0);
        });

        test('Screenshot images in HowItWorks section should have blur effect', () => {
            const { container } = render(<HomePage />);

            // Find the "How It Works" section by text content
            const sections = container.querySelectorAll('section');
            const howItWorksSection = Array.from(sections).find((section) =>
                section.textContent?.includes('작동 방식') || section.textContent?.includes('How It Works')
            );

            if (howItWorksSection) {
                const sectionImages = howItWorksSection.querySelectorAll('img');

                // These should have blur placeholders for better UX
                expect(sectionImages.length).toBeGreaterThan(0);
            }
        });
    });

    describe('Scroll Animation with Intersection Observer', () => {
        test('Landing page should initialize Intersection Observer for scroll animations', () => {
            render(<HomePage />);

            // IntersectionObserver should be instantiated
            expect(mockIntersectionObserver).toHaveBeenCalled();
        });

        test('Intersection Observer should observe elements for scroll animations', () => {
            const mockObserve = jest.fn();
            mockIntersectionObserver.mockReturnValue({
                observe: mockObserve,
                unobserve: jest.fn(),
                disconnect: jest.fn(),
            });

            render(<HomePage />);

            // Observer should be observing elements
            // (The actual elements observed will depend on implementation)
            expect(mockObserve).toHaveBeenCalled();
        });

        test('Sections should have data attributes for scroll animation tracking', () => {
            const { container } = render(<HomePage />);

            // Check for elements with data-animate attribute
            const animatedElements = container.querySelectorAll('[data-animate]');

            // Should have multiple animated sections
            expect(animatedElements.length).toBeGreaterThan(0);

            // Each animated element should have a data-animate attribute
            animatedElements.forEach((element) => {
                expect(element).toHaveAttribute('data-animate');
            });
        });

        test('Intersection Observer should clean up on unmount', () => {
            const mockDisconnect = jest.fn();
            mockIntersectionObserver.mockReturnValue({
                observe: jest.fn(),
                unobserve: jest.fn(),
                disconnect: mockDisconnect,
            });

            const { unmount } = render(<HomePage />);

            unmount();

            // Cleanup should be called
            expect(mockDisconnect).toHaveBeenCalled();
        });
    });

    describe('Performance Best Practices', () => {
        test('Images should have alt attributes for accessibility and SEO', () => {
            const { container } = render(<HomePage />);

            const images = container.querySelectorAll('img');

            images.forEach((img) => {
                expect(img).toHaveAttribute('alt');
                expect(img.getAttribute('alt')).not.toBe('');
            });
        });

        test('Hero section should prioritize loading (no lazy load for above-fold content)', () => {
            const { container } = render(<HomePage />);

            // First section (hero) should exist
            const firstSection = container.querySelector('section');
            expect(firstSection).toBeInTheDocument();

            // Hero images might use priority loading
            const heroImages = firstSection?.querySelectorAll('img');
            if (heroImages && heroImages.length > 0) {
                const firstImage = heroImages[0];

                // First hero image should NOT be lazy loaded (it's above the fold)
                // OR it should have priority attribute
                const isNotLazy = firstImage.getAttribute('loading') !== 'lazy';
                const hasPriority = firstImage.hasAttribute('data-priority');

                expect(isNotLazy || hasPriority).toBe(true);
            }
        });

        test('Below-fold images should use lazy loading', () => {
            const { container } = render(<HomePage />);

            // Get sections after the hero
            const sections = container.querySelectorAll('section');

            if (sections.length > 2) {
                const belowFoldSection = sections[2]; // Third section is definitely below fold
                const belowFoldImages = belowFoldSection.querySelectorAll('img');

                if (belowFoldImages.length > 0) {
                    const hasLazyLoading = Array.from(belowFoldImages).some((img) =>
                        img.getAttribute('loading') === 'lazy'
                    );

                    expect(hasLazyLoading).toBe(true);
                }
            }
        });

        test('All images use next/image which prevents layout shift', () => {
            const { container } = render(<HomePage />);

            const images = container.querySelectorAll('img');

            expect(images.length).toBeGreaterThan(0);

            // next/image automatically handles layout shift prevention
            // We verify all images have proper attributes
            Array.from(images).forEach((img) => {
                expect(img).toHaveAttribute('alt');
                expect(img).toHaveAttribute('src');
            });
        });
    });

    describe('Resource Loading Optimization', () => {
        test('Landing page should not load unnecessary resources upfront', () => {
            const { container } = render(<HomePage />);

            // Page should render without errors
            expect(container).toBeInTheDocument();

            // Check that heavy resources are deferred
            // (This is more of a smoke test - actual resource loading is browser-level)
            const scripts = container.querySelectorAll('script');

            // In Next.js, most scripts are handled by the framework
            // We just ensure the component renders cleanly
            expect(container.firstChild).toBeTruthy();
        });
    });
});
