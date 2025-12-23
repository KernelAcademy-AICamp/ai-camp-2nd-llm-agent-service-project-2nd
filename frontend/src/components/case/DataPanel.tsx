'use client';

/**
 * DataPanel - Left Panel Accordion Component
 * LDS2 Compact density applied
 *
 * Collapsible accordion lists for:
 * - Evidence (with legal numbering: 갑제1호증, 을제1호증)
 * - Consultation history
 * - Assets
 * - Similar precedents
 */

import { useState, ReactNode } from 'react';
import { ChevronDown, ChevronRight, FileText, Upload } from 'lucide-react';
import { PrecedentPopover } from '@/components/precedent/PrecedentPopover';

interface AccordionSection {
  id: string;
  title: string;
  icon: ReactNode;
  count?: number;
  content: ReactNode;
  action?: {
    label: string;
    icon: ReactNode;
    onClick: () => void;
  };
}

interface DataPanelProps {
  sections: AccordionSection[];
  defaultOpenSections?: string[];
}

export function DataPanel({ sections, defaultOpenSections = ['evidence'] }: DataPanelProps) {
  const [openSections, setOpenSections] = useState<Set<string>>(new Set(defaultOpenSections));

  const toggleSection = (sectionId: string) => {
    setOpenSections((prev) => {
      const next = new Set(prev);
      if (next.has(sectionId)) {
        next.delete(sectionId);
      } else {
        next.add(sectionId);
      }
      return next;
    });
  };

  return (
    <div className="divide-y divide-gray-100 dark:divide-neutral-700">
      {sections.map((section) => {
        const isOpen = openSections.has(section.id);

        return (
          <div key={section.id}>
            {/* Section Header - LDS2 Compact (32px height) */}
            <button
              onClick={() => toggleSection(section.id)}
              className="w-full flex items-center justify-between px-3 py-2 hover:bg-gray-50 dark:hover:bg-neutral-750 transition-colors duration-100"
            >
              <div className="flex items-center gap-1.5">
                <span className="text-[var(--color-text-secondary)]">
                  {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                </span>
                <span className="text-[var(--color-text-secondary)]">{section.icon}</span>
                <span className="text-xs font-medium text-[var(--color-text-primary)]">
                  {section.title}
                </span>
                {section.count !== undefined && section.count > 0 && (
                  <span className="px-1.5 py-0.5 text-[10px] bg-gray-100 dark:bg-neutral-700 text-[var(--color-text-secondary)] rounded">
                    {section.count}
                  </span>
                )}
              </div>
              {section.action && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    section.action?.onClick();
                  }}
                  className="p-1 rounded hover:bg-gray-200 dark:hover:bg-neutral-600 text-[var(--color-primary)] transition-colors"
                  aria-label={section.action.label}
                >
                  {section.action.icon}
                </button>
              )}
            </button>

            {/* Section Content - LDS2 Compact */}
            {isOpen && (
              <div className="px-3 pb-2">
                {section.content}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// Convenience wrapper for case detail page
interface CaseDataPanelProps {
  evidenceContent: ReactNode;
  evidenceCount: number;
  onUploadEvidence: () => void;
  consultationContent?: ReactNode;
  consultationCount?: number;
  onAddConsultation?: () => void;
  assetContent?: ReactNode;
  assetCount?: number;
  onAddAsset?: () => void;
  precedentContent?: ReactNode;
  precedentCount?: number;
}

export function CaseDataPanel({
  evidenceContent,
  evidenceCount,
  onUploadEvidence,
  consultationContent,
  consultationCount = 0,
  onAddConsultation,
  assetContent,
  assetCount = 0,
  onAddAsset,
  precedentContent,
  precedentCount = 0,
}: CaseDataPanelProps) {
  const sections: AccordionSection[] = [
    {
      id: 'evidence',
      title: '증거 목록',
      icon: <FileText className="w-4 h-4" />,
      count: evidenceCount,
      content: evidenceContent,
      action: {
        label: '증거 업로드',
        icon: <Upload className="w-4 h-4" />,
        onClick: onUploadEvidence,
      },
    },
    {
      id: 'consultation',
      title: '상담내역',
      icon: <FileText className="w-4 h-4" />,
      count: consultationCount,
      content: consultationContent || <div className="text-sm text-[var(--color-text-secondary)]">상담 내역이 없습니다.</div>,
      action: onAddConsultation ? {
        label: '상담 추가',
        icon: <Upload className="w-4 h-4" />,
        onClick: onAddConsultation,
      } : undefined,
    },
    {
      id: 'assets',
      title: '재산목록',
      icon: <FileText className="w-4 h-4" />,
      count: assetCount,
      content: assetContent || <div className="text-sm text-[var(--color-text-secondary)]">등록된 재산이 없습니다.</div>,
      action: onAddAsset ? {
        label: '재산 추가',
        icon: <Upload className="w-4 h-4" />,
        onClick: onAddAsset,
      } : undefined,
    },
    {
      id: 'precedent',
      title: '유사판례',
      icon: <FileText className="w-4 h-4" />,
      count: precedentCount,
      content: precedentContent || <PrecedentPopover />,
    },
  ];

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        <DataPanel sections={sections} defaultOpenSections={['evidence', 'consultation', 'assets', 'precedent']} />
      </div>
    </div>
  );
}

export default DataPanel;
