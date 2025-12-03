/**
 * Evidence Mapper
 * Converts API Evidence (snake_case) to UI Evidence (camelCase)
 */

import { Evidence as ApiEvidence } from '@/lib/api/evidence';
import { Evidence, EvidenceStatus } from '@/types/evidence';

/**
 * Map API status to UI status
 * API may return different status values than the UI expects
 */
function mapApiStatusToStatus(apiStatus?: string): EvidenceStatus {
    const statusMap: Record<string, EvidenceStatus> = {
        'pending': 'queued',
        'queued': 'queued',
        'processing': 'processing',
        'completed': 'completed',
        'failed': 'failed',
        'review_needed': 'review_needed',
    };
    return statusMap[apiStatus || 'queued'] || 'queued';
}

/**
 * Convert API Evidence to UI Evidence
 */
export function mapApiEvidenceToEvidence(apiEvidence: ApiEvidence): Evidence {
    return {
        id: apiEvidence.id,
        caseId: apiEvidence.case_id,
        filename: apiEvidence.filename,
        type: apiEvidence.type,
        status: mapApiStatusToStatus((apiEvidence as unknown as { status?: string }).status),
        uploadDate: apiEvidence.created_at,
        summary: apiEvidence.ai_summary,
        size: 0, // Size not provided by API, will need to be fetched separately if needed
        speaker: apiEvidence.speaker as Evidence['speaker'],
        labels: apiEvidence.labels,
        timestamp: apiEvidence.timestamp,
        s3Key: apiEvidence.s3_key,
    };
}

/**
 * Convert array of API Evidence to UI Evidence array
 */
export function mapApiEvidenceListToEvidence(apiEvidenceList: ApiEvidence[]): Evidence[] {
    return apiEvidenceList.map(mapApiEvidenceToEvidence);
}
