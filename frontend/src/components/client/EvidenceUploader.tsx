/**
 * EvidenceUploader Component
 * 003-role-based-ui Feature - US4 (T073)
 *
 * Component for uploading evidence files.
 * Handles file selection, upload progress, and confirmation.
 */

'use client';

import { useState, useRef, useCallback } from 'react';
import {
  requestEvidenceUpload,
  confirmEvidenceUpload,
  uploadFileToS3,
} from '@/lib/api/client-portal';

interface EvidenceUploaderProps {
  caseId: string;
  onUploadComplete?: (evidenceId: string) => void;
  onError?: (error: string) => void;
  maxSizeMB?: number;
  acceptedTypes?: string[];
  className?: string;
}

type UploadStatus = 'idle' | 'selecting' | 'uploading' | 'confirming' | 'success' | 'error';

interface UploadState {
  status: UploadStatus;
  progress: number;
  error?: string;
  file?: File;
  evidenceId?: string;
}

// File type icons
function FileIcon({ type }: { type: string }) {
  if (type.startsWith('image/')) {
    return (
      <svg className="w-8 h-8 text-[var(--color-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    );
  }
  if (type.startsWith('audio/')) {
    return (
      <svg className="w-8 h-8 text-[var(--color-success)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    );
  }
  if (type.startsWith('video/')) {
    return (
      <svg className="w-8 h-8 text-[var(--color-warning)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
    );
  }
  // Default document icon
  return (
    <svg className="w-8 h-8 text-[var(--color-secondary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

// Format file size
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export default function EvidenceUploader({
  caseId,
  onUploadComplete,
  onError,
  maxSizeMB = 100,
  acceptedTypes = ['image/*', 'audio/*', 'video/*', 'application/pdf', '.txt', '.csv'],
  className = '',
}: EvidenceUploaderProps) {
  const [state, setState] = useState<UploadState>({
    status: 'idle',
    progress: 0,
  });
  const [description, setDescription] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const maxSizeBytes = maxSizeMB * 1024 * 1024;

  const resetUpload = useCallback(() => {
    setState({ status: 'idle', progress: 0 });
    setDescription('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const validateFile = useCallback(
    (file: File): string | null => {
      if (file.size > maxSizeBytes) {
        return `파일 크기가 ${maxSizeMB}MB를 초과합니다`;
      }
      return null;
    },
    [maxSizeBytes, maxSizeMB]
  );

  const handleFileSelect = useCallback(
    (file: File) => {
      const error = validateFile(file);
      if (error) {
        setState({ status: 'error', progress: 0, error });
        onError?.(error);
        return;
      }

      setState({
        status: 'selecting',
        progress: 0,
        file,
      });
    },
    [validateFile, onError]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);

      const file = e.dataTransfer.files[0];
      if (file) {
        handleFileSelect(file);
      }
    },
    [handleFileSelect]
  );

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFileSelect(file);
      }
    },
    [handleFileSelect]
  );

  const handleUpload = async () => {
    if (!state.file) return;

    try {
      // Step 1: Request presigned URL
      setState((prev) => ({ ...prev, status: 'uploading', progress: 0 }));

      const uploadRequest = await requestEvidenceUpload(caseId, {
        file_name: state.file.name,
        file_type: state.file.type || 'application/octet-stream',
        file_size: state.file.size,
        description: description || undefined,
      });

      if (uploadRequest.error || !uploadRequest.data) {
        throw new Error(uploadRequest.error || 'Failed to get upload URL');
      }

      const { evidence_id, upload_url } = uploadRequest.data;

      // Step 2: Upload to S3
      const uploadResult = await uploadFileToS3(upload_url, state.file, (progress) => {
        setState((prev) => ({ ...prev, progress }));
      });

      if (!uploadResult.success) {
        // Cancel the upload on S3 failure
        await confirmEvidenceUpload(caseId, evidence_id, false);
        throw new Error(uploadResult.error || 'Upload failed');
      }

      // Step 3: Confirm upload
      setState((prev) => ({ ...prev, status: 'confirming', progress: 100 }));

      const confirmResult = await confirmEvidenceUpload(caseId, evidence_id, true);

      if (confirmResult.error || !confirmResult.data?.success) {
        throw new Error(confirmResult.error || 'Failed to confirm upload');
      }

      // Success
      setState({
        status: 'success',
        progress: 100,
        evidenceId: evidence_id,
      });

      onUploadComplete?.(evidence_id);

      // Reset after delay
      setTimeout(resetUpload, 3000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setState({
        status: 'error',
        progress: 0,
        error: errorMessage,
      });
      onError?.(errorMessage);
    }
  };

  return (
    <div className={`bg-white rounded-xl border border-[var(--color-border-default)] ${className}`}>
      <div className="p-4 border-b border-[var(--color-border-default)]">
        <h3 className="font-semibold text-[var(--color-text-primary)]">증거자료 업로드</h3>
        <p className="text-sm text-[var(--color-text-secondary)] mt-1">
          이미지, 오디오, 비디오, PDF 파일을 업로드할 수 있습니다 (최대 {maxSizeMB}MB)
        </p>
      </div>

      <div className="p-6">
        {/* Idle/Drag-drop area */}
        {(state.status === 'idle' || state.status === 'error') && (
          <div
            className={`
              border-2 border-dashed rounded-lg p-8 text-center transition-colors
              ${
                isDragOver
                  ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
                  : 'border-[var(--color-border-default)] hover:border-[var(--color-primary)]'
              }
            `}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragOver(true);
            }}
            onDragLeave={() => setIsDragOver(false)}
            onDrop={handleDrop}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept={acceptedTypes.join(',')}
              onChange={handleFileInputChange}
              className="hidden"
              id="evidence-file-input"
            />

            <svg
              className="w-12 h-12 mx-auto text-[var(--color-text-tertiary)] mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>

            <p className="text-[var(--color-text-primary)] mb-2">
              파일을 여기에 드래그하거나
            </p>

            <label
              htmlFor="evidence-file-input"
              className="inline-block px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg cursor-pointer hover:bg-[var(--color-primary-hover)] transition-colors"
            >
              파일 선택
            </label>

            {state.status === 'error' && state.error && (
              <p className="mt-4 text-sm text-[var(--color-error)]">{state.error}</p>
            )}
          </div>
        )}

        {/* File selected - preview */}
        {state.status === 'selecting' && state.file && (
          <div className="space-y-4">
            {/* File preview */}
            <div className="flex items-center gap-4 p-4 bg-[var(--color-bg-secondary)] rounded-lg">
              <FileIcon type={state.file.type} />
              <div className="flex-1 min-w-0">
                <p className="font-medium text-[var(--color-text-primary)] truncate">
                  {state.file.name}
                </p>
                <p className="text-sm text-[var(--color-text-secondary)]">
                  {formatFileSize(state.file.size)}
                </p>
              </div>
              <button
                type="button"
                onClick={resetUpload}
                className="p-2 text-[var(--color-text-tertiary)] hover:text-[var(--color-error)] transition-colors"
                aria-label="파일 제거"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Description input */}
            <div>
              <label
                htmlFor="evidence-description"
                className="block text-sm font-medium text-[var(--color-text-primary)] mb-1"
              >
                설명 (선택사항)
              </label>
              <input
                id="evidence-description"
                type="text"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="예: 2024년 3월 카카오톡 대화 내역"
                className="w-full px-4 py-2 border border-[var(--color-border-default)] rounded-lg focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent"
              />
            </div>

            {/* Action buttons */}
            <div className="flex gap-3">
              <button
                type="button"
                onClick={resetUpload}
                className="flex-1 px-4 py-2 border border-[var(--color-border-default)] rounded-lg text-[var(--color-text-primary)] hover:bg-[var(--color-bg-secondary)] transition-colors"
              >
                취소
              </button>
              <button
                type="button"
                onClick={handleUpload}
                className="flex-1 px-4 py-2 bg-[var(--color-primary)] text-white rounded-lg hover:bg-[var(--color-primary-hover)] transition-colors"
              >
                업로드
              </button>
            </div>
          </div>
        )}

        {/* Uploading */}
        {(state.status === 'uploading' || state.status === 'confirming') && (
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-4 bg-[var(--color-bg-secondary)] rounded-lg">
              {state.file && <FileIcon type={state.file.type} />}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-[var(--color-text-primary)] truncate">
                  {state.file?.name}
                </p>
                <p className="text-sm text-[var(--color-text-secondary)]">
                  {state.status === 'confirming' ? '업로드 확인 중...' : '업로드 중...'}
                </p>
              </div>
            </div>

            {/* Progress bar */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-[var(--color-text-secondary)]">진행률</span>
                <span className="text-sm font-medium text-[var(--color-primary)]">
                  {state.progress}%
                </span>
              </div>
              <div className="h-2 bg-[var(--color-neutral-200)] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[var(--color-primary)] rounded-full transition-all duration-300"
                  style={{ width: `${state.progress}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {/* Success */}
        {state.status === 'success' && (
          <div className="text-center py-8">
            <div className="w-16 h-16 mx-auto mb-4 bg-[var(--color-success-light)] rounded-full flex items-center justify-center">
              <svg
                className="w-8 h-8 text-[var(--color-success)]"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <p className="text-lg font-semibold text-[var(--color-text-primary)]">
              업로드 완료!
            </p>
            <p className="text-sm text-[var(--color-text-secondary)] mt-1">
              AI가 파일을 분석하고 있습니다
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
