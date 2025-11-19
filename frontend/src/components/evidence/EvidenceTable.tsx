import { Evidence, EvidenceStatus } from '@/types/evidence';
import { FileText, Image, Mic, Video, File, MoreVertical, CheckCircle2, Clock, AlertCircle, Loader2 } from 'lucide-react';

interface EvidenceTableProps {
    items: Evidence[];
}

export default function EvidenceTable({ items }: EvidenceTableProps) {
    const getTypeIcon = (type: string) => {
        switch (type) {
            case 'text': return <FileText className="w-5 h-5 text-gray-500" />;
            case 'image': return <Image className="w-5 h-5 text-blue-500" />;
            case 'audio': return <Mic className="w-5 h-5 text-purple-500" />;
            case 'video': return <Video className="w-5 h-5 text-red-500" />;
            case 'pdf': return <File className="w-5 h-5 text-red-600" />;
            default: return <File className="w-5 h-5 text-gray-400" />;
        }
    };

    const getStatusBadge = (status: EvidenceStatus) => {
        switch (status) {
            case 'uploading':
                return (
                    <span className="flex items-center text-xs font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" /> 업로드 중
                    </span>
                );
            case 'completed':
                return (
                    <span className="flex items-center text-xs font-medium text-success-green bg-green-50 px-2 py-1 rounded-full">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> 완료
                    </span>
                );
            case 'processing':
                return (
                    <span className="flex items-center text-xs font-medium text-accent bg-teal-50 px-2 py-1 rounded-full">
                        <Loader2 className="w-3 h-3 mr-1 animate-spin" /> 분석 중
                    </span>
                );
            case 'queued':
                return (
                    <span className="flex items-center text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                        <Clock className="w-3 h-3 mr-1" /> 대기 중
                    </span>
                );
            case 'review_needed':
                return (
                    <span className="flex items-center text-xs font-medium text-orange-600 bg-orange-50 px-2 py-1 rounded-full">
                        <AlertCircle className="w-3 h-3 mr-1" /> 검토 필요
                    </span>
                );
            case 'failed':
                return (
                    <span className="flex items-center text-xs font-medium text-semantic-error bg-red-50 px-2 py-1 rounded-full">
                        <AlertCircle className="w-3 h-3 mr-1" /> 실패
                    </span>
                );
            default:
                return <span className="text-xs text-gray-400">{status}</span>;
        }
    };

    return (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                    <tr>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            유형
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            파일명
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            AI 요약
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            업로드 날짜
                        </th>
                        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            상태
                        </th>
                        <th scope="col" className="relative px-6 py-3">
                            <span className="sr-only">Actions</span>
                        </th>
                    </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                    {items.map((item) => (
                        <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4 whitespace-nowrap">
                                {getTypeIcon(item.type)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                                <div className="text-sm font-medium text-gray-900">{item.filename}</div>
                                <div className="text-xs text-gray-500">{(item.size / 1024 / 1024).toFixed(2)} MB</div>
                            </td>
                            <td className="px-6 py-4">
                                <div className="text-sm text-gray-500 truncate max-w-xs">
                                    {item.summary || '-'}
                                </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {new Date(item.uploadDate).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                                {getStatusBadge(item.status)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <button className="text-gray-400 hover:text-gray-600">
                                    <MoreVertical className="w-5 h-5" />
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
