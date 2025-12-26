/**
 * EmptyState Component (T071)
 *
 * Displays helpful guidance when no data exists.
 * Provides actionable next steps for users.
 *
 * Features:
 * - Customizable icon, title, and description
 * - Primary and secondary action buttons
 * - Accessible with proper semantics
 * - Multiple size variants
 */

'use client';

import { ReactNode } from 'react';
import { Inbox, FileText, FolderOpen, Search, Plus, Calendar, MessageSquare, Receipt, ShieldAlert } from 'lucide-react';
import { Button } from '@/components/primitives';

interface EmptyStateAction {
  /**
   * Button label
   */
  label: string;
  /**
   * Click handler
   */
  onClick: () => void;
  /**
   * Button variant
   */
  variant?: 'primary' | 'secondary' | 'ghost';
  /**
   * Button icon
   */
  icon?: ReactNode;
}

interface EmptyStateProps {
  /**
   * Icon to display (use preset or custom)
   */
  icon?: 'inbox' | 'file' | 'folder' | 'search' | 'custom';
  /**
   * Custom icon component
   */
  customIcon?: ReactNode;
  /**
   * Title text
   */
  title: string;
  /**
   * Description text
   */
  description?: string;
  /**
   * Primary action button
   */
  primaryAction?: EmptyStateAction;
  /**
   * Secondary action button
   */
  secondaryAction?: EmptyStateAction;
  /**
   * Size variant
   */
  size?: 'sm' | 'md' | 'lg';
  /**
   * Additional classes
   */
  className?: string;
  /**
   * Children for custom content
   */
  children?: ReactNode;
}

const iconComponents: Record<string, typeof Inbox> = {
  inbox: Inbox,
  file: FileText,
  folder: FolderOpen,
  search: Search,
};

