/**
 * EvidenceLinkModal - Modal for linking evidence to a party
 * User Story 4: Evidence-Party Linking
 */

'use client';

import { useState, useEffect, useId } from 'react';
import type {
  PartyNode,
  PartyRelationship,
  EvidenceLinkCreate,
  LinkType,
} from '@/types/party';
import { LINK_TYPE_LABELS } from '@/types/party';

interface EvidenceItem {
  id: string;
  summary?: string;
  filename?: string;
  type: string;
  timestamp: string;
  labels?: string[];
}

interface EvidenceLinkModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: EvidenceLinkCreate) => Promise<void>;
  parties: PartyNode[];
  relationships: PartyRelationship[];
  evidenceList: EvidenceItem[];
  isLoadingEvidence: boolean;
  preSelectedPartyId?: string;
  preSelectedRelationshipId?: string;
}

const LINK_TYPES: LinkType[] = ['mentions', 'proves', 'involves', 'contradicts'];

export function EvidenceLinkModal({
  isOpen,
  onClose,
  onSave,
  parties,
  relationships,
  evidenceList,
  isLoadingEvidence,
  preSelectedPartyId,
  preSelectedRelationshipId,
}: EvidenceLinkModalProps) {
  const [selectedEvidence, setSelectedEvidence] = useState<string>('');
  const [selectedParty, setSelectedParty] = useState<string>(preSelectedPartyId || '');
  const [selectedRelationship, setSelectedRelationship] = useState<string>(preSelectedRelationshipId || '');
  const [linkType, setLinkType] = useState<LinkType>('involves');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const titleId = useId();

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setSelectedEvidence('');
      setSelectedParty(preSelectedPartyId || '');
      setSelectedRelationship(preSelectedRelationshipId || '');
      setLinkType('involves');
      setError(null);
      setSearchQuery('');
    }
  }, [isOpen, preSelectedPartyId, preSelectedRelationshipId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!selectedEvidence) {
      setError('증거를 선택해주세요.');
      return;
    }

    if (!selectedParty && !selectedRelationship) {
      setError('당사자 또는 관계를 선택해주세요.');
      return;
    }

    setIsSubmitting(true);

    try {
      const data: EvidenceLinkCreate = {
        evidence_id: selectedEvidence,
        party_id: selectedParty || undefined,
        relationship_id: selectedRelationship || undefined,
        link_type: linkType,
      };
      await onSave(data);
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '연결에 실패했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Filter evidence by search query (searches summary, filename, type, labels)
  const filteredEvidence = evidenceList.filter((e) => {
    const query = searchQuery.toLowerCase();
    return (
      e.summary?.toLowerCase().includes(query) ||
      e.filename?.toLowerCase().includes(query) ||
      e.type.toLowerCase().includes(query) ||
      e.labels?.some((label) => label.toLowerCase().includes(query))
    );
  });

  const getPartyName = (partyId: string) => {
    return parties.find((p) => p.id === partyId)?.name || partyId;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} aria-hidden="true" />

      {/* Modal */}
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative bg-white dark:bg-neutral-800 rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200 dark:border-neutral-700">
          <h2 id={titleId} className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
            증거 연결
          </h2>
          <button
            onClick={onClose}
            aria-label="닫기"
            className="text-neutral-400 hover:text-neutral-600 dark:hover:text-neutral-300"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
            {/* Error message */}
            {error && (
              <div className="p-3 text-sm text-error bg-error-light rounded-lg">
                {error}
              </div>
            )}

            {/* Evidence selection */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                증거 선택 <span className="text-error">*</span>
              </label>
              <input
                type="text"
                placeholder="증거 검색..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-3 py-2 mb-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary dark:bg-neutral-800 dark:border-neutral-600 dark:text-white"
              />
              <div className="max-h-40 overflow-y-auto border rounded-lg">
                {isLoadingEvidence ? (
                  <div className="p-4 text-center text-neutral-500 dark:text-neutral-400">
                    불러오는 중...
                  </div>
                ) : filteredEvidence.length === 0 ? (
                  <div className="p-4 text-center text-neutral-500 dark:text-neutral-400">
                    {searchQuery ? '검색 결과가 없습니다' : '증거가 없습니다'}
                  </div>
                ) : (
                  filteredEvidence.map((evidence) => (
                    <label
                      key={evidence.id}
                      className={`
                        flex items-start gap-3 p-3 cursor-pointer hover:bg-neutral-50 dark:hover:bg-neutral-700
                        ${selectedEvidence === evidence.id ? 'bg-info-light' : ''}
                      `}
                    >
                      <input
                        type="radio"
                        name="evidence"
                        value={evidence.id}
                        checked={selectedEvidence === evidence.id}
                        onChange={(e) => setSelectedEvidence(e.target.value)}
                        className="mt-1"
                      />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
                          {evidence.summary || evidence.filename || `증거 #${evidence.id.slice(0, 8)}`}
                        </p>
                        <p className="text-xs text-neutral-500 dark:text-neutral-400">
                          {evidence.type} · {new Date(evidence.timestamp).toLocaleDateString()}
                          {evidence.filename && evidence.summary && (
                            <span className="ml-1 text-neutral-400 dark:text-neutral-500">({evidence.filename})</span>
                          )}
                        </p>
                        {evidence.labels && evidence.labels.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {evidence.labels.slice(0, 3).map((label) => (
                              <span
                                key={label}
                                className="px-1.5 py-0.5 text-xs bg-neutral-100 dark:bg-neutral-700 text-neutral-600 dark:text-neutral-300 rounded"
                              >
                                {label}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </label>
                  ))
                )}
              </div>
            </div>

            {/* Target selection */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                연결 대상 <span className="text-error">*</span>
              </label>
              <div className="space-y-2">
                {/* Party selection */}
                <select
                  value={selectedParty}
                  onChange={(e) => {
                    setSelectedParty(e.target.value);
                    if (e.target.value) setSelectedRelationship('');
                  }}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary dark:bg-neutral-800 dark:border-neutral-600 dark:text-white"
                >
                  <option value="">당사자 선택...</option>
                  {parties.map((party) => (
                    <option key={party.id} value={party.id}>
                      {party.name} ({party.type})
                    </option>
                  ))}
                </select>

                <div className="text-center text-xs text-neutral-400 dark:text-neutral-500">또는</div>

                {/* Relationship selection */}
                <select
                  value={selectedRelationship}
                  onChange={(e) => {
                    setSelectedRelationship(e.target.value);
                    if (e.target.value) setSelectedParty('');
                  }}
                  className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary dark:bg-neutral-800 dark:border-neutral-600 dark:text-white"
                >
                  <option value="">관계 선택...</option>
                  {relationships.map((rel) => (
                    <option key={rel.id} value={rel.id}>
                      {getPartyName(rel.source_party_id)} ↔ {getPartyName(rel.target_party_id)} ({rel.type})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Link type */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
                연결 유형
              </label>
              <div className="grid grid-cols-2 gap-2">
                {LINK_TYPES.map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setLinkType(type)}
                    className={`
                      px-3 py-2 text-sm rounded-lg border transition-colors
                      ${linkType === type
                        ? 'border-info bg-info-light text-info'
                        : 'border-neutral-200 hover:border-neutral-300 dark:border-neutral-600 dark:hover:border-neutral-500'
                      }
                    `}
                  >
                    {LINK_TYPE_LABELS[type]}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex justify-end gap-3 px-6 py-4 border-t border-neutral-200 dark:border-neutral-700 bg-neutral-50 dark:bg-neutral-900 rounded-b-lg">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-lg"
              disabled={isSubmitting}
            >
              취소
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-primary hover:bg-primary/90 rounded-lg disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? '연결 중...' : '연결'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
