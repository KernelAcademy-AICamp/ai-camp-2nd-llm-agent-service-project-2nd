'use client';

/**
 * Drawer - LDS2 Side Panel Component
 *
 * LDS2 원칙: "패널은 모달보다 선호된다. 모달은 즉각적 주의가 필요한 중요 작업에만 사용"
 *
 * 사용 케이스:
 * - 보조 정보 표시 (인물 상세, 증거 상세)
 * - 컨텍스트 유지가 필요한 작업
 * - 긴 폼 입력
 */

import { useEffect, useRef, useCallback, ReactNode, useId } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { IconButton } from '../IconButton';

export type DrawerPosition = 'left' | 'right';
export type DrawerSize = 'sm' | 'md' | 'lg';

export interface DrawerProps {
  /** Controls drawer visibility */
  isOpen: boolean;
  /** Called when drawer should close */
  onClose: () => void;
  /** Drawer title (displayed in header) */
  title: string;
  /** Optional description below title */
  description?: string;
  /** Drawer content */
  children: ReactNode;
  /** Optional footer content */
  footer?: ReactNode;
  /** Position on screen */
  position?: DrawerPosition;
  /** Size variant */
  size?: DrawerSize;
  /** Close when clicking backdrop (default: true) */
  closeOnOverlayClick?: boolean;
  /** Close when pressing Escape (default: true) */
  closeOnEscape?: boolean;
  /** Hide close button in header */
  hideCloseButton?: boolean;
}

// LDS2 Drawer Size Standards
const sizeStyles: Record<DrawerSize, string> = {
  sm: 'w-80',    // 320px
  md: 'w-[400px]', // 400px
  lg: 'w-[560px]', // 560px
};

const positionStyles: Record<DrawerPosition, { base: string; open: string; closed: string }> = {
  right: {
    base: 'right-0',
    open: 'translate-x-0',
    closed: 'translate-x-full',
  },
  left: {
    base: 'left-0',
    open: 'translate-x-0',
    closed: '-translate-x-full',
  },
};

/**
 * Get all focusable elements within a container
 */
function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const focusableSelectors = [
    'button:not([disabled])',
    '[href]',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    '[tabindex]:not([tabindex="-1"])',
  ].join(', ');

  return Array.from(container.querySelectorAll<HTMLElement>(focusableSelectors));
}

export function Drawer({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  position = 'right',
  size = 'md',
  closeOnOverlayClick = true,
  closeOnEscape = true,
  hideCloseButton = false,
}: DrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Generate unique IDs for ARIA attributes
  const titleId = useId();
  const descriptionId = useId();

  // Handle keyboard events
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!isOpen || !drawerRef.current) return;

      // Skip if IME composition is in progress
      if (event.isComposing || event.keyCode === 229) return;

      // Close on Escape
      if (event.key === 'Escape' && closeOnEscape) {
        event.preventDefault();
        onClose();
        return;
      }

      // Focus trap
      if (event.key === 'Tab') {
        const focusableElements = getFocusableElements(drawerRef.current);
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey) {
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            event.preventDefault();
            firstElement.focus();
          }
        }
      }
    },
    [isOpen, closeOnEscape, onClose]
  );

  // Setup/cleanup effects
  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement as HTMLElement;
      document.addEventListener('keydown', handleKeyDown);

      // Focus first focusable element
      requestAnimationFrame(() => {
        if (drawerRef.current) {
          const focusableElements = getFocusableElements(drawerRef.current);
          if (focusableElements.length > 0) {
            focusableElements[0].focus();
          } else {
            drawerRef.current.focus();
          }
        }
      });
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      if (previousActiveElement.current && !isOpen) {
        previousActiveElement.current.focus();
      }
    };
  }, [isOpen, handleKeyDown]);

  // Don't render if not open or if we're on the server
  if (typeof document === 'undefined') return null;

  const posStyles = positionStyles[position];

  const drawerContent = (
    <div
      className="fixed inset-0"
      role="presentation"
      style={{ zIndex: 9998, isolation: 'isolate' }}
    >
      {/* Backdrop - Semi-transparent (non-modal feel) */}
      <div
        className={twMerge(
          'fixed inset-0 bg-black/20 transition-opacity duration-200',
          isOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'
        )}
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          if (closeOnOverlayClick) onClose();
        }}
        aria-hidden="true"
        style={{ zIndex: 9998 }}
      />

      {/* Drawer Panel - LDS2 Compact */}
      <aside
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
        style={{ zIndex: 9999 }}
        className={twMerge(
          clsx(
            'fixed top-0 h-full bg-white dark:bg-neutral-800 shadow-xl',
            'flex flex-col',
            'transform transition-transform duration-200 ease-out',
            'focus:outline-none',
            sizeStyles[size],
            posStyles.base,
            isOpen ? posStyles.open : posStyles.closed
          )
        )}
      >
        {/* Header - LDS2 Compact (h-12 = 48px) */}
        <div className="flex items-center justify-between gap-3 h-12 px-4 border-b border-neutral-200 dark:border-neutral-700 flex-shrink-0">
          <div className="flex-1 min-w-0">
            <h3
              id={titleId}
              className="text-sm font-semibold text-[var(--color-text-primary)] truncate"
            >
              {title}
            </h3>
            {description && (
              <p
                id={descriptionId}
                className="text-xs text-[var(--color-text-secondary)] truncate"
              >
                {description}
              </p>
            )}
          </div>
          {!hideCloseButton && (
            <IconButton
              icon={<X className="w-4 h-4" />}
              onClick={onClose}
              aria-label="닫기"
              variant="ghost"
              size="sm"
              className="flex-shrink-0"
            />
          )}
        </div>

        {/* Body - LDS2 Compact */}
        <div className="flex-1 overflow-y-auto p-4">
          {children}
        </div>

        {/* Footer - LDS2 Compact (h-14 = 56px) */}
        {footer && (
          <div className="flex items-center justify-end gap-2 h-14 px-4 border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 flex-shrink-0">
            {footer}
          </div>
        )}
      </aside>
    </div>
  );

  // Render in portal
  return createPortal(drawerContent, document.body);
}

export default Drawer;
