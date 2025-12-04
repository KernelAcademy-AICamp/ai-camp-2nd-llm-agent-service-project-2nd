export type DraftDownloadFormat = 'docx' | 'pdf' | 'hwp';

export interface DownloadResult {
    success: boolean;
    filename?: string;
    error?: string;
}

export const downloadDraftAsDocx = async (
    draftText: string,
    caseId: string,
    format: DraftDownloadFormat = 'docx',
): Promise<DownloadResult> => {
    try {
        const response = await fetch(`/api/cases/${caseId}/draft/convert?format=${format}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: draftText }),
        });

        if (!response.ok) {
            const errorText = await response.text().catch(() => 'Unknown error');
            return {
                success: false,
                error: `변환 실패: ${response.status} - ${errorText}`,
            };
        }

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const filename = `draft_${caseId}.${format}`;
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = filename;
        document.body.appendChild(anchor);

        try {
            anchor.click();
        } catch {
            // Ignore click errors in non-browser environments (e.g., tests)
        }

        URL.revokeObjectURL(url);
        document.body.removeChild(anchor);

        return { success: true, filename };
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : '네트워크 오류가 발생했습니다.',
        };
    }
};

/**
 * Export draft from backend API with retries
 */
export const exportDraft = async (
    caseId: string,
    format: DraftDownloadFormat = 'docx',
    maxRetries: number = 2,
): Promise<DownloadResult> => {
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || '';
    let lastError: string | undefined;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch(
                `${apiBaseUrl}/cases/${caseId}/draft-export?format=${format}`,
                {
                    method: 'GET',
                    credentials: 'include',
                }
            );

            if (!response.ok) {
                lastError = `서버 오류: ${response.status}`;
                if (response.status >= 500 && attempt < maxRetries) {
                    // Retry on server errors
                    await new Promise((resolve) => setTimeout(resolve, 1000 * (attempt + 1)));
                    continue;
                }
                return { success: false, error: lastError };
            }

            const contentDisposition = response.headers.get('Content-Disposition');
            const filenameMatch = contentDisposition?.match(/filename="?([^";\n]+)"?/);
            const filename = filenameMatch?.[1] || `draft_${caseId}.${format}`;

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const anchor = document.createElement('a');
            anchor.href = url;
            anchor.download = filename;
            document.body.appendChild(anchor);

            try {
                anchor.click();
            } catch {
                // Ignore click errors in non-browser environments
            }

            URL.revokeObjectURL(url);
            document.body.removeChild(anchor);

            return { success: true, filename };
        } catch (error) {
            lastError = error instanceof Error ? error.message : '네트워크 오류';
            if (attempt < maxRetries) {
                await new Promise((resolve) => setTimeout(resolve, 1000 * (attempt + 1)));
                continue;
            }
        }
    }

    return { success: false, error: lastError || '다운로드 실패' };
};
