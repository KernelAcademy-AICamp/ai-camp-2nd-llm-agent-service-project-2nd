export type DraftDownloadFormat = 'docx' | 'hwp';

export const downloadDraftAsDocx = async (
    draftText: string,
    caseId: string,
    format: DraftDownloadFormat = 'docx',
): Promise<void> => {
    const response = await fetch(`/api/cases/${caseId}/draft/convert?format=${format}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: draftText }),
    });

    if (!response.ok) {
        throw new Error('Draft conversion failed');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `draft_${caseId}.${format}`;
    document.body.appendChild(anchor);

    try {
        anchor.click();
    } catch {
        // Ignore click errors in non-browser environments (e.g., tests)
    }

    URL.revokeObjectURL(url);
    document.body.removeChild(anchor);
};
