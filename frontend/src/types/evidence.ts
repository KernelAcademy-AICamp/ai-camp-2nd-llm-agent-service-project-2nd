export type EvidenceType = 'text' | 'image' | 'audio' | 'video' | 'pdf';
export type EvidenceStatus = 'uploading' | 'queued' | 'processing' | 'review_needed' | 'completed' | 'failed';
export type SpeakerType = '원고' | '피고' | '제3자' | 'unknown';

export interface Evidence {
    id: string;
    caseId: string;
    filename: string;
    type: EvidenceType;
    status: EvidenceStatus;
    uploadDate: string; // ISO Date string
    summary?: string;
    size: number;
    downloadUrl?: string;
    content?: string; // STT/OCR 원문 텍스트

    // AI Worker generated fields (optional - populated after processing)
    speaker?: SpeakerType;
    labels?: string[]; // AI-generated labels (e.g., '폭언', '불륜', '유책사유')
    timestamp?: string; // ISO Date string - when the evidence was created/recorded
    s3Key?: string; // S3 storage path
    qdrantId?: string; // Vector store ID for RAG
}
