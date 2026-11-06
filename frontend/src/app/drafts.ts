/**
 * Local drafts of unsent answers and code, kept per learner and item so work survives session
 * expiry and network loss (FR-045b). localStorage may be unavailable: every access is guarded.
 */
const PREFIX = "academy:draft:";

function key(learnerId: string, item: string): string {
  return `${PREFIX}${learnerId}:${item}`;
}

export function saveDraft<T>(learnerId: string, item: string, value: T): void {
  try {
    localStorage.setItem(key(learnerId, item), JSON.stringify({ savedAt: Date.now(), value }));
  } catch {
    /* storage unavailable or full: drafts are a convenience only */
  }
}

export function loadDraft<T>(learnerId: string, item: string): T | undefined {
  try {
    const raw = localStorage.getItem(key(learnerId, item));
    return raw ? (JSON.parse(raw) as { value: T }).value : undefined;
  } catch {
    return undefined;
  }
}

export function clearDraft(learnerId: string, item: string): void {
  try {
    localStorage.removeItem(key(learnerId, item));
  } catch {
    /* ignore */
  }
}

/** Replays every pending draft for a learner through `send`; drafts are cleared on success. */
export async function replayDrafts(
  learnerId: string,
  send: (item: string, value: unknown) => Promise<void>,
): Promise<void> {
  let keys: string[] = [];
  try {
    keys = Object.keys(localStorage).filter((k) => k.startsWith(`${PREFIX}${learnerId}:`));
  } catch {
    return;
  }
  for (const k of keys) {
    const item = k.slice(`${PREFIX}${learnerId}:`.length);
    const value = loadDraft<unknown>(learnerId, item);
    try {
      await send(item, value);
      clearDraft(learnerId, item);
    } catch {
      /* keep the draft for the next attempt */
    }
  }
}
