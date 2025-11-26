import { useState } from 'react';
import { Evidence } from '@/types/evidence';
import { X, FileText, Image, Mic, Video, File, Check } from 'lucide-react';
import { DraftTemplate } from '@/types/draft';

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
    const [selectedTemplateId, setSelectedTemplateId] = useState<string>(templates[0]?.id ?? 'default');

    if (!isOpen) return null;

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

    const getTypeIcon = (type: string) => {
        switch (type) {
            case 'text': return <FileText className="w-4 h-4 text-gray-500" />;
            case 'image': return <Image className="w-4 h-4 text-blue-500" />;
            case 'audio': return <Mic className="w-4 h-4 text-purple-500" />;
            case 'video': return <Video className="w-4 h-4 text-red-500" />;
            case 'pdf': return <File className="w-4 h-4 text-red-600" />;
            default: return <File className="w-4 h-4 text-gray-400" />;
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] flex flex-col animate-in fade-in zoom-in duration-200">
                <div className="flex items-center justify-between p-6 border-b border-gray-100">
                    <div>
                        <h2 className="text-xl font-bold text-deep-trust-blue">Draft 생성 옵션</h2>
                        <p className="text-sm text-gray-500 mt-1">초안 작성에 참고할 증거를 선택해주세요.</p>
                    </div>
                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="닫기"
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <X className="w-6 h-6" />
                    </button>
                </div>

                <div className="px-6 pt-4 space-y-3">
                    <label className="flex flex-col text-sm text-gray-700">
                        <span className="font-medium mb-1">템플릿 선택</span>
                        <select
                            aria-label="템플릿 선택"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-accent bg-white text-sm"
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

                <div className="p-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                    <div className="text-sm font-medium text-gray-700">
                        선택된 증거: <span className="text-accent">{selectedIds.length}</span> / {evidenceList.length}
                    </div>
                    <button
                        type="button"
                        onClick={handleSelectAll}
                        className="text-xs text-deep-trust-blue hover:underline font-medium"
                    >
                        {selectedIds.length === evidenceList.length ? '전체 해제' : '전체 선택'}
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-2">
                    {evidenceList.length === 0 ? (
                        <div className="text-center py-10 text-gray-500">
                            선택 가능한 증거가 없습니다.
                        </div>
                    ) : (
                        evidenceList.map((evidence) => (
                            <div
                                key={evidence.id}
                                onClick={() => toggleSelection(evidence.id)}
                                className={`flex items-center p-3 rounded-lg border cursor-pointer transition-all ${selectedIds.includes(evidence.id)
                                        ? 'border-accent bg-accent/5 ring-1 ring-accent'
                                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                                    }`}
                            >
                                <div className={`w-5 h-5 rounded border flex items-center justify-center mr-3 transition-colors ${selectedIds.includes(evidence.id)
                                        ? 'bg-accent border-accent text-white'
                                        : 'border-gray-300 bg-white'
                                    }`}>
                                    {selectedIds.includes(evidence.id) && <Check className="w-3 h-3" />}
                                </div>
                                <div className="mr-3 p-2 bg-gray-100 rounded-md">
                                    {getTypeIcon(evidence.type)}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <h4 className="text-sm font-medium text-gray-900 truncate">{evidence.filename}</h4>
                                    <p className="text-xs text-gray-500 truncate">{evidence.summary || '요약 없음'}</p>
                                </div>
                                <div className="text-xs text-gray-400 whitespace-nowrap ml-2">
                                    {new Date(evidence.uploadDate).toLocaleDateString()}
                                </div>
                            </div>
                        ))
                    )}
                </div>

                <div className="p-6 border-t border-gray-100 flex justify-end space-x-3 bg-gray-50 rounded-b-xl">
                    <button
                        type="button"
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-800 bg-white border border-gray-300 rounded-lg shadow-sm hover:bg-gray-50 transition-colors"
                    >
                        취소
                    </button>
                    <button
                        type="button"
                        onClick={() => onGenerate(selectedIds)}
                        disabled={selectedIds.length === 0}
                        className="px-4 py-2 text-sm font-medium text-white bg-deep-trust-blue hover:bg-slate-800 rounded-lg shadow-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                    >
                        <FileText className="w-4 h-4 mr-2" />
                        선택한 증거로 초안 생성
                    </button>
                </div>
            </div>
        </div>
    );
}
