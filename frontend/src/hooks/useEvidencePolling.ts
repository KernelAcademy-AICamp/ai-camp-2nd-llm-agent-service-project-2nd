/**
 * useEvidencePolling Hook
 * Real-time evidence status updates using polling
 *
 * Responsibilities:
 * - Poll evidence status at configurable intervals
 * - Auto-stop polling when all items are in final state
 * - Handle error states and retry logic
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { Evidence, EvidenceStatus, Article840Category } from '@/types/evidence';
import { getEvidence, Evidence as ApiEvidence } from '@/lib/api/evidence';

// Final states that don't need polling
const FINAL_STATES: EvidenceStatus[] = ['completed', 'failed', 'review_needed'];

interface UseEvidencePollingOptions {
  /** Polling interval in milliseconds (default: 5000) */
  interval?: number;
  /** Maximum retry count for failed items (default: 3) */
  maxRetries?: number;
  /** Enable polling (default: true) */
  enabled?: boolean;
  /** Callback when evidence status changes */
  onStatusChange?: (evidence: Evidence, previousStatus: EvidenceStatus) => void;
}

interface UseEvidencePollingResult {
  /** Current evidence list */
  evidence: Evidence[];
  /** Is currently polling */
  isPolling: boolean;
  /** Any items in processing state */
  hasProcessingItems: boolean;
  /** Error from last poll */
  error: Error | null;
  /** Manually trigger a refresh */
  refresh: () => Promise<void>;
  /** Start polling */
  startPolling: () => void;
  /** Stop polling */
  stopPolling: () => void;
}

export function useEvidencePolling(
  caseId: string,
  initialEvidence: Evidence[] = [],
  options: UseEvidencePollingOptions = {}
): UseEvidencePollingResult {
  const {
    interval = 5000,
    enabled = true,
    onStatusChange,
  } = options;

  const [evidence, setEvidence] = useState<Evidence[]>(initialEvidence);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  // Refs for stable callbacks
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const previousEvidenceRef = useRef<Map<string, EvidenceStatus>>(new Map());

  // Check if any items need polling
  const hasProcessingItems = evidence.some(
    (e) => !FINAL_STATES.includes(e.status)
  );

  // Update previous status map
  useEffect(() => {
    const statusMap = new Map<string, EvidenceStatus>();
    evidence.forEach((e) => statusMap.set(e.id, e.status));
    previousEvidenceRef.current = statusMap;
  }, [evidence]);

  // Fetch latest evidence
  const fetchEvidence = useCallback(async () => {
    if (!caseId) return;

    try {
      const response = await getEvidence(caseId);
      if (response.data?.evidence) {
        const newEvidence = response.data.evidence.map((e: ApiEvidence) => mapApiToEvidence(e));

        // Check for status changes and trigger callbacks
        if (onStatusChange) {
          newEvidence.forEach((e) => {
            const prevStatus = previousEvidenceRef.current.get(e.id);
            if (prevStatus && prevStatus !== e.status) {
              onStatusChange(e, prevStatus);
            }
          });
        }

        setEvidence(newEvidence);
        setError(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch evidence'));
    }
  }, [caseId, onStatusChange]);

  // Start polling
  const startPolling = useCallback(() => {
    if (intervalRef.current) return;

    setIsPolling(true);
    intervalRef.current = setInterval(fetchEvidence, interval);
  }, [fetchEvidence, interval]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  // Auto-start/stop polling based on processing items
  useEffect(() => {
    if (!enabled) {
      stopPolling();
      return;
    }

    if (hasProcessingItems) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => stopPolling();
  }, [enabled, hasProcessingItems, startPolling, stopPolling]);

  // Update evidence when initialEvidence changes
  useEffect(() => {
    setEvidence(initialEvidence);
  }, [initialEvidence]);

  // Manual refresh
  const refresh = useCallback(async () => {
    await fetchEvidence();
  }, [fetchEvidence]);

  return {
    evidence,
    isPolling,
    hasProcessingItems,
    error,
    refresh,
    startPolling,
    stopPolling,
  };
}

// Helper to map API response to Evidence type
function mapApiToEvidence(apiEvidence: ApiEvidence): Evidence {
  return {
    id: apiEvidence.id,
    caseId: apiEvidence.case_id,
    filename: apiEvidence.filename,
    type: apiEvidence.type,
    status: mapApiStatus(apiEvidence.status),
    uploadDate: apiEvidence.created_at,
    summary: apiEvidence.ai_summary,
    size: apiEvidence.size,
    speaker: apiEvidence.speaker as Evidence['speaker'],
    labels: apiEvidence.labels,
    s3Key: apiEvidence.s3_key,
    article840Tags: apiEvidence.article_840_tags
      ? {
          categories: apiEvidence.article_840_tags.categories as Article840Category[],
          confidence: apiEvidence.article_840_tags.confidence,
          matchedKeywords: apiEvidence.article_840_tags.matched_keywords,
        }
      : undefined,
  };
}

// Map API status to frontend status
function mapApiStatus(status: string): EvidenceStatus {
  const statusMap: Record<string, EvidenceStatus> = {
    pending: 'queued',
    processing: 'processing',
    processed: 'completed',
    completed: 'completed',
    failed: 'failed',
    queued: 'queued',
    uploading: 'uploading',
    review_needed: 'review_needed',
  };
  return statusMap[status] || 'queued';
}

/**
 * Hook for polling a single evidence item
 */
export function useSingleEvidencePolling(
  evidenceId: string,
  initialEvidence: Evidence | null,
  options: Omit<UseEvidencePollingOptions, 'onStatusChange'> & {
    onStatusChange?: (evidence: Evidence, previousStatus: EvidenceStatus) => void;
  } = {}
) {
  const [evidence, setEvidence] = useState<Evidence | null>(initialEvidence);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const { interval = 5000, enabled = true, onStatusChange } = options;
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const previousStatusRef = useRef<EvidenceStatus | null>(null);

  const isProcessing = evidence && !FINAL_STATES.includes(evidence.status);

  // Update previous status
  useEffect(() => {
    if (evidence) {
      previousStatusRef.current = evidence.status;
    }
  }, [evidence]);

  const fetchEvidence = useCallback(async () => {
    if (!evidenceId) return;

    try {
      const { getEvidenceById } = await import('@/lib/api/evidence');
      const response = await getEvidenceById(evidenceId);

      if (response.data) {
        const newEvidence = mapApiToEvidence(response.data);

        // Check for status change
        if (
          onStatusChange &&
          previousStatusRef.current &&
          previousStatusRef.current !== newEvidence.status
        ) {
          onStatusChange(newEvidence, previousStatusRef.current);
        }

        setEvidence(newEvidence);
        setError(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch evidence'));
    }
  }, [evidenceId, onStatusChange]);

  const startPolling = useCallback(() => {
    if (intervalRef.current) return;
    setIsPolling(true);
    intervalRef.current = setInterval(fetchEvidence, interval);
  }, [fetchEvidence, interval]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  useEffect(() => {
    if (!enabled) {
      stopPolling();
      return;
    }

    if (isProcessing) {
      startPolling();
    } else {
      stopPolling();
    }

    return () => stopPolling();
  }, [enabled, isProcessing, startPolling, stopPolling]);

  useEffect(() => {
    setEvidence(initialEvidence);
  }, [initialEvidence]);

  const refresh = useCallback(async () => {
    await fetchEvidence();
  }, [fetchEvidence]);

  return {
    evidence,
    isPolling,
    isProcessing: !!isProcessing,
    error,
    refresh,
    startPolling,
    stopPolling,
  };
}
