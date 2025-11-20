import { useState } from 'react';
import { Evidence, EvidenceStatus } from '@/types/evidence';
import { FileText, Image, Mic, Video, File, MoreVertical, CheckCircle2, Clock, AlertCircle, Loader2, Filter } from 'lucide-react';

interface EvidenceTableProps {
    items: Evidence[];
}

export default function EvidenceTable({ items }: EvidenceTableProps) {
    const [typeFilter, setTypeFilter] = useState<string>('all');
    const [dateFilter, setDateFilter] = useState<string>('all');

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

    // 필터링 로직
    const filteredItems = items.filter(item => {
        // 유형 필터
        if (typeFilter !== 'all' && item.type !== typeFilter) {
            return false;
        }

        // 날짜 필터
        if (dateFilter !== 'all') {
            const itemDate = new Date(item.uploadDate);
            const now = new Date();
            const daysDiff = Math.floor((now.getTime() - itemDate.getTime()) / (1000 * 60 * 60 * 24));

            if (dateFilter === 'today' && daysDiff !== 0) return false;
            if (dateFilter === 'week' && daysDiff > 7) return false;
            if (dateFilter === 'month' && daysDiff > 30) return false;
        }

        return true;
    });

    return (
        <div className="space-y-4">
            {/* 필터 컨트롤 */}
            <div className="flex items-center space-x-4 bg-white p-4 rounded-lg border border-gray-200">
                <Filter className="w-5 h-5 text-gray-400" />

                <div className="flex items-center space-x-2">
                    <label htmlFor="type-filter" className="text-sm font-medium text-gray-700">
                        유형 필터:
                    </label>
                    <select
                        id="type-filter"
                        value={typeFilter}
                        onChange={(e) => setTypeFilter(e.target.value)}
                        className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-accent"
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
                    <label htmlFor="date-filter" className="text-sm font-medium text-gray-700">
                        날짜 필터:
                    </label>
                    <select
                        id="date-filter"
                        value={dateFilter}
                        onChange={(e) => setDateFilter(e.target.value)}
                        className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                    >
                        <option value="all">전체</option>
                        <option value="today">오늘</option>
                        <option value="week">최근 7일</option>
                        <option value="month">최근 30일</option>
                    </select>
                </div>

                <div className="text-sm text-gray-500">
                    {filteredItems.length}개 / 전체 {items.length}개
                </div>
            </div>

            {/* 테이블 */}
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
                    <tbody className="divide-y divide-gray-200">
                        {filteredItems.map((item, index) => {
                            const zebraBackground = index % 2 === 0 ? 'bg-white' : 'bg-gray-50/70';
                            return (
                            <tr key={item.id} className={`group transition-colors ${zebraBackground} hover:bg-accent/5`}>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    {getTypeIcon(item.type)}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="text-sm font-medium text-gray-900">{item.filename}</div>
                                    <div className="text-xs text-gray-500">{(item.size / 1024 / 1024).toFixed(2)} MB</div>
                                    <div className="text-[11px] text-gray-400 hidden group-hover:block mt-1">
                                        클릭하여 상세 · 타임라인 연결 옵션 보기
                                    </div>
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
                                    <button
                                        className="text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity"
                                        aria-label={`${item.filename} 추가 작업`}
                                    >
                                        <MoreVertical className="w-5 h-5" />
                                    </button>
                                </td>
                            </tr>
                        )})}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
