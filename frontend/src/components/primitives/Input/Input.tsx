import { forwardRef, InputHTMLAttributes, ReactNode, useId } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'> {
  /** Label text displayed above the input */
  label?: string;
  /** Error message (also sets aria-invalid) */
  error?: string;
  /** Hint text displayed below the input */
  hint?: string;
  /** Icon to display at the start of the input */
  leftIcon?: ReactNode;
  /** Icon to display at the end of the input */
  rightIcon?: ReactNode;
  /** Makes input full width (default: true) */
  fullWidth?: boolean;
  /** Size variant */
  inputSize?: 'sm' | 'md' | 'lg';
}

const sizeStyles = {
  sm: 'h-9 px-3 text-sm',
  md: 'h-11 px-3 text-base',
  lg: 'h-12 px-4 text-lg',
};

/**
 * Input - Text input component
 *
 * A fully accessible input component with label, error states,
 * hints, and icon support.
 *
 * Accessibility features:
 * - Auto-generated unique IDs for label-input association
 * - aria-invalid when error is present
 * - aria-describedby linking to error and hint messages
 * - Required field indicator (visual and programmatic)
 * - Minimum 44px height touch target (WCAG 2.1 AA)
 *
 * @example
 * ```tsx
 * // Basic usage
 * <Input label="이메일" type="email" placeholder="email@example.com" />
 *
 * // With error
 * <Input
 *   label="비밀번호"
 *   type="password"
 *   error="비밀번호는 8자 이상이어야 합니다"
 * />
 *
 * // With hint
 * <Input
 *   label="사용자명"
 *   hint="영문, 숫자, 밑줄만 사용할 수 있습니다"
 * />
 *
 * // With icons
 * <Input
 *   label="검색"
 *   leftIcon={<Search className="w-5 h-5" />}
 *   placeholder="검색어를 입력하세요"
 * />
 * ```
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      hint,
      leftIcon,
      rightIcon,
      fullWidth = true,
      inputSize = 'md',
      className,
      id: providedId,
      disabled,
      required,
      ...props
    },
    ref
  ) => {
    // Generate unique IDs for accessibility
    const generatedId = useId();
    const inputId = providedId || `input-${generatedId}`;
    const errorId = error ? `${inputId}-error` : undefined;
    const hintId = hint && !error ? `${inputId}-hint` : undefined;
    const describedBy = [errorId, hintId].filter(Boolean).join(' ') || undefined;

    return (
      <div className={clsx(fullWidth && 'w-full')}>
        {/* Label */}
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-neutral-700 mb-1.5"
          >
            {label}
            {required && (
              <span className="text-error ml-0.5" aria-hidden="true">
                *
              </span>
            )}
            {required && <span className="sr-only">(필수)</span>}
          </label>
        )}

        {/* Input wrapper */}
        <div className="relative">
          {/* Left icon */}
          {leftIcon && (
            <span
              className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none"
              aria-hidden="true"
            >
              {leftIcon}
            </span>
          )}

          {/* Input element */}
          <input
            ref={ref}
            id={inputId}
            disabled={disabled}
            required={required}
            aria-invalid={!!error}
            aria-describedby={describedBy}
            className={twMerge(
              clsx(
                // Base styles
                'block rounded-lg border bg-white text-neutral-900',
                'transition-colors duration-200',
                'placeholder:text-neutral-400',
                // Size
                sizeStyles[inputSize],
                // Width
                fullWidth && 'w-full',
                // Padding for icons
                leftIcon && 'pl-10',
                rightIcon && 'pr-10',
                // Focus styles (WCAG 2.1 AA)
                'focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary',
                // Error state
                error
                  ? 'border-error focus:ring-error focus:border-error'
                  : 'border-neutral-300 hover:border-neutral-400',
                // Disabled state
                disabled && 'bg-neutral-100 cursor-not-allowed opacity-50',
                className
              )
            )}
            {...props}
          />

          {/* Right icon */}
          {rightIcon && (
            <span
              className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 pointer-events-none"
              aria-hidden="true"
            >
              {rightIcon}
            </span>
          )}
        </div>

        {/* Error message */}
        {error && (
          <p
            id={errorId}
            className="mt-1.5 text-sm text-error flex items-center gap-1"
            role="alert"
          >
            <svg
              className="w-4 h-4 flex-shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            {error}
          </p>
        )}

        {/* Hint text */}
        {hint && !error && (
          <p id={hintId} className="mt-1.5 text-sm text-neutral-500">
            {hint}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
