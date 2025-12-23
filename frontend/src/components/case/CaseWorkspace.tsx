'use client';

/**
 * CaseWorkspace - LDS2 2-Column Layout Container
 * Updated for LDS2 UI redesign
 *
 * 2-column layout for case detail page:
 * - Left Panel (256px): Data lists (evidence, consultation)
 * - Main Workspace (flex-1): Core work area (fact summary, draft generation)
 *
 * Left panel is collapsible for flexible workspace management.
 * Right Context panel removed - info now in CustomerInfo tab.
 */

import { useState, ReactNode } from 'react';
import { ChevronLeft, ChevronRight, PanelLeftClose, PanelLeft } from 'lucide-react';

interface CaseWorkspaceProps {
  leftPanel: ReactNode;
  mainContent: ReactNode;
  rightPanel?: ReactNode;  // Kept for backward compatibility but not rendered
  leftPanelTitle?: string;
  rightPanelTitle?: string;  // Kept for backward compatibility
  defaultLeftOpen?: boolean;
  defaultRightOpen?: boolean;  // Kept for backward compatibility
}

export function CaseWorkspace({
  leftPanel,
  mainContent,
  leftPanelTitle = '자료',
  defaultLeftOpen = true,
}: CaseWorkspaceProps) {
  const [leftOpen, setLeftOpen] = useState(defaultLeftOpen);

  return (
    <div className="flex h-full min-h-[500px]">
      {/* Left Panel - Data Lists (256px) */}
      <aside
        className={`
          relative flex-shrink-0 bg-white dark:bg-neutral-800
          border-r border-gray-200 dark:border-neutral-700
          transition-all duration-200 ease-out
          ${leftOpen ? 'w-64' : 'w-0'}
        `}
      >
        {leftOpen && (
          <div className="h-full flex flex-col w-64">
            {/* Panel Header - LDS2 Compact */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200 dark:border-neutral-700 bg-gray-50 dark:bg-neutral-900/50">
              <h3 className="text-xs font-semibold text-[var(--color-text-secondary)] uppercase tracking-wide">
                {leftPanelTitle}
              </h3>
              <button
                onClick={() => setLeftOpen(false)}
                className="p-1 rounded hover:bg-gray-200 dark:hover:bg-neutral-700 text-[var(--color-text-secondary)] transition-colors"
                aria-label="패널 접기"
              >
                <PanelLeftClose className="w-4 h-4" />
              </button>
            </div>
            {/* Panel Content */}
            <div className="flex-1 overflow-y-auto">
              {leftPanel}
            </div>
          </div>
        )}

        {/* Left Panel Toggle (when collapsed) */}
        {!leftOpen && (
          <button
            onClick={() => setLeftOpen(true)}
            className="absolute -right-10 top-3 flex items-center gap-1 px-2 py-1.5 bg-white dark:bg-neutral-800 border border-gray-200 dark:border-neutral-700 rounded-r-md shadow-sm hover:bg-gray-50 dark:hover:bg-neutral-700 text-[var(--color-text-secondary)] text-xs transition-colors"
            aria-label="패널 열기"
          >
            <PanelLeft className="w-4 h-4" />
            <span>자료</span>
          </button>
        )}
      </aside>

      {/* Main Workspace (flex-1, min-width 600px) */}
      <main className="flex-1 min-w-[600px] overflow-y-auto bg-gray-50 dark:bg-neutral-900/30">
        <div className="p-4">
          {mainContent}
        </div>
      </main>
    </div>
  );
}

export default CaseWorkspace;
