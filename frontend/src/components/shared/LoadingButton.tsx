/**
 * LoadingButton Component
 * 009-mvp-gap-closure Feature - T034
 *
 * Button with loading state indicator.
 * Shows spinner and disables interaction during API calls.
 * Implements FR-010 (버튼 로딩 상태)
 */

'use client';

import React, { forwardRef, ButtonHTMLAttributes } from 'react';
import { Spinner, SpinnerSize } from '@/components/primitives/Spinner/Spinner';

export interface LoadingButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Whether the button is in loading state */
  isLoading?: boolean;
  /** Text to show during loading (optional, shows spinner only if not provided) */
  loadingText?: string;
  /** Button variant */
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost';
  /** Button size */
  size?: 'sm' | 'md' | 'lg';
  /** Full width button */
  fullWidth?: boolean;
}

/**
 * Get variant-specific classes
 */
const getVariantClasses = (variant: LoadingButtonProps['variant'], isLoading: boolean): string => {
  const baseClasses = 'transition-colors duration-200 font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2';

  const variants = {
    primary: `${baseClasses} bg-primary text-white hover:bg-primary/90 focus:ring-primary disabled:bg-primary/60`,
    secondary: `${baseClasses} bg-neutral-200 text-neutral-900 hover:bg-neutral-300 focus:ring-neutral-500 disabled:bg-neutral-100 dark:bg-neutral-700 dark:text-neutral-100 dark:hover:bg-neutral-600`,
    danger: `${baseClasses} bg-error text-white hover:bg-error/90 focus:ring-error disabled:bg-error/60`,
    ghost: `${baseClasses} bg-transparent text-neutral-700 hover:bg-neutral-100 focus:ring-neutral-500 dark:text-neutral-300 dark:hover:bg-neutral-800`,
  };

  return variants[variant || 'primary'];
};

/**
 * Get size-specific classes
 */
const getSizeClasses = (size: LoadingButtonProps['size']): string => {
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return sizes[size || 'md'];
};

/**
 * Get spinner size based on button size
 */
const getSpinnerSize = (size: LoadingButtonProps['size']): SpinnerSize => {
  return size || 'md';
};

/**
 * LoadingButton component with loading state indicator
 *
 * @example
 * ```tsx
 * // Basic usage
 * <LoadingButton isLoading={isSubmitting} onClick={handleSubmit}>
 *   저장
 * </LoadingButton>
 *
 * // With loading text
 * <LoadingButton
 *   isLoading={isSubmitting}
 *   loadingText="저장 중..."
 *   onClick={handleSubmit}
 * >
 *   저장
 * </LoadingButton>
 *
 * // Different variants
 * <LoadingButton variant="danger" isLoading={isDeleting}>
 *   삭제
 * </LoadingButton>
 * ```
 */
export const LoadingButton = forwardRef<HTMLButtonElement, LoadingButtonProps>(
  (
    {
      children,
      isLoading = false,
      loadingText,
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      disabled,
      className = '',
      ...props
    },
    ref
  ) => {
    const variantClasses = getVariantClasses(variant, isLoading);
    const sizeClasses = getSizeClasses(size);
    const spinnerSize = getSpinnerSize(size);

    const buttonClasses = [
      variantClasses,
      sizeClasses,
      fullWidth ? 'w-full' : '',
      'inline-flex items-center justify-center gap-2',
      isLoading ? 'cursor-not-allowed' : '',
      className,
    ]
      .filter(Boolean)
      .join(' ');

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={buttonClasses}
        aria-busy={isLoading}
        aria-disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && <Spinner size={spinnerSize} />}
        <span className={isLoading && !loadingText ? 'sr-only' : ''}>
          {isLoading && loadingText ? loadingText : children}
        </span>
      </button>
    );
  }
);

LoadingButton.displayName = 'LoadingButton';

export default LoadingButton;
