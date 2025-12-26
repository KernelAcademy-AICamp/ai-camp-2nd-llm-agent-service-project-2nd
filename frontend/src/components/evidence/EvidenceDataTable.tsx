/**
 * Evidence DataTable Component
 * Shadcn/ui style with TanStack Table integration
 *
 * Responsibilities:
 * - Render table structure
 * - Display evidence data with sorting
 * - Integrate with useEvidenceTable hook for logic
 */

import { useState } from 'react';
import toast from 'react-hot-toast';
import { logger } from '@/lib/logger';
import { flexRender } from '@tanstack/react-table';
import { ArrowUpDown, MoreVertical, Filter, RefreshCw } from 'lucide-react';
import { Evidence } from '@/types/evidence';
import type { PartyNode } from '@/types/party';
import { useEvidenceTable } from '@/hooks/useEvidenceTable';
import { EvidenceTypeIcon } from './EvidenceTypeIcon';
import { EvidenceStatusBadge } from './EvidenceStatusBadge';
import { SpeakerMappingBadge } from './SpeakerMappingBadge';
import { SpeakerMappingModal } from './SpeakerMappingModal';
import { AISummaryModal } from './AISummaryModal';
import { ContentModal } from './ContentModal';
import { DataTablePagination } from './DataTablePagination';
import { getEvidenceDetail, retryEvidence, updateSpeakerMapping } from '@/lib/api/evidence';
import type { SpeakerMapping } from '@/lib/api/evidence';

interface EvidenceDataTableProps {
  items: Evidence[];
  onRetry?: (evidenceId: string) => void;
  /** 015-evidence-speaker-mapping: 인물관계도의 당사자 목록 */
  parties?: PartyNode[];
  /** 015-evidence-speaker-mapping: 화자 매핑 저장 후 콜백 */
  onSpeakerMappingUpdate?: (evidenceId: string) => void;
}

