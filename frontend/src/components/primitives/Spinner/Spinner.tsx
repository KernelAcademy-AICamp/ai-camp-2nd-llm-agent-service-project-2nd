import { clsx } from 'clsx';

export type SpinnerSize = 'sm' | 'md' | 'lg';

export interface SpinnerProps {
  /** Size of the spinner */
  size?: SpinnerSize;
  /** Additional CSS classes */
  className?: string;
  /** Label for screen readers (default: "로딩 중...") */
  label?: string;
}

const sizeStyles: Record<SpinnerSize, string> = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
};

/**
 * Spinner - Loading indicator component
 *
 * A simple animated spinner for indicating loading states.
 * Hidden from screen readers by default with aria-hidden.
 *
 * @example
 * ```tsx
 * <Spinner size="md" />
 * <Spinner size="lg" className="text-primary" />
 * ```
 */
export function Spinner({ size = 'md', className, label = '로딩 중...' }: SpinnerProps) {
  return (
    <div role="status" aria-label={label}>
      <svg
        className={clsx('animate-spin', sizeStyles[size], className)}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      <span className="sr-only">{label}</span>
    </div>
  );
}

export default Spinner;
