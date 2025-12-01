export type CaseStatus = 'open' | 'closed' | 'archived';
export type DraftStatus = 'not_started' | 'generating' | 'ready' | 'reviewed';

export interface Case {
    id: string;
    title: string;
    clientName: string;
    status: CaseStatus;
    evidenceCount: number;
    draftStatus: DraftStatus;
    lastUpdated: string; // ISO Date string
    tags?: string[];
}
