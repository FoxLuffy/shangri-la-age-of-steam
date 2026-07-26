// CR5: render dynamic events as concise, in-world highlights instead of raw JSON dumps.

type EventObj = Record<string, unknown>;

function humanize(id: string): string {
  return id
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
}

/**
 * Turn an event (string or object) into a short, human-readable, in-world line.
 * Returns null when the event has nothing meaningful to show — callers should skip it
 * rather than dump raw data (which is what the bug report was about).
 */
export function formatEvent(ev: unknown): string | null {
  if (ev == null) return null;

  if (typeof ev === 'string') {
    const t = ev.trim();
    return t || null;
  }

  if (typeof ev === 'object') {
    const o = ev as EventObj;

    // Prefer an explicit human-readable field.
    for (const key of ['description', 'text', 'event_text', 'message', 'summary']) {
      const v = o[key];
      if (typeof v === 'string' && v.trim()) return v.trim();
    }

    // Known structured events → a curated in-world phrase.
    const npc = o.npc as EventObj | undefined;
    const npcName = npc && typeof npc.name === 'string' ? (npc.name as string) : undefined;
    if (o.type === 'npc_state_change' && npcName) {
      const hp = typeof npc?.hp === 'number' ? (npc?.hp as number) : undefined;
      if (hp === 0) return `${npcName} has fallen.`;
      return `${npcName} reacts.`;
    }

    // Named event without a description → show the humanized name only.
    if (typeof o.name === 'string' && (o.name as string).trim()) return (o.name as string).trim();
    if (typeof o.type === 'string' && (o.type as string).trim()) return humanize(o.type as string);

    // Nothing meaningful — do NOT dump raw JSON.
    return null;
  }

  return null;
}