export function EvidenceDataTable({ items, onRetry, parties = [], onSpeakerMappingUpdate }: EvidenceDataTableProps) {
  const [typeFilter, setTypeFilterValue] = useState<string>('all');
  const [dateFilter, setDateFilterValue] = useState<string>('all');
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(null);
  const [isSummaryModalOpen, setIsSummaryModalOpen] = useState(false);
  const [isContentModalOpen, setIsContentModalOpen] = useState(false);
  const [evidenceContent, setEvidenceContent] = useState<string | null>(null);
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const [retryingIds, setRetryingIds] = useState<Set<string>>(new Set());

  // 015-evidence-speaker-mapping: 화자 매핑 모달 상태
  const [isSpeakerMappingModalOpen, setIsSpeakerMappingModalOpen] = useState(false);
  const [speakerMappingEvidence, setSpeakerMappingEvidence] = useState<Evidence | null>(null);

  const { table, setTypeFilter, setDateFilter } = useEvidenceTable(items);

  const handleRetry = async (evidenceId: string) => {
    setRetryingIds((prev) => new Set(prev).add(evidenceId));
    try {
      await retryEvidence(evidenceId);
      onRetry?.(evidenceId);
    } catch (err) {
      logger.error('Failed to retry evidence:', err);
      toast.error('증거 재처리에 실패했습니다.');
    } finally {
      setRetryingIds((prev) => {
        const next = new Set(prev);
        next.delete(evidenceId);
        return next;
      });
    }
  };

  const handleOpenSummary = (evidence: Evidence) => {
    setSelectedEvidence(evidence);
    setIsSummaryModalOpen(true);
  };

  const handleCloseSummary = () => {
    setIsSummaryModalOpen(false);
    setSelectedEvidence(null);
  };

  const handleOpenContent = async (evidence: Evidence) => {
    setSelectedEvidence(evidence);
    setIsContentModalOpen(true);
    setIsLoadingContent(true);
    setEvidenceContent(null);

    try {
      const result = await getEvidenceDetail(evidence.id);
      if (result.data?.content) {
        setEvidenceContent(result.data.content);
      }
    } catch (err) {
      logger.error('Failed to fetch evidence content:', err);
      toast.error('증거 내용을 불러오지 못했습니다.');
    } finally {
      setIsLoadingContent(false);
    }
  };

  const handleCloseContent = () => {
    setIsContentModalOpen(false);
    setSelectedEvidence(null);
    setEvidenceContent(null);
  };

  // 015-evidence-speaker-mapping: 화자 매핑 모달 핸들러
  const handleOpenSpeakerMapping = (evidence: Evidence) => {
    setSpeakerMappingEvidence(evidence);
    setIsSpeakerMappingModalOpen(true);
  };

  const handleCloseSpeakerMapping = () => {
    setIsSpeakerMappingModalOpen(false);
    setSpeakerMappingEvidence(null);
  };

  const handleSaveSpeakerMapping = async (mapping: SpeakerMapping) => {
    if (!speakerMappingEvidence) return;

    const response = await updateSpeakerMapping(speakerMappingEvidence.id, {
      speaker_mapping: mapping,
    });

    if (response.error) {
      throw new Error(response.error);
    }

    // 매핑 업데이트 콜백 호출 (목록 새로고침용)
    onSpeakerMappingUpdate?.(speakerMappingEvidence.id);
  };

  const handleTypeFilterChange = (value: string) => {
    setTypeFilterValue(value);
    setTypeFilter(value);
  };

  const handleDateFilterChange = (value: string) => {
    setDateFilterValue(value);
    setDateFilter(value);
  };

  return (
    <div className="space-y-4">
      {/* Filter Controls - Calm Control UX */}
      <div className="flex items-center space-x-4 bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <Filter className="w-5 h-5 text-gray-400" />

        <div className="flex items-center space-x-2">
          <label htmlFor="type-filter" className="text-sm font-medium text-neutral-700">
            유형 필터:
          </label>
          <select
            id="type-filter"
            value={typeFilter}
            onChange={(e) => handleTypeFilterChange(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all"
          >
            <option value="all">전체</option>
            <option value="text">텍스트</option>
            <option value="image">이미지</option>
            <option value="audio">오디오</option>
            <option value="video">비디오</option>
            <option value="pdf">PDF</option>
          </select>
        </div>

        <div className="flex items-center space-x-2">
          <label htmlFor="date-filter" className="text-sm font-medium text-neutral-700">
            날짜 필터:
          </label>
          <select
            id="date-filter"
            value={dateFilter}
            onChange={(e) => handleDateFilterChange(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary transition-all"
          >
            <option value="all">전체</option>
            <option value="today">오늘</option>
            <option value="week">최근 7일</option>
            <option value="month">최근 30일</option>
          </select>
        </div>

        <div className="text-sm text-gray-500 ml-auto">
          {table.getFilteredRowModel().rows.length}개 / 전체 {items.length}개
        </div>
      </div>

      {/* DataTable - Shadcn/ui style */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200" aria-label="증거 자료 목록">
            <caption className="sr-only">
              증거 자료 목록. 유형, 파일명, AI 요약, 업로드 날짜, 상태 열이 있습니다.
              파일명과 업로드 날짜는 정렬 가능합니다.
            </caption>
            <thead className="bg-gray-50">
              <tr>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  유형
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  aria-sort={
                    table.getColumn('filename')?.getIsSorted() === 'asc'
                      ? 'ascending'
                      : table.getColumn('filename')?.getIsSorted() === 'desc'
                        ? 'descending'
                        : 'none'
                  }
                >
                  <button
                    type="button"
                    onClick={() => table.getColumn('filename')?.toggleSorting()}
                    className="flex items-center space-x-1 hover:text-secondary transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded"
                    aria-label="파일명으로 정렬"
                  >
                    <span>파일명</span>
                    <ArrowUpDown className="w-4 h-4" aria-hidden="true" />
                  </button>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  AI 요약
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  aria-sort={
                    table.getColumn('uploadDate')?.getIsSorted() === 'asc'
                      ? 'ascending'
                      : table.getColumn('uploadDate')?.getIsSorted() === 'desc'
                        ? 'descending'
                        : 'none'
                  }
                >
                  <button
                    type="button"
                    onClick={() => table.getColumn('uploadDate')?.toggleSorting()}
                    className="flex items-center space-x-1 hover:text-secondary transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded"
                    aria-label="업로드 날짜로 정렬"
                  >
                    <span>업로드 날짜</span>
                    <ArrowUpDown className="w-4 h-4" aria-hidden="true" />
                  </button>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  상태
                </th>
                {/* 015-evidence-speaker-mapping: 화자 매핑 열 */}
                {parties.length > 0 && (
                  <th
                    scope="col"
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    화자
                  </th>
                )}
                <th scope="col" className="relative px-6 py-3">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {table.getRowModel().rows.map((row, index) => {
                const evidence = row.original;
                const zebraBackground = index % 2 === 0 ? 'bg-white' : 'bg-gray-50/70';

                return (
                  <tr
                    key={evidence.id}
                    className={`group transition-colors ${zebraBackground} hover:bg-primary-light/50`}
                  >
                    {/* Type Icon - 클릭하면 원문 보기 */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => handleOpenContent(evidence)}
                        className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                        aria-label={`${evidence.filename} 원문 보기`}
                      >
                        <EvidenceTypeIcon type={evidence.type} />
                      </button>
                    </td>

                    {/* Filename */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {evidence.filename}
                      </div>
                      <div className="text-xs text-gray-500">
                        {(evidence.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                      <div className="text-[11px] text-gray-400 hidden group-hover:block mt-1">
                        클릭하여 상세 · 타임라인 연결 옵션 보기
                      </div>
                    </td>

                    {/* AI Summary */}
                    <td className="px-6 py-4">
                      {evidence.status === 'completed' && evidence.summary ? (
                        <button
                          type="button"
                          onClick={() => handleOpenSummary(evidence)}
                          className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-sm font-medium text-primary bg-primary-light hover:bg-primary-light/80 rounded-lg transition-colors"
                        >
                          <Sparkles className="w-4 h-4" />
                          <span>요약 보기</span>
                        </button>
                      ) : evidence.status === 'processing' || evidence.status === 'queued' ? (
                        <span className="text-sm text-gray-400">분석 중...</span>
                      ) : (
                        <span className="text-sm text-gray-400">-</span>
                      )}
                    </td>

                    {/* Upload Date */}
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(evidence.uploadDate).toLocaleDateString()}
                    </td>

                    {/* Status Badge */}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <EvidenceStatusBadge status={evidence.status} />
                        {evidence.status === 'failed' && (
                          <button
                            type="button"
                            onClick={() => handleRetry(evidence.id)}
                            disabled={retryingIds.has(evidence.id)}
                            className="flex items-center gap-1 px-2 py-1 text-xs font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-md transition-colors disabled:opacity-50"
                            title="재시도"
                          >
                            <RefreshCw className={`w-3 h-3 ${retryingIds.has(evidence.id) ? 'animate-spin' : ''}`} />
                            {retryingIds.has(evidence.id) ? '재시도 중...' : '재시도'}
                          </button>
                        )}
                      </div>
                    </td>

                    {/* 015-evidence-speaker-mapping: 화자 매핑 뱃지 (T027) */}
                    {parties.length > 0 && (
                      <td className="px-6 py-4 whitespace-nowrap">
                        <SpeakerMappingBadge
                          hasSpeakerMapping={evidence.hasSpeakerMapping}
                          speakerMapping={evidence.speakerMapping}
                          onClick={() => handleOpenSpeakerMapping(evidence)}
                        />
                      </td>
                    )}

                    {/* Actions */}
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        type="button"
                        className="text-gray-400 hover:text-neutral-600 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
                        aria-label={`${evidence.filename} 추가 작업`}
                      >
                        <MoreVertical className="w-5 h-5" />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <DataTablePagination table={table} />
      </div>

      {/* AI Summary Modal */}
      <AISummaryModal
        isOpen={isSummaryModalOpen}
        onClose={handleCloseSummary}
        evidence={selectedEvidence}
      />

      {/* Content Modal (원문 보기) */}
      <ContentModal
        isOpen={isContentModalOpen}
        onClose={handleCloseContent}
        evidence={selectedEvidence}
        content={evidenceContent}
        isLoading={isLoadingContent}
        showSpeakerMappingButton={parties.length > 0}
        onOpenSpeakerMapping={() => {
          if (selectedEvidence) {
            handleCloseContent();
            handleOpenSpeakerMapping(selectedEvidence);
          }
        }}
      />

      {/* 015-evidence-speaker-mapping: 화자 매핑 모달 */}
      {speakerMappingEvidence && (
        <SpeakerMappingModal
          isOpen={isSpeakerMappingModalOpen}
          onClose={handleCloseSpeakerMapping}
          evidence={speakerMappingEvidence}
          parties={parties}
          onSave={handleSaveSpeakerMapping}
          onSaveSuccess={() => {
            // 목록 새로고침
            onSpeakerMappingUpdate?.(speakerMappingEvidence.id);
          }}
        />
      )}
    </div>
  );
}