export function EmptyState({
  icon = 'inbox',
  customIcon,
  title,
  description,
  primaryAction,
  secondaryAction,
  size = 'md',
  className = '',
  children,
}: EmptyStateProps) {
  const sizeStyles: Record<string, { container: string; icon: string; title: string; description: string }> = {
    sm: {
      container: 'py-8 px-4',
      icon: 'w-10 h-10',
      title: 'text-base',
      description: 'text-sm',
    },
    md: {
      container: 'py-12 px-6',
      icon: 'w-14 h-14',
      title: 'text-lg',
      description: 'text-base',
    },
    lg: {
      container: 'py-16 px-8',
      icon: 'w-20 h-20',
      title: 'text-xl',
      description: 'text-base',
    },
  };

  const styles = sizeStyles[size];
  const IconComponent = icon !== 'custom' ? iconComponents[icon] : null;

  return (
    <div
      role="status"
      aria-label={title}
      className={`
        flex flex-col items-center justify-center text-center
        animate-fade-in
        ${styles.container}
        ${className}
      `}
    >
      {/* Icon */}
      <div className={`
        mb-4 p-4 rounded-full transition-all duration-500
        bg-neutral-100 dark:bg-neutral-800/80
        dark:backdrop-blur-sm dark:border dark:border-white/10
        hover:scale-110 hover:shadow-lg
      `}>
        {customIcon || (IconComponent && (
          <IconComponent
            className={`${styles.icon} text-neutral-400 dark:text-neutral-500`}
            aria-hidden="true"
          />
        ))}
      </div>

      {/* Title */}
      <h3 className={`${styles.title} font-semibold text-neutral-900 dark:text-neutral-100 mb-2 animate-slide-up`}>
        {title}
      </h3>

      {/* Description */}
      {description && (
        <p className={`${styles.description} text-neutral-500 dark:text-neutral-400 max-w-md mb-6`}>
          {description}
        </p>
      )}

      {/* Custom Children */}
      {children && <div className="mb-6">{children}</div>}

      {/* Actions */}
      {(primaryAction || secondaryAction) && (
        <div className="flex flex-col sm:flex-row gap-3">
          {primaryAction && (
            <Button
              variant={primaryAction.variant || 'primary'}
              onClick={primaryAction.onClick}
            >
              {primaryAction.icon || <Plus className="w-4 h-4 mr-2" />}
              {primaryAction.label}
            </Button>
          )}
          {secondaryAction && (
            <Button
              variant={secondaryAction.variant || 'ghost'}
              onClick={secondaryAction.onClick}
            >
              {secondaryAction.icon}
              {secondaryAction.label}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * ErrorState Component (T072)
 *
 * Displays error message with retry option.
 */
interface ErrorStateProps {
  /**
   * Error title
   */
  title?: string;
  /**
   * Error message
   */
  message?: string;
  /**
   * Retry action
   */
  onRetry?: () => void;
  /**
   * Retry button text
   */
  retryText?: string;
  /**
   * Size variant
   */
  size?: 'sm' | 'md' | 'lg';
  /**
   * Additional classes
   */
  className?: string;
}

export function ErrorState({
  title = '오류가 발생했습니다',
  message = '데이터를 불러오는 중 문제가 발생했습니다.',
  onRetry,
  retryText = '다시 시도',
  size = 'md',
  className = '',
}: ErrorStateProps) {
  const sizeStyles: Record<string, { container: string; icon: string; title: string }> = {
    sm: { container: 'py-6 px-4', icon: 'w-8 h-8', title: 'text-base' },
    md: { container: 'py-10 px-6', icon: 'w-12 h-12', title: 'text-lg' },
    lg: { container: 'py-14 px-8', icon: 'w-16 h-16', title: 'text-xl' },
  };

  const styles = sizeStyles[size];

  return (
    <div
      role="alert"
      className={`
        flex flex-col items-center justify-center text-center
        ${styles.container}
        ${className}
      `}
    >
      {/* Error Icon */}
      <div className="mb-4 p-3 bg-error-light rounded-full">
        <svg
          className={`${styles.icon} text-error`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
      </div>

      {/* Title */}
      <h3 className={`${styles.title} font-semibold text-error mb-2`}>
        {title}
      </h3>

      {/* Message */}
      <p className="text-sm text-neutral-500 dark:text-neutral-400 max-w-md mb-4">
        {message}
      </p>

      {/* Retry Button */}
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          <svg
            className="w-4 h-4 mr-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          {retryText}
        </Button>
      )}
    </div>
  );
}

// ============================================
// Specialized Empty States
// ============================================

export function EmptyCases({ onCreateCase }: { onCreateCase?: () => void }) {
  return (
    <EmptyState
      icon="folder"
      title="케이스가 없습니다"
      description="새로운 케이스를 생성하여 증거 관리를 시작하세요."
      primaryAction={onCreateCase ? {
        label: '새 케이스 만들기',
        onClick: onCreateCase,
        icon: <Plus className="w-4 h-4 mr-2" />
      } : undefined}
    />
  );
}

export function EmptyEvidence({ onUploadEvidence }: { onUploadEvidence?: () => void }) {
  return (
    <EmptyState
      icon="file"
      title="증거가 없습니다"
      description="증거 파일을 업로드하여 AI 분석을 시작하세요."
      primaryAction={onUploadEvidence ? {
        label: '증거 업로드',
        onClick: onUploadEvidence,
        icon: <Plus className="w-4 h-4 mr-2" />
      } : undefined}
    />
  );
}

export function EmptyCalendar({ onCreateEvent }: { onCreateEvent?: () => void }) {
  return (
    <EmptyState
      customIcon={<Calendar className="w-14 h-14 text-neutral-400" />}
      icon="custom"
      title="일정이 없습니다"
      description="새로운 일정을 등록하여 케이스 관련 이벤트를 관리하세요."
      primaryAction={onCreateEvent ? {
        label: '일정 추가',
        onClick: onCreateEvent,
        icon: <Plus className="w-4 h-4 mr-2" />
      } : undefined}
    />
  );
}

export function EmptyMessages({ onStartConversation }: { onStartConversation?: () => void }) {
  return (
    <EmptyState
      customIcon={<MessageSquare className="w-14 h-14 text-neutral-400" />}
      icon="custom"
      title="메시지가 없습니다"
      description="아직 주고받은 메시지가 없습니다."
      primaryAction={onStartConversation ? {
        label: '대화 시작',
        onClick: onStartConversation,
        icon: <Plus className="w-4 h-4 mr-2" />
      } : undefined}
    />
  );
}

export function EmptyInvoices({ onCreateInvoice }: { onCreateInvoice?: () => void }) {
  return (
    <EmptyState
      customIcon={<Receipt className="w-14 h-14 text-neutral-400" />}
      icon="custom"
      title="청구서가 없습니다"
      description="새로운 청구서를 생성하여 결제를 요청하세요."
      primaryAction={onCreateInvoice ? {
        label: '청구서 생성',
        onClick: onCreateInvoice,
        icon: <Plus className="w-4 h-4 mr-2" />
      } : undefined}
    />
  );
}

export function EmptyInvestigations({ onViewAvailable }: { onViewAvailable?: () => void }) {
  return (
    <EmptyState
      icon="search"
      title="진행 중인 조사가 없습니다"
      description="새로운 조사 의뢰를 수락하여 업무를 시작하세요."
      primaryAction={onViewAvailable ? {
        label: '의뢰 목록 보기',
        onClick: onViewAvailable,
        icon: <Plus className="w-4 h-4 mr-2" />
      } : undefined}
    />
  );
}

export function EmptyNotifications() {
  return (
    <EmptyState
      icon="inbox"
      title="알림이 없습니다"
      description="새로운 알림이 없습니다."
    />
  );
}

export function EmptySearchResults({ searchTerm, onClearSearch }: { searchTerm: string; onClearSearch?: () => void }) {
  return (
    <EmptyState
      icon="search"
      title="검색 결과가 없습니다"
      description={`"${searchTerm}"에 대한 검색 결과가 없습니다. 다른 검색어를 시도해 보세요.`}
      primaryAction={onClearSearch ? {
        label: '검색 초기화',
        onClick: onClearSearch,
        icon: <Plus className="w-4 h-4 mr-2" />
      } : undefined}
    />
  );
}

export function EmptyList({ itemType }: { itemType: string }) {
  return (
    <EmptyState
      icon="inbox"
      title={`${itemType}(이)가 없습니다`}
      description={`표시할 ${itemType}(이)가 없습니다.`}
    />
  );
}

export default EmptyState;
