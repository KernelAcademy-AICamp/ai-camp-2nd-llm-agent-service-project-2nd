import { useState, useCallback } from 'react';
import { UploadCloud, File } from 'lucide-react';

interface EvidenceUploadProps {
    onUpload: (files: File[]) => void;
}

export default function EvidenceUpload({ onUpload }: EvidenceUploadProps) {
    const [isDragging, setIsDragging] = useState(false);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);

        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            onUpload(Array.from(e.dataTransfer.files));
        }
    }, [onUpload]);

    const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            onUpload(Array.from(e.target.files));
        }
    }, [onUpload]);

    return (
        <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`
        border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors duration-200
        ${isDragging
                    ? 'border-accent bg-accent/5'
                    : 'border-gray-300 hover:border-accent hover:bg-gray-50'
                }
      `}
        >
            <input
                type="file"
                multiple
                className="hidden"
                id="file-upload"
                onChange={handleFileSelect}
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                <div className={`p-4 rounded-full mb-4 ${isDragging ? 'bg-accent/10' : 'bg-gray-100'}`}>
                    <UploadCloud className={`w-8 h-8 ${isDragging ? 'text-accent' : 'text-gray-400'}`} />
                </div>
                <h3 className="text-lg font-medium text-gray-900">
                    파일을 끌어다 놓거나 클릭하여 업로드
                </h3>
                <p className="mt-1 text-sm text-gray-500">
                    PDF, 이미지, 음성, 텍스트 파일 지원
                </p>
            </label>
        </div>
    );
}
