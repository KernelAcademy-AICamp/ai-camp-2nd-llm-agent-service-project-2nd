import { Evidence } from '@/types/evidence';
import { Clock, FileText, Image, Mic, Video, File } from 'lucide-react';

const dateFormatter = new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
});

interface TimelineProps {
    items: Evidence[];
    onSelect: (id: string) => void;
}

export default function Timeline({ items, onSelect }: TimelineProps) {
    if (items.length === 0) {
        return (
            <div className="text-center py-10 text-gray-500">
                표시할 타임라인이 없습니다.
            </div>
        );
    }

    // Sort by date (newest first or oldest first? Usually timeline is chronological, so oldest top? 
    // Or reverse chronological? Let's do newest first for now as it's common in feeds, 
    // but legal timelines might be chronological. Let's stick to the test expectation.
    // The test just checks presence, not order strictly, but I'll sort Descending (newest top) for now.
    const sortedItems = [...items].sort((a, b) =>
        new Date(b.uploadDate).getTime() - new Date(a.uploadDate).getTime()
    );

    const getTypeIcon = (type: string) => {
        switch (type) {
            case 'text': return <FileText className="w-4 h-4" />;
            case 'image': return <Image className="w-4 h-4" />;
            case 'audio': return <Mic className="w-4 h-4" />;
            case 'video': return <Video className="w-4 h-4" />;
            default: return <File className="w-4 h-4" />;
        }
    };

    return (
        <div className="relative border-l-2 border-gray-200 ml-3 space-y-8 py-4">
            {sortedItems.map((item) => (
                <div key={item.id} className="relative pl-8 group">
                    {/* Dot on the line */}
                    <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-white border-2 border-gray-300 group-hover:border-accent transition-colors"></div>

                    <div
                        onClick={() => onSelect(item.id)}
                        className="cursor-pointer hover:bg-gray-50 p-3 rounded-lg transition-colors -mt-2"
                    >
                        <div className="flex items-center text-sm text-gray-500 mb-1">
                            <Clock className="w-3 h-3 mr-1" />
                            <time>{dateFormatter.format(new Date(item.uploadDate))}</time>
                        </div>

                        <h4 className="text-base font-medium text-gray-900 mb-1">
                            {item.summary || item.filename}
                        </h4>

                        <div className="flex items-center text-xs text-gray-400">
                            <span className="mr-2 flex items-center">
                                {getTypeIcon(item.type)}
                                <span className="ml-1 capitalize">{item.type}</span>
                            </span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}
