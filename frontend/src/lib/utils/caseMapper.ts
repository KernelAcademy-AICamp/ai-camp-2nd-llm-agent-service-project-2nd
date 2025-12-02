/**
 * Case Type Mapper
 * Converts between API (snake_case) and Frontend (camelCase) types
 *
 * Naming Convention:
 * - API types (snake_case): Defined in lib/api/*.ts (e.g., ApiCase)
 * - Frontend types (camelCase): Defined in types/*.ts (e.g., Case)
 */

import { ApiCase } from '@/lib/api/cases';
import { Case } from '@/types/case';

/**
 * Maps API Case response to Frontend Case type
 * Handles status value translation between backend and frontend conventions
 */
export function mapApiCaseToCase(apiCase: ApiCase): Case {
    return {
        id: apiCase.id,
        title: apiCase.title,
        clientName: apiCase.client_name,
        status: mapApiStatusToStatus(apiCase.status),
        evidenceCount: apiCase.evidence_count,
        draftStatus: mapApiDraftStatusToDraftStatus(apiCase.draft_status),
        lastUpdated: apiCase.updated_at,
    };
}

/**
 * Maps Frontend Case to API Case request format
 */
export function mapCaseToApiCase(frontendCase: Case): Partial<ApiCase> {
    return {
        id: frontendCase.id,
        title: frontendCase.title,
        client_name: frontendCase.clientName,
        status: mapStatusToApiStatus(frontendCase.status),
        evidence_count: frontendCase.evidenceCount,
        draft_status: mapDraftStatusToApiDraftStatus(frontendCase.draftStatus),
        updated_at: frontendCase.lastUpdated,
    };
}

// Helper functions for status mapping
function mapApiStatusToStatus(apiStatus: ApiCase['status']): Case['status'] {
    switch (apiStatus) {
        case 'active':
        case 'in_progress':
            return 'open';
        case 'closed':
            return 'closed';
        default:
            return 'open';
    }
}

function mapStatusToApiStatus(status: Case['status']): ApiCase['status'] {
    switch (status) {
        case 'open':
            return 'active';
        case 'closed':
            return 'closed';
        case 'archived':
            return 'closed';
        default:
            return 'active';
    }
}

function mapApiDraftStatusToDraftStatus(apiDraftStatus: ApiCase['draft_status']): Case['draftStatus'] {
    switch (apiDraftStatus) {
        case 'not_started':
            return 'not_started';
        case 'in_progress':
            return 'generating';
        case 'completed':
            return 'ready';
        default:
            return 'not_started';
    }
}

function mapDraftStatusToApiDraftStatus(draftStatus: Case['draftStatus']): ApiCase['draft_status'] {
    switch (draftStatus) {
        case 'not_started':
            return 'not_started';
        case 'generating':
            return 'in_progress';
        case 'ready':
        case 'reviewed':
            return 'completed';
        default:
            return 'not_started';
    }
}
