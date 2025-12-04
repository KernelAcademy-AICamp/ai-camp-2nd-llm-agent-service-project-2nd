/**
 * FieldRecorder Component
 * 003-role-based-ui Feature - US5 (T100)
 *
 * Component for recording field observations during detective work.
 * Includes record type selection, content input, photo attachment, and GPS.
 */

'use client';

import { useState, useCallback, useRef } from 'react';
import { createFieldRecord, type FieldRecordRequest } from '@/lib/api/detective-portal';
import GPSTracker from './GPSTracker';

type RecordType = 'observation' | 'photo' | 'note' | 'video' | 'audio';

interface LocationData {
  latitude: number;
  longitude: number;
  accuracy?: number;
  timestamp?: number;
}

interface FieldRecorderProps {
  caseId: string;
  onRecordSaved?: (recordId: string) => void;
  onError?: (error: string) => void;
  className?: string;
}

const RECORD_TYPES: { type: RecordType; label: string; icon: React.ReactNode }[] = [
  {
    type: 'observation',
    label: '관찰 기록',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
      </svg>
    ),
  },
  {
    type: 'photo',
    label: '사진 기록',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    type: 'note',
    label: '메모',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
  },
];

export default function FieldRecorder({
  caseId,
  onRecordSaved,
  onError,
  className = '',
}: FieldRecorderProps) {
  const [recordType, setRecordType] = useState<RecordType | null>(null);
  const [content, setContent] = useState('');
  const [location, setLocation] = useState<LocationData | null>(null);
  const [photo, setPhoto] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);
  const [errors, setErrors] = useState<{ type?: string; content?: string }>({});

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleLocationSave = useCallback((locationData: LocationData) => {
    setLocation(locationData);
  }, []);

  const handlePhotoSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setPhoto(file);
    }
  }, []);

  const handleRemovePhoto = useCallback(() => {
    setPhoto(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  const validate = useCallback((): boolean => {
    const newErrors: { type?: string; content?: string } = {};

    if (!recordType) {
      newErrors.type = '기록 유형을 선택해 주세요.';
    }
    if (!content.trim()) {
      newErrors.content = '내용을 입력해 주세요.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [recordType, content]);

  const handleSubmit = useCallback(async () => {
    if (!validate()) {
      return;
    }

    setIsSubmitting(true);
    setSuccess(false);

    try {
      const requestData: FieldRecordRequest = {
        record_type: recordType!,
        content: content.trim(),
      };

      if (location) {
        requestData.gps_lat = location.latitude;
        requestData.gps_lng = location.longitude;
      }

      const { data, error } = await createFieldRecord(caseId, requestData);

      if (error) {
        setErrors({ content: '오류가 발생했습니다. 다시 시도해 주세요.' });
        onError?.(error);
        return;
      }

      if (data?.success) {
        setSuccess(true);
        onRecordSaved?.(data.record_id);

        // Reset form
        setRecordType(null);
        setContent('');
        setLocation(null);
        setPhoto(null);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  }, [caseId, recordType, content, location, validate, onRecordSaved, onError]);

  return (
    <div className={`p-6 bg-[var(--color-bg-secondary)] rounded-lg ${className}`}>
      <h3 className="text-lg font-semibold mb-6">현장 기록</h3>

      {/* Record Type Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
          기록 유형
        </label>
        <div className="flex flex-wrap gap-2">
          {RECORD_TYPES.map(({ type, label, icon }) => (
            <button
              key={type}
              type="button"
              onClick={() => setRecordType(type)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg border min-h-[44px]
                transition-colors
                ${
                  recordType === type
                    ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
                    : 'bg-white border-[var(--color-border)] text-[var(--color-text-primary)] hover:border-[var(--color-primary)]'
                }
              `}
            >
              {icon}
              <span>{label}</span>
            </button>
          ))}
        </div>
        {errors.type && (
          <p className="mt-1 text-sm text-[var(--color-error)]">{errors.type}</p>
        )}
      </div>

      {/* Content Input */}
      <div className="mb-6">
        <label
          htmlFor="record-content"
          className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2"
        >
          내용
        </label>
        <textarea
          id="record-content"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="관찰 내용이나 기록을 입력하세요..."
          rows={4}
          className="w-full px-4 py-3 border border-[var(--color-border)] rounded-lg
            focus:outline-none focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent
            resize-none"
        />
        <div className="flex justify-between mt-1">
          {errors.content ? (
            <p className="text-sm text-[var(--color-error)]">{errors.content}</p>
          ) : (
            <span />
          )}
          <span className="text-sm text-[var(--color-text-secondary)]">
            {content.length}자
          </span>
        </div>
      </div>

      {/* Photo Attachment */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-2">
          사진 추가
        </label>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handlePhotoSelect}
          className="hidden"
          id="photo-input"
        />
        {!photo ? (
          <label
            htmlFor="photo-input"
            className="flex items-center justify-center w-full h-32 border-2 border-dashed
              border-[var(--color-border)] rounded-lg cursor-pointer
              hover:border-[var(--color-primary)] transition-colors"
          >
            <div className="flex flex-col items-center text-[var(--color-text-secondary)]">
              <svg className="w-8 h-8 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <span>클릭하여 사진 선택</span>
            </div>
          </label>
        ) : (
          <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-[var(--color-border)]">
            <div className="flex items-center gap-3">
              <svg className="w-6 h-6 text-[var(--color-primary)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span className="truncate max-w-[200px]">{photo.name}</span>
            </div>
            <button
              type="button"
              onClick={handleRemovePhoto}
              className="p-2 text-[var(--color-error)] hover:bg-red-50 rounded-lg"
              aria-label="사진 제거"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* GPS Tracker */}
      <div className="mb-6">
        <GPSTracker
          onLocationSave={handleLocationSave}
          onError={onError}
        />
        {location && (
          <div className="mt-2 p-2 bg-green-50 text-green-700 rounded-lg flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span>위치 저장됨: {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}</span>
          </div>
        )}
      </div>

      {/* Submit Button */}
      <button
        type="button"
        onClick={handleSubmit}
        disabled={isSubmitting}
        className="w-full px-4 py-3 bg-[var(--color-primary)] text-white rounded-lg
          font-medium hover:bg-[var(--color-primary-hover)]
          disabled:opacity-50 disabled:cursor-not-allowed
          min-h-[44px]"
      >
        {isSubmitting ? '저장 중...' : '기록 저장'}
      </button>

      {/* Success Message */}
      {success && (
        <div className="mt-4 p-3 bg-green-50 text-green-700 rounded-lg">
          저장 완료! 현장 기록이 성공적으로 저장되었습니다.
        </div>
      )}
    </div>
  );
}
