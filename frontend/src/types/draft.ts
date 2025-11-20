export interface DraftCitation {
    evidenceId: string;
    title: string;
    quote: string;
}

export interface DraftPreviewState {
    draftText: string;
    citations: DraftCitation[];
}

export interface DraftTemplate {
    id: string;
    name: string;
    updatedAt: string;
}
