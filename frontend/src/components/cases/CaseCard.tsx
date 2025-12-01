'use client';

import Link from 'next/link';
import { useState, useEffect, useRef } from 'react';
import { Case } from '@/types/case';
import { FileText, Clock, AlertCircle, CheckCircle2, ChevronDown } from 'lucide-react';

interface CaseCardProps {
  caseData: Case;
  onStatusChange?: (caseId: string, newStatus: 'open' | 'closed') => void;
}

export default function CaseCard({ caseData, onStatusChange }: CaseCardProps) {
  const [isStatusDropdownOpen, setIsStatusDropdownOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsStatusDropdownOpen(false);
      }
    }

    if (isStatusDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isStatusDropdownOpen]);

  const handleStatusChange = (e: React.MouseEvent, newStatus: 'open' | 'closed') => {
    e.preventDefault();
    e.stopPropagation();
    if (onStatusChange) {
      onStatusChange(caseData.id, newStatus);
    }
    setIsStatusDropdownOpen(false);
  };

  const toggleStatusDropdown = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsStatusDropdownOpen(!isStatusDropdownOpen);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsStatusDropdownOpen(false);
    }
  };

  return (
    <Link href={`/cases/${caseData.id}`}>
      <div className="relative card p-6 h-full flex flex-col justify-between group cursor-pointer bg-neutral-50 border border-neutral-200 rounded-lg overflow-hidden transition-all duration-300 hover:shadow-lg">
        {/* Border Beam Glow Effect - Magic UI Style */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
          <div className="absolute inset-[-2px] bg-gradient-to-r from-transparent via-primary to-transparent rounded-lg blur-sm animate-border-beam" />
        </div>

        {/* Content wrapper to ensure proper z-index layering */}
        <div className="relative z-10 flex flex-col h-full justify-between">
          <div>
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-xl font-bold text-secondary group-hover:text-primary transition-colors">
                  {caseData.title}
                </h3>
                <p className="text-sm text-neutral-500 mt-1">{caseData.clientName}</p>
              </div>

              {/* Status Dropdown */}
              <div className="relative" ref={dropdownRef}>
                <button
                  type="button"
                  onClick={toggleStatusDropdown}
                  onKeyDown={handleKeyDown}
                  aria-expanded={isStatusDropdownOpen}
                  aria-haspopup="listbox"
                  aria-label="상태 변경"
                  className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1
                    focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
                    transition-colors ${
                      caseData.status === 'open'
                        ? 'bg-primary-light text-primary'
                        : 'bg-neutral-100 text-neutral-700'
                    }`}
                >
                  <span>{caseData.status === 'open' ? '진행 중' : '종결'}</span>
                  <ChevronDown
                    className={`w-3 h-3 transition-transform ${
                      isStatusDropdownOpen ? 'rotate-180' : ''
                    }`}
                  />
                </button>

                {isStatusDropdownOpen && (
                  <div
                    role="listbox"
                    className="absolute right-0 mt-1 w-32 bg-white rounded-lg shadow-lg z-dropdown border border-neutral-200 overflow-hidden"
                  >
                    <button
                      type="button"
                      role="option"
                      aria-selected={caseData.status === 'open'}
                      onClick={(e) => handleStatusChange(e, 'open')}
                      className="block w-full text-left px-4 py-2 text-sm text-neutral-700
                        hover:bg-neutral-100 focus:bg-neutral-100 focus:outline-none"
                    >
                      진행 중
                    </button>
                    <button
                      type="button"
                      role="option"
                      aria-selected={caseData.status === 'closed'}
                      onClick={(e) => handleStatusChange(e, 'closed')}
                      className="block w-full text-left px-4 py-2 text-sm text-neutral-700
                        hover:bg-neutral-100 focus:bg-neutral-100 focus:outline-none"
                    >
                      종결
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center text-sm text-neutral-600">
                <FileText className="w-4 h-4 mr-2" aria-hidden="true" />
                <span>증거 {caseData.evidenceCount}건</span>
              </div>
              <div className="flex items-center text-sm text-neutral-600">
                <Clock className="w-4 h-4 mr-2" aria-hidden="true" />
                <span>
                  최근 업데이트:{' '}
                  {mounted
                    ? new Date(caseData.lastUpdated).toLocaleDateString('ko-KR')
                    : '로딩 중...'}
                </span>
              </div>
            </div>
          </div>

          {/* Draft Status */}
          <div className="mt-6 pt-4 border-t border-neutral-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-neutral-500">Draft 상태:</span>
              {caseData.draftStatus === 'ready' ? (
                <div className="flex items-center text-success text-sm font-bold">
                  <CheckCircle2 className="w-4 h-4 mr-1" aria-hidden="true" />
                  <span>준비됨</span>
                </div>
              ) : caseData.draftStatus === 'generating' ? (
                <div className="flex items-center text-primary text-sm font-bold animate-pulse">
                  <Clock className="w-4 h-4 mr-1" aria-hidden="true" />
                  <span>생성 중...</span>
                </div>
              ) : (
                <div className="flex items-center text-neutral-400 text-sm">
                  <AlertCircle className="w-4 h-4 mr-1" aria-hidden="true" />
                  <span>미생성</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Link>
  );
}
