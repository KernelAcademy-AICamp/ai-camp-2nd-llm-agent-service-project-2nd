/**
 * LEH Design System - Primitive Components
 *
 * Core UI building blocks following atomic design principles.
 * All components are fully accessible (WCAG 2.1 AA compliant).
 *
 * @example
 * ```tsx
 * import { Button, Input, Modal, Spinner, IconButton } from '@/components/primitives';
 *
 * <Button variant="primary" isLoading={loading}>
 *   저장
 * </Button>
 * ```
 */

// Button
export { Button, type ButtonProps, type ButtonVariant, type ButtonSize } from './Button';

// Input
export { Input, type InputProps } from './Input';

// Modal
export { Modal, type ModalProps, type ModalSize } from './Modal';

// IconButton
export { IconButton, type IconButtonProps, type IconButtonVariant, type IconButtonSize } from './IconButton';

// Spinner
export { Spinner, type SpinnerProps, type SpinnerSize } from './Spinner';
