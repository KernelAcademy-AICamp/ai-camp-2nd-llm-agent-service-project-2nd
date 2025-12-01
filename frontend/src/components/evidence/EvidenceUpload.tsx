'use client';

import { useState, useCallback, useRef } from 'react';
import { UploadCloud } from 'lucide-react';

interface EvidenceUploadProps {
  onUpload: (files: File[]) => void;
  disabled?: boolean;
}

export default function EvidenceUpload({ onUpload, disabled = false }: EvidenceUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      if (disabled) return;

      if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
        onUpload(Array.from(e.dataTransfer.files));
      }
    },
    [onUpload, disabled]
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (disabled) return;
      if (e.target.files && e.target.files.length > 0) {
        onUpload(Array.from(e.target.files));
      }
    },
    [onUpload, disabled]
  );

  // Keyboard accessibility: allow Enter/Space to open file dialog
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      inputRef.current?.click();
    }
  }, [disabled]);

  const handleClick = useCallback(() => {
    if (!disabled) {
      inputRef.current?.click();
    }
  }, [disabled]);

  return (
    <div
      role="button"
      tabIndex={disabled ? -1 : 0}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onKeyDown={handleKeyDown}
      onClick={handleClick}
      aria-label="파일 업로드 영역. 클릭하거나 파일을 끌어다 놓으세요."
      aria-disabled={disabled}
      className={`
        border-2 border-dashed rounded-lg p-10 text-center
        transition-colors duration-200
        focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
        ${disabled
          ? 'border-neutral-200 bg-neutral-50 cursor-not-allowed opacity-60'
          : isDragging
            ? 'border-primary bg-primary-light cursor-pointer'
            : 'border-neutral-300 hover:border-primary hover:bg-neutral-50 cursor-pointer'
        }
      `}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        disabled={disabled}
        className="sr-only"
        id="file-upload"
        aria-label="파일을 끌어다 놓거나 클릭하여 업로드"
        onChange={handleFileSelect}
        aria-describedby="upload-description"
      />

      <div className="flex flex-col items-center">
        <div
          className={`p-4 rounded-full mb-4 transition-colors ${
            isDragging ? 'bg-primary-light' : 'bg-neutral-100'
          }`}
        >
          <UploadCloud
            className={`w-8 h-8 transition-colors ${
              isDragging ? 'text-primary' : 'text-neutral-400'
            }`}
            aria-hidden="true"
          />
        </div>

        <h3 className="text-lg font-medium text-neutral-900">
          파일을 끌어다 놓거나 클릭하여 업로드
        </h3>

        <p id="upload-description" className="mt-1 text-sm text-neutral-500">
          PDF, 이미지, 음성, 텍스트 파일 지원
        </p>
      </div>
    </div>
  );
}
