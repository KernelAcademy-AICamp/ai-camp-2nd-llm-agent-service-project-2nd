export type DraftSaveReason = 'auto' | 'manual' | 'ai';

export interface DraftVersionSnapshot {
  id: string;
  content: string;
  savedAt: string;
  reason: DraftSaveReason;
}

export interface DraftEditorState {
  content: string;
  lastSavedAt: string | null;
  history: DraftVersionSnapshot[];
}

const STORAGE_PREFIX = 'leh:draft-editor:v1:';

const getStorageKey = (caseId: string) => `${STORAGE_PREFIX}${caseId}`;

export function loadDraftState(caseId: string): DraftEditorState | null {
  if (typeof window === 'undefined') {
    return null;
  }

  const raw = window.localStorage.getItem(getStorageKey(caseId));
  if (!raw) {
    return null;
  }

  try {
    const parsed = JSON.parse(raw) as DraftEditorState;
    return {
      content: parsed.content || '',
      lastSavedAt: parsed.lastSavedAt || null,
      history: Array.isArray(parsed.history) ? parsed.history : [],
    };
  } catch {
    return null;
  }
}

export function persistDraftState(caseId: string, state: DraftEditorState) {
  if (typeof window === 'undefined') {
    return;
  }

  const payload: DraftEditorState = {
    content: state.content || '',
    lastSavedAt: state.lastSavedAt || null,
    history: state.history || [],
  };

  window.localStorage.setItem(getStorageKey(caseId), JSON.stringify(payload));
}

export function clearDraftState(caseId: string) {
  if (typeof window === 'undefined') {
    return;
  }
  window.localStorage.removeItem(getStorageKey(caseId));
}
