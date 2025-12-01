'use client';

import { useState } from 'react';
import { Evidence } from '@/types/evidence';
import { FileText, Image, Mic, Video, File, Check } from 'lucide-react';
import { DraftTemplate } from '@/types/draft';
import { Modal, Button } from '@/components/primitives';

interface DraftGenerationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (selectedEvidenceIds: string[]) => void;
  evidenceList: Evidence[];
  templates?: DraftTemplate[];
}

export default function DraftGenerationModal({
  isOpen,
  onClose,
  onGenerate,
  evidenceList,
  templates = [
    { id: 'default', name: '기본 양식', updatedAt: '2024-05-01' },
    { id: 'custom-1', name: '이혼 소송 답변서 v1', updatedAt: '2024-05-10' },
  ],
}: DraftGenerationModalProps) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>(
    templates[0]?.id ?? 'default'
  );
  const [isGenerating, setIsGenerating] = useState(false);

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedIds.length === evidenceList.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(evidenceList.map((e) => e.id));
    }
  };

  const handleGenerate = async () => {
    setIsGenerating(true);
    try {
      await onGenerate(selectedIds);
    } finally {
      setIsGenerating(false);
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'text':
        return <FileText className="w-4 h-4 text-neutral-500" />;
      case 'image':
        return <Image className="w-4 h-4 text-blue-500" />;
      case 'audio':
        return <Mic className="w-4 h-4 text-purple-500" />;
      case 'video':
        return <Video className="w-4 h-4 text-red-500" />;
      case 'pdf':
        return <File className="w-4 h-4 text-red-600" />;
      default:
        return <File className="w-4 h-4 text-neutral-400" />;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Draft 생성 옵션"
      description="초안 작성에 참고할 증거를 선택해주세요."
      size="xl"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            취소
          </Button>
          <Button
            variant="secondary"
            onClick={handleGenerate}
            disabled={selectedIds.length === 0}
            isLoading={isGenerating}
            leftIcon={<FileText className="w-4 h-4" />}
          >
            선택한 증거로 초안 생성
          </Button>
        </>
      }
    >
      {/* Template Selection */}
      <div className="space-y-3 mb-4">
        <label className="flex flex-col text-sm text-neutral-700">
          <span className="font-medium mb-1">템플릿 선택</span>
          <select
            aria-label="템플릿 선택"
            className="w-full px-3 py-2 border border-neutral-300 rounded-lg
                       focus:outline-none focus:ring-2 focus:ring-primary
                       bg-white text-sm transition-colors duration-200"
            value={selectedTemplateId}
            onChange={(e) => setSelectedTemplateId(e.target.value)}
          >
            {templates.map((template) => (
              <option key={template.id} value={template.id}>
                {template.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {/* Selection Header */}
      <div className="p-4 -mx-6 border-y border-neutral-100 bg-neutral-50 flex justify-between items-center">
        <div className="text-sm font-medium text-neutral-700">
          선택된 증거:{' '}
          <span className="text-primary">{selectedIds.length}</span> /{' '}
          {evidenceList.length}
        </div>
        <button
          type="button"
          onClick={handleSelectAll}
          className="text-xs text-secondary hover:underline font-medium
                     focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded"
        >
          {selectedIds.length === evidenceList.length ? '전체 해제' : '전체 선택'}
        </button>
      </div>

      {/* Evidence List */}
      <div className="space-y-2 mt-4 max-h-[40vh] overflow-y-auto">
        {evidenceList.length === 0 ? (
          <div className="text-center py-10 text-neutral-500">
            선택 가능한 증거가 없습니다.
          </div>
        ) : (
          evidenceList.map((evidence) => {
            const isSelected = selectedIds.includes(evidence.id);
            return (
              <div
                key={evidence.id}
                role="checkbox"
                aria-checked={isSelected}
                tabIndex={0}
                onClick={() => toggleSelection(evidence.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleSelection(evidence.id);
                  }
                }}
                className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all
                  focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
                  ${
                    isSelected
                      ? 'border-primary bg-primary-light ring-1 ring-primary'
                      : 'border-neutral-200 hover:border-neutral-300 hover:bg-neutral-50'
                  }`}
              >
                {/* Custom Checkbox */}
                <div
                  className={`w-5 h-5 rounded border flex items-center justify-center mr-3 transition-colors ${
                    isSelected
                      ? 'bg-primary border-primary text-white'
                      : 'border-neutral-300 bg-white'
                  }`}
                  aria-hidden="true"
                >
                  {isSelected && <Check className="w-3 h-3" />}
                </div>

                {/* Type Icon */}
                <div className="mr-3 p-2 bg-neutral-100 rounded-md">
                  {getTypeIcon(evidence.type)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <h4 className="text-sm font-medium text-neutral-900 truncate">
                    {evidence.filename}
                  </h4>
                  <p className="text-xs text-neutral-500 truncate">
                    {evidence.summary || '요약 없음'}
                  </p>
                </div>

                {/* Date */}
                <div className="text-xs text-neutral-400 whitespace-nowrap ml-2">
                  {new Date(evidence.uploadDate).toLocaleDateString()}
                </div>
              </div>
            );
          })
        )}
      </div>
    </Modal>
  );
}
