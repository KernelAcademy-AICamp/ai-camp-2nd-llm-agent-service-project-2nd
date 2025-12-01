import { forwardRef, ButtonHTMLAttributes, ReactNode } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export type IconButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive';
export type IconButtonSize = 'sm' | 'md' | 'lg';

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** The icon to display */
  icon: ReactNode;
  /** Visual variant */
  variant?: IconButtonVariant;
  /** Size of the button */
  size?: IconButtonSize;
  /** Accessible label (required for screen readers) */
  'aria-label': string;
}

const variantStyles: Record<IconButtonVariant, string> = {
  primary: 'bg-primary text-primary-contrast hover:bg-primary-hover active:bg-primary-active',
  secondary: 'bg-secondary text-secondary-contrast hover:bg-secondary-hover active:bg-secondary-active',
  ghost: 'bg-transparent text-neutral-600 hover:bg-neutral-100 active:bg-neutral-200',
  destructive: 'bg-error text-error-contrast hover:bg-error-hover active:bg-error-active',
};

const sizeStyles: Record<IconButtonSize, string> = {
  sm: 'w-9 h-9',
  md: 'w-11 h-11',
  lg: 'w-12 h-12',
};

/**
 * IconButton - Icon-only button component
 *
 * A button that displays only an icon. Requires an aria-label
 * for accessibility since there's no visible text.
 *
 * @example
 * ```tsx
 * <IconButton
 *   icon={<X className="w-5 h-5" />}
 *   aria-label="닫기"
 *   variant="ghost"
 *   onClick={handleClose}
 * />
 * ```
 */
export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  (
    {
      icon,
      variant = 'ghost',
      size = 'md',
      className,
      type = 'button',
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        type={type}
        disabled={disabled}
        className={twMerge(
          clsx(
            // Base styles
            'inline-flex items-center justify-center',
            'rounded-lg',
            'transition-colors duration-200',
            // Focus styles (WCAG 2.1 AA)
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2',
            // Disabled styles
            'disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none',
            // Variant and size
            variantStyles[variant],
            sizeStyles[size],
            className
          )
        )}
        {...props}
      >
        {icon}
      </button>
    );
  }
);

IconButton.displayName = 'IconButton';

export default IconButton;
