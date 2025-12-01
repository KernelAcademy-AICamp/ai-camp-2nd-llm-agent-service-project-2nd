'use client';

import { useEffect, useRef, useCallback, ReactNode, useId } from 'react';
import { createPortal } from 'react-dom';
import { X } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { IconButton } from '../IconButton';

export type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | 'full';

export interface ModalProps {
  /** Controls modal visibility */
  isOpen: boolean;
  /** Called when modal should close */
  onClose: () => void;
  /** Modal title (displayed in header) */
  title: string;
  /** Optional description below title */
  description?: string;
  /** Modal content */
  children: ReactNode;
  /** Optional footer content (typically action buttons) */
  footer?: ReactNode;
  /** Size variant */
  size?: ModalSize;
  /** Close when clicking backdrop (default: true) */
  closeOnOverlayClick?: boolean;
  /** Close when pressing Escape (default: true) */
  closeOnEscape?: boolean;
  /** Ref to element that should receive initial focus */
  initialFocusRef?: React.RefObject<HTMLElement>;
  /** Hide close button in header */
  hideCloseButton?: boolean;
}

const sizeStyles: Record<ModalSize, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-lg',
  xl: 'max-w-2xl',
  full: 'max-w-[90vw] max-h-[90vh]',
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

/**
 * Modal - Dialog overlay component
 *
 * A fully accessible modal dialog with focus trapping, keyboard navigation,
 * and proper ARIA attributes.
 *
 * Accessibility features:
 * - Focus trapped within modal when open
 * - Escape key closes modal
 * - Focus restored to trigger element on close
 * - Body scroll locked when open
 * - role="dialog" and aria-modal="true"
 * - aria-labelledby and aria-describedby
 *
 * @example
 * ```tsx
 * const [isOpen, setIsOpen] = useState(false);
 *
 * <Modal
 *   isOpen={isOpen}
 *   onClose={() => setIsOpen(false)}
 *   title="확인"
 *   description="이 작업을 수행하시겠습니까?"
 *   footer={
 *     <>
 *       <Button variant="ghost" onClick={() => setIsOpen(false)}>
 *         취소
 *       </Button>
 *       <Button onClick={handleConfirm}>확인</Button>
 *     </>
 *   }
 * >
 *   <p>모달 내용이 여기에 표시됩니다.</p>
 * </Modal>
 * ```
 */
export function Modal({
  isOpen,
  onClose,
  title,
  description,
  children,
  footer,
  size = 'md',
  closeOnOverlayClick = true,
  closeOnEscape = true,
  initialFocusRef,
  hideCloseButton = false,
}: ModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const previousActiveElement = useRef<HTMLElement | null>(null);

  // Generate unique IDs for ARIA attributes
  const titleId = useId();
  const descriptionId = useId();

  // Handle keyboard events (Escape and Tab for focus trap)
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!isOpen || !modalRef.current) return;

      // Close on Escape
      if (event.key === 'Escape' && closeOnEscape) {
        event.preventDefault();
        onClose();
        return;
      }

      // Focus trap
      if (event.key === 'Tab') {
        const focusableElements = getFocusableElements(modalRef.current);
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey) {
          // Shift + Tab: moving backward
          if (document.activeElement === firstElement) {
            event.preventDefault();
            lastElement.focus();
          }
        } else {
          // Tab: moving forward
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
      // Store the currently focused element
      previousActiveElement.current = document.activeElement as HTMLElement;

      // Add keyboard listener
      document.addEventListener('keydown', handleKeyDown);

      // Lock body scroll
      document.body.style.overflow = 'hidden';

      // Focus initial element after modal renders
      requestAnimationFrame(() => {
        if (initialFocusRef?.current) {
          initialFocusRef.current.focus();
        } else if (modalRef.current) {
          const focusableElements = getFocusableElements(modalRef.current);
          if (focusableElements.length > 0) {
            focusableElements[0].focus();
          } else {
            // If no focusable elements, focus the modal itself
            modalRef.current.focus();
          }
        }
      });
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';

      // Restore focus to previous element
      if (previousActiveElement.current && !isOpen) {
        previousActiveElement.current.focus();
      }
    };
  }, [isOpen, handleKeyDown, initialFocusRef]);

  // Don't render if not open or if we're on the server
  if (!isOpen || typeof document === 'undefined') return null;

  const modalContent = (
    <div
      className="fixed inset-0 z-modal flex items-center justify-center p-4"
      role="presentation"
    >
      {/* Backdrop/Overlay */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm animate-fade-in"
        onClick={closeOnOverlayClick ? onClose : undefined}
        aria-hidden="true"
      />

      {/* Modal Panel */}
      <div
        ref={modalRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={description ? descriptionId : undefined}
        tabIndex={-1}
        className={twMerge(
          clsx(
            'relative bg-white rounded-xl shadow-xl',
            'w-full max-h-[85vh] flex flex-col',
            'animate-scale-in',
            'focus:outline-none',
            sizeStyles[size]
          )
        )}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 p-6 border-b border-neutral-200">
          <div className="flex-1 min-w-0">
            <h2
              id={titleId}
              className="text-xl font-bold text-secondary truncate"
            >
              {title}
            </h2>
            {description && (
              <p
                id={descriptionId}
                className="mt-1 text-sm text-neutral-500"
              >
                {description}
              </p>
            )}
          </div>
          {!hideCloseButton && (
            <IconButton
              icon={<X className="w-5 h-5" />}
              onClick={onClose}
              aria-label="닫기"
              variant="ghost"
              size="sm"
              className="flex-shrink-0 -mr-2 -mt-1"
            />
          )}
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="flex justify-end gap-3 p-6 border-t border-neutral-200 bg-neutral-50 rounded-b-xl">
            {footer}
          </div>
        )}
      </div>
    </div>
  );

  // Render in portal
  return createPortal(modalContent, document.body);
}

export default Modal;
