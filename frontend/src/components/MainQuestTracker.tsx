import { useEffect, useState } from 'react';
import { fetchMainQuest } from '../api';
import type { MainQuestProgress } from '../api';

export default function MainQuestTracker({ characterId }: { characterId: number }) {
  const [mq, setMq] = useState<MainQuestProgress | null>(null);

  useEffect(() => {
    let alive = true;
    fetchMainQuest(characterId)
      .then((d) => { if (alive) setMq(d); })
      .catch(() => { if (alive) setMq(null); });
    return () => { alive = false; };
  }, [characterId]);

  if (!mq) return null;

  const done = mq.status === 'completed';
  return (
    <div className="text-xs border border-amber-900/40 bg-slate-900/60 rounded px-3 py-2 text-amber-200">
      <div className="uppercase tracking-wider text-amber-500">
        ★ Main Quest{done ? ' — Complete' : ''}
      </div>
      <div className="text-amber-400 font-semibold">{mq.title}</div>
      {!done && mq.current_objective && (
        <div className="text-amber-200/80 mt-0.5">
          Objective {mq.current_stage + 1}/{mq.stages.length}: {mq.current_objective}
        </div>
      )}
    </div>
  );
}
