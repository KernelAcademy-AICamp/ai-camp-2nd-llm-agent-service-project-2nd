import { forwardRef, ButtonHTMLAttributes, ReactNode } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Spinner } from '../Spinner';

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive' | 'outline';
export type ButtonSize = 'sm' | 'md' | 'lg';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual variant of the button */
  variant?: ButtonVariant;
  /** Size of the button */
  size?: ButtonSize;
  /** Shows loading spinner and disables button */
  isLoading?: boolean;
  /** Loading text for screen readers (default: "로딩 중...") */
  loadingText?: string;
  /** Icon to display before children */
  leftIcon?: ReactNode;
  /** Icon to display after children */
  rightIcon?: ReactNode;
  /** Makes button full width */
  fullWidth?: boolean;
  /** Button content */
  children: ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: clsx(
    'bg-primary text-primary-contrast',
    'hover:bg-primary-hover active:bg-primary-active'
  ),
  secondary: clsx(
    'bg-secondary text-secondary-contrast',
    'hover:bg-secondary-hover active:bg-secondary-active'
  ),
  ghost: clsx(
    'bg-transparent text-neutral-700',
    'hover:bg-neutral-100 active:bg-neutral-200'
  ),
  destructive: clsx(
    'bg-error text-error-contrast',
    'hover:bg-error-hover active:bg-error-active'
  ),
  outline: clsx(
    'bg-transparent border-2 border-primary text-primary',
    'hover:bg-primary-light active:bg-primary-light'
  ),
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-9 px-3 text-sm gap-1.5',
  md: 'h-11 px-4 text-base gap-2',
  lg: 'h-12 px-6 text-lg gap-2.5',
};

/**
 * Button - Primary interactive element
 *
 * A fully accessible button component with multiple variants,
 * sizes, loading states, and icon support.
 *
 * Accessibility features:
 * - Defaults to type="button" to prevent accidental form submissions
 * - aria-busy indicates loading state to screen readers
 * - Minimum 44x44px touch target (WCAG 2.1 AA)
 * - Focus-visible ring for keyboard navigation
 *
 * @example
 * ```tsx
 * // Basic usage
 * <Button variant="primary" onClick={handleClick}>
 *   저장
 * </Button>
 *
 * // With loading state
 * <Button isLoading>저장 중...</Button>
 *
 * // With icons
 * <Button leftIcon={<Plus />}>새로 만들기</Button>
 *
 * // Full width
 * <Button fullWidth variant="primary">로그인</Button>
 * ```
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      isLoading = false,
      loadingText = '로딩 중...',
      leftIcon,
      rightIcon,
      fullWidth = false,
      disabled,
      className,
      children,
      type = 'button', // WCAG: Prevent accidental form submissions
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || isLoading;

    return (
      <button
        ref={ref}
        type={type}
        disabled={isDisabled}
        aria-busy={isLoading}
        aria-disabled={isDisabled}
        className={twMerge(
          clsx(
            // Base styles
            'inline-flex items-center justify-center',
            'font-semibold rounded-lg',
            'transition-colors duration-200',
            // Focus styles (WCAG 2.1 AA)
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
            // Disabled styles
            'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
            // Minimum touch target (WCAG 2.1 AA: 44x44px)
            'min-h-[44px] min-w-[44px]',
            // Variant and size
            variantStyles[variant],
            sizeStyles[size],
            // Full width
            fullWidth && 'w-full',
            className
          )
        )}
        {...props}
      >
        {isLoading ? (
          <>
            <Spinner
              size={size === 'sm' ? 'sm' : 'md'}
              className="flex-shrink-0"
              label={loadingText}
            />
            <span className="sr-only">{loadingText}</span>
            {/* Show children but visually indicate loading */}
            <span className="opacity-0 absolute">{children}</span>
          </>
        ) : (
          <>
            {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
          </>
        )}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;
