export type EvidenceType = 'text' | 'image' | 'audio' | 'video' | 'pdf';
export type EvidenceStatus = 'uploading' | 'queued' | 'processing' | 'review_needed' | 'completed' | 'failed';

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
}
