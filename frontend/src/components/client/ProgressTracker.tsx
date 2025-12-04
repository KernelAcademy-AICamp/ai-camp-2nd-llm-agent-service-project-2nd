/**
 * ProgressTracker Component
 * 003-role-based-ui Feature - US4 (T072)
 *
 * Visual progress tracker showing case progress steps.
 * Displays completed, current, and pending steps.
 */

'use client';

import type { ProgressStep } from '@/types/client-portal';

interface ProgressTrackerProps {
  steps: ProgressStep[];
  className?: string;
  orientation?: 'vertical' | 'horizontal';
}

// Individual step component
function Step({
  step,
  title,
  status,
  date,
  isLast,
  orientation,
}: ProgressStep & { isLast: boolean; orientation: 'vertical' | 'horizontal' }) {
  const statusStyles = {
    completed: {
      circle: 'bg-[var(--color-success)] text-white',
      line: 'bg-[var(--color-success)]',
      text: 'text-[var(--color-text-primary)]',
    },
    current: {
      circle:
        'bg-[var(--color-primary)] text-white ring-4 ring-[var(--color-primary-light)]',
      line: 'bg-[var(--color-neutral-200)]',
      text: 'text-[var(--color-primary)] font-semibold',
    },
    pending: {
      circle: 'bg-[var(--color-neutral-200)] text-[var(--color-text-tertiary)]',
      line: 'bg-[var(--color-neutral-200)]',
      text: 'text-[var(--color-text-tertiary)]',
    },
  };

  const styles = statusStyles[status];

  if (orientation === 'horizontal') {
    return (
      <div className="flex flex-col items-center flex-1">
        <div className="flex items-center w-full">
          {/* Circle */}
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold text-sm flex-shrink-0 ${styles.circle}`}
          >
            {status === 'completed' ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            ) : (
              step
            )}
          </div>
          {/* Line */}
          {!isLast && <div className={`flex-1 h-1 mx-2 ${styles.line}`} />}
        </div>
        {/* Text below */}
        <div className="mt-3 text-center">
          <p className={`text-sm ${styles.text}`}>{title}</p>
          {date && (
            <p className="text-xs text-[var(--color-text-secondary)] mt-1">{date}</p>
          )}
        </div>
      </div>
    );
  }

  // Vertical orientation
  return (
    <div className="flex items-start gap-4">
      <div className="flex flex-col items-center">
        {/* Circle */}
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${styles.circle}`}
        >
          {status === 'completed' ? (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          ) : (
            step
          )}
        </div>
        {/* Line */}
        {!isLast && <div className={`w-0.5 h-12 ${styles.line}`} />}
      </div>
      <div className={`flex-1 ${isLast ? '' : 'pb-8'}`}>
        <p className={`${styles.text}`}>{title}</p>
        {date && (
          <p className="text-sm text-[var(--color-text-secondary)] mt-1">{date}</p>
        )}
      </div>
    </div>
  );
}

export default function ProgressTracker({
  steps,
  className = '',
  orientation = 'vertical',
}: ProgressTrackerProps) {
  if (steps.length === 0) {
    return (
      <div className="text-center py-8 text-[var(--color-text-secondary)]">
        진행 단계 정보가 없습니다
      </div>
    );
  }

  // Calculate progress percentage based on completed steps
  const completedSteps = steps.filter((s) => s.status === 'completed').length;
  const currentStep = steps.findIndex((s) => s.status === 'current');
  const progressPercent = Math.round(
    ((completedSteps + (currentStep >= 0 ? 0.5 : 0)) / steps.length) * 100
  );

  return (
    <div className={className}>
      {/* Progress bar summary */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-[var(--color-text-secondary)]">전체 진행률</span>
          <span className="text-sm font-semibold text-[var(--color-primary)]">
            {progressPercent}%
          </span>
        </div>
        <div className="h-2 bg-[var(--color-neutral-200)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--color-primary)] rounded-full transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div
        className={
          orientation === 'horizontal' ? 'flex items-start' : 'flex flex-col'
        }
      >
        {steps.map((step, index) => (
          <Step
            key={step.step}
            {...step}
            isLast={index === steps.length - 1}
            orientation={orientation}
          />
        ))}
      </div>
    </div>
  );
}

// Export smaller variant for cards/summaries
export function ProgressBar({
  percent,
  className = '',
  showLabel = true,
}: {
  percent: number;
  className?: string;
  showLabel?: boolean;
}) {
  const clampedPercent = Math.max(0, Math.min(100, percent));

  return (
    <div className={className}>
      {showLabel && (
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-[var(--color-text-secondary)]">진행률</span>
          <span className="text-xs font-medium text-[var(--color-primary)]">
            {clampedPercent}%
          </span>
        </div>
      )}
      <div className="h-1.5 bg-[var(--color-neutral-200)] rounded-full overflow-hidden">
        <div
          className="h-full bg-[var(--color-primary)] rounded-full transition-all duration-300"
          style={{ width: `${clampedPercent}%` }}
        />
      </div>
    </div>
  );
}
