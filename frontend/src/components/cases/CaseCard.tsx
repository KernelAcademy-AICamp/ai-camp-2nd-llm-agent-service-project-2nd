import Link from 'next/link';
import { useState } from 'react';
import { Case } from '@/types/case';
import { FileText, Clock, AlertCircle, CheckCircle2, ChevronDown } from 'lucide-react';

interface CaseCardProps {
    caseData: Case;
    onStatusChange?: (caseId: string, newStatus: 'open' | 'closed') => void;
}

export default function CaseCard({ caseData, onStatusChange }: CaseCardProps) {
    const [isStatusDropdownOpen, setIsStatusDropdownOpen] = useState(false);

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'ready': return 'text-success-green';
            case 'generating': return 'text-accent';
            default: return 'text-gray-400';
        }
    };

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

    return (
        <Link href={`/cases/${caseData.id}`}>
            <div className="relative card p-6 h-full flex flex-col justify-between group cursor-pointer bg-calm-grey border border-gray-200 rounded-lg overflow-hidden transition-all duration-300 hover:shadow-lg">
                {/* Border Beam Glow Effect - Magic UI Style */}
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
                    <div className="absolute inset-[-2px] bg-gradient-to-r from-transparent via-accent to-transparent rounded-lg blur-sm animate-border-beam"></div>
                </div>

                {/* Content wrapper to ensure proper z-index layering */}
                <div className="relative z-10 flex flex-col h-full justify-between">
                <div>
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="text-xl font-bold text-deep-trust-blue group-hover:text-accent transition-colors">
                                {caseData.title}
                            </h3>
                            <p className="text-sm text-gray-500 mt-1">{caseData.clientName}</p>
                        </div>
                        <div className="relative">
                            <button
                                onClick={toggleStatusDropdown}
                                className={`px-2 py-1 rounded-full text-xs font-medium flex items-center space-x-1 ${caseData.status === 'open' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                                    }`}
                                aria-label="상태 변경"
                            >
                                <span>{caseData.status === 'open' ? '진행 중' : '종결'}</span>
                                <ChevronDown className="w-3 h-3" />
                            </button>
                            {isStatusDropdownOpen && (
                                <div className="absolute right-0 mt-1 w-32 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                                    <button
                                        role="option"
                                        onClick={(e) => handleStatusChange(e, 'open')}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                    >
                                        진행 중
                                    </button>
                                    <button
                                        role="option"
                                        onClick={(e) => handleStatusChange(e, 'closed')}
                                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                    >
                                        종결
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="space-y-3">
                        <div className="flex items-center text-sm text-gray-600">
                            <FileText className="w-4 h-4 mr-2" />
                            <span>증거 {caseData.evidenceCount}건</span>
                        </div>
                        <div className="flex items-center text-sm text-gray-600">
                            <Clock className="w-4 h-4 mr-2" />
                            <span>최근 업데이트: {new Date(caseData.lastUpdated).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>

                <div className="mt-6 pt-4 border-t border-gray-100 flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-500">Draft 상태:</span>
                        {caseData.draftStatus === 'ready' ? (
                            <div className="flex items-center text-success-green text-sm font-bold">
                                <CheckCircle2 className="w-4 h-4 mr-1" />
                                <span>준비됨</span>
                            </div>
                        ) : caseData.draftStatus === 'generating' ? (
                            <div className="flex items-center text-accent text-sm font-bold animate-pulse">
                                <Clock className="w-4 h-4 mr-1" />
                                <span>생성 중...</span>
                            </div>
                        ) : (
                            <div className="flex items-center text-gray-400 text-sm">
                                <AlertCircle className="w-4 h-4 mr-1" />
                                <span>미생성</span>
                            </div>
                        )}
                    </div>
                </div>
                </div> {/* End of content wrapper */}
            </div>
        </Link>
    );
}
