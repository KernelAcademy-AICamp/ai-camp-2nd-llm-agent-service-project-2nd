/**
 * Speaker Mapping Modal Component
 * 015-evidence-speaker-mapping: T015, T016, T017
 *
 * 대화 참여자를 인물관계도의 인물과 매핑하는 모달
 */

'use client';

import { useState, useEffect, useMemo, useId } from 'react';
import { X, Users, AlertCircle, Loader2, Save, Trash2, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import type { PartyNode } from '@/types/party';
import type { SpeakerMapping, Evidence } from '@/types/evidence';
import { useSpeakerMapping, extractSpeakersFromContent } from '@/hooks/useSpeakerMapping';
import { PARTY_TYPE_LABELS } from '@/types/party';

interface SpeakerMappingModalProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Close handler */
  onClose: () => void;
  /** Evidence being mapped */
  evidence: Evidence;
  /** Available parties from the case */
  parties: PartyNode[];
  /** Save handler - called with the mapping request */
  onSave: (mapping: SpeakerMapping) => Promise<void>;
  /** Optional: Called after successful save */
  onSaveSuccess?: () => void;
}

export function SpeakerMappingModal({
  isOpen,
  onClose,
  evidence,
  parties,
  onSave,
  onSaveSuccess,
}: SpeakerMappingModalProps) {
  const [isSaving, setIsSaving] = useState(false);
  const titleId = useId();

  // Extract speakers from evidence content
  const detectedSpeakers = useMemo(() => {
    return extractSpeakersFromContent(evidence.content || '');
  }, [evidence.content]);

  // Use speaker mapping hook
  const {
    mapping,
    isDirty,
    validationErrors,
    setMappingItem,
    removeMappingItem,
    clearMapping,
    resetMapping,
    isValid,
  } = useSpeakerMapping({
    initialMapping: evidence.speakerMapping || {},
    parties,
  });

  // Reset mapping when modal opens with new evidence
  useEffect(() => {
    if (isOpen) {
      resetMapping();
    }
  }, [isOpen, evidence.id, resetMapping]);

  // Handle save
  const handleSave = async () => {
    if (!isValid) {
      validationErrors.forEach((err) => toast.error(err));
      return;
    }

    setIsSaving(true);
    try {
      await onSave(mapping);
      toast.success('화자 매핑이 저장되었습니다.');
      onSaveSuccess?.();
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '저장에 실패했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  // Handle clear and save (remove all mappings)
  const handleClearAndSave = async () => {
    setIsSaving(true);
    try {
      await onSave({});
      toast.success('화자 매핑이 삭제되었습니다.');
      onSaveSuccess?.();
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '삭제에 실패했습니다.');
    } finally {
      setIsSaving(false);
    }
  };

  // Handle close with unsaved changes warning
  const handleClose = () => {
    if (isDirty) {
      if (!confirm('저장하지 않은 변경사항이 있습니다. 정말 닫으시겠습니까?')) {
        return;
      }
    }
    onClose();
  };

  if (!isOpen) return null;

  // T017: Empty party list edge case
  const hasParties = parties.length > 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" aria-hidden="true">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="bg-white dark:bg-neutral-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center gap-2">
            <Users className="w-5 h-5 text-info" />
            <h2 id={titleId} className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
              화자 매핑
            </h2>
          </div>
          <button
            onClick={handleClose}
            aria-label="닫기"
            className="p-1 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded transition-colors"
          >
            <X className="w-5 h-5 text-neutral-500 dark:text-neutral-400" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {/* T017: Empty party list warning */}
          {!hasParties ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-warning-light flex items-center justify-center">
                <AlertCircle className="w-8 h-8 text-warning" />
              </div>
              <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-2">
                인물관계도에 등록된 인물이 없습니다
              </h3>
              <p className="text-neutral-500 dark:text-neutral-400 max-w-md mx-auto mb-4">
                화자 매핑을 설정하려면 먼저 &quot;인물관계&quot; 탭에서 당사자(원고, 피고 등)를 추가해주세요.
              </p>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-neutral-200 dark:bg-neutral-700 text-neutral-700 dark:text-neutral-300 rounded-lg hover:bg-neutral-300 dark:hover:bg-neutral-600 transition-colors"
              >
                닫기
              </button>
            </div>
          ) : (
            <>
              {/* Instructions */}
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mb-4">
                대화에서 감지된 화자를 인물관계도의 인물과 연결하세요.
                매핑된 화자는 사실관계 생성 시 실제 인물명으로 해석됩니다.
              </p>

              {/* Evidence filename */}
              <div className="mb-4 p-3 bg-neutral-50 dark:bg-neutral-900 rounded-lg">
                <span className="text-xs text-neutral-500 dark:text-neutral-400">증거 파일: </span>
                <span className="text-sm text-neutral-700 dark:text-neutral-300">{evidence.filename}</span>
              </div>

              {/* Detected speakers */}
              {detectedSpeakers.length === 0 ? (
                <div className="text-center py-6 border border-dashed border-neutral-300 dark:border-neutral-600 rounded-lg mb-4">
                  <p className="text-neutral-500 dark:text-neutral-400">
                    대화 형식의 화자가 감지되지 않았습니다.
                  </p>
                  <p className="text-sm text-neutral-400 dark:text-neutral-500 mt-1">
                    &quot;이름:&quot; 형식의 대화 내용이 필요합니다.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {detectedSpeakers.map((speaker) => {
                    const currentMapping = mapping[speaker];
                    const isMapped = !!currentMapping;

                    return (
                      <div
                        key={speaker}
                        className={`p-4 rounded-lg border ${
                          isMapped
                            ? 'border-success/30 bg-success-light'
                            : 'border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-neutral-900 dark:text-neutral-100">
                              &quot;{speaker}&quot;
                            </span>
                            {isMapped && (
                              <CheckCircle className="w-4 h-4 text-success" />
                            )}
                          </div>
                          {isMapped && (
                            <button
                              onClick={() => removeMappingItem(speaker)}
                              aria-label="매핑 해제"
                              className="p-1 text-error hover:bg-error-light rounded transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>

                        {/* Party selection dropdown */}
                        <select
                          value={currentMapping?.party_id || ''}
                          onChange={(e) => {
                            const partyId = e.target.value;
                            if (partyId) {
                              const party = parties.find((p) => p.id === partyId);
                              if (party) {
                                setMappingItem(speaker, party.id, party.name);
                              }
                            } else {
                              removeMappingItem(speaker);
                            }
                          }}
                          className="w-full px-3 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg
                                     bg-white dark:bg-neutral-700 text-neutral-900 dark:text-neutral-100
                                     focus:ring-2 focus:ring-primary focus:border-transparent"
                        >
                          <option value="">-- 인물 선택 --</option>
                          {parties.map((party) => (
                            <option key={party.id} value={party.id}>
                              {party.name} ({PARTY_TYPE_LABELS[party.type]})
                              {party.alias ? ` - ${party.alias}` : ''}
                            </option>
                          ))}
                        </select>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Mapped count summary */}
              {detectedSpeakers.length > 0 && (
                <div className="mt-4 text-sm text-neutral-500 dark:text-neutral-400">
                  {Object.keys(mapping).length}명 / {detectedSpeakers.length}명 매핑됨
                </div>
              )}

              {/* Validation errors */}
              {validationErrors.length > 0 && (
                <div className="mt-4 p-3 bg-error-light border border-error/30 rounded-lg">
                  <ul className="list-disc list-inside text-sm text-error">
                    {validationErrors.map((err, i) => (
                      <li key={i}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        {hasParties && (
          <div className="flex items-center justify-between px-6 py-4 border-t border-neutral-200 dark:border-neutral-700">
            <div>
              {Object.keys(mapping).length > 0 && (
                <button
                  onClick={handleClearAndSave}
                  disabled={isSaving}
                  className="px-3 py-2 text-sm text-error hover:bg-error-light rounded-lg transition-colors disabled:opacity-50"
                >
                  <Trash2 className="w-4 h-4 inline mr-1" />
                  모두 해제
                </button>
              )}
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleClose}
                disabled={isSaving}
                className="px-4 py-2 text-neutral-600 dark:text-neutral-400 hover:text-neutral-900 dark:hover:text-neutral-100
                           border border-neutral-300 dark:border-neutral-600 rounded-lg transition-colors disabled:opacity-50"
              >
                취소
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving || !isDirty || !isValid}
                className="px-4 py-2 bg-primary text-white rounded-lg
                           hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSaving ? (
                  <>
                    <Loader2 className="w-4 h-4 inline mr-1 animate-spin" />
                    저장 중...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 inline mr-1" />
                    저장
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SpeakerMappingModal;
