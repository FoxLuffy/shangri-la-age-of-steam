import { useCallback, useEffect, useState } from 'react';
import {
  getKnownRecipes,
  getCraftingMaterials,
  getProficiency,
  craftItem,
  experimentCraft,
  craftSuccessPct,
} from '../api';
import type { KnownRecipeInfo, CraftingMaterial, CraftingProficiency } from '../api';

interface CraftingPanelProps {
  characterId: number;
  onClose: () => void;
}

export default function CraftingPanel({ characterId, onClose }: CraftingPanelProps) {
  const [recipes, setRecipes] = useState<KnownRecipeInfo[]>([]);
  const [materials, setMaterials] = useState<CraftingMaterial[]>([]);
  const [proficiency, setProficiency] = useState<CraftingProficiency[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    const [r, m, p] = await Promise.all([
      getKnownRecipes(characterId),
      getCraftingMaterials(characterId),
      getProficiency(characterId),
    ]);
    setRecipes(r);
    setMaterials(m);
    setProficiency(p);
  }, [characterId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const levelFor = (branch: string | null): number =>
    proficiency.find((p) => p.branch === branch)?.level ?? 0;

  const ownedQty = (itemId: number): number =>
    materials.find((m) => m.item_id === itemId)?.quantity ?? 0;

  const canCraft = (recipe: KnownRecipeInfo): boolean =>
    recipe.requirements.every((req) => ownedQty(req.item_id) >= req.quantity);

  const handleCraft = async (recipe: KnownRecipeInfo) => {
    setBusy(true);
    setStatus(null);
    try {
      const res = await craftItem(characterId, recipe.recipe_id);
      setStatus(res.crafted ? `Crafted ${recipe.result_name ?? recipe.name}!` : 'Crafting failed — materials lost.');
      await refresh();
    } catch {
      setStatus('Crafting error.');
    } finally {
      setBusy(false);
    }
  };

  const toggleMaterial = (itemId: number) => {
    setSelected((prev) => (prev.includes(itemId) ? prev.filter((id) => id !== itemId) : [...prev, itemId]));
  };

  const handleExperiment = async () => {
    setBusy(true);
    setStatus(null);
    try {
      const res = await experimentCraft(characterId, selected);
      setStatus(res.discovered ? `Discovered: ${res.discovered.name}!` : 'Nothing discovered.');
      setSelected([]);
      await refresh();
    } catch {
      setStatus('Experiment error.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 font-mono">
      <div className="bg-slate-900 border-2 border-amber-900/50 shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto flex flex-col">
        <div className="p-4 border-b border-amber-900/30 bg-slate-800/50 flex justify-between items-center">
          <h2 className="text-xl text-amber-500 uppercase tracking-widest font-serif">Workbench</h2>
          <button onClick={onClose} className="text-amber-500 hover:text-amber-300 text-2xl px-2">✕</button>
        </div>

        <div className="p-5 space-y-6 text-amber-100">
          {/* Proficiency */}
          <div className="space-y-2">
            <div className="text-sm uppercase text-amber-400">Specialization</div>
            {proficiency.map((p) => (
              <div key={p.branch} className="flex items-center gap-3">
                <span className="text-xs uppercase w-24 text-amber-300 capitalize">{p.branch}</span>
                <div className="flex-1 h-2 bg-slate-800 border border-amber-900/30">
                  <div className="h-full bg-amber-600" style={{ width: `${(p.level / 10) * 100}%` }} />
                </div>
                <span className="text-xs text-amber-600/70 w-16 text-right">Lv {p.level} · {p.xp}xp</span>
              </div>
            ))}
          </div>

          {status && <div className="text-xs text-amber-300 border border-amber-900/30 bg-slate-950/40 p-2">{status}</div>}

          {/* Recipe browser */}
          <div className="space-y-2">
            <div className="text-sm uppercase text-amber-400">Known Recipes</div>
            {recipes.length === 0 && <div className="text-xs text-slate-500 italic">No recipes discovered yet.</div>}
            {recipes.map((r) => {
              const pct = craftSuccessPct(levelFor(r.branch), r.tier, r.branch);
              const craftable = canCraft(r);
              return (
                <div key={r.recipe_id} className="border border-amber-900/30 bg-slate-800/30 p-3">
                  <div className="flex justify-between items-center">
                    <span className="text-amber-400 font-bold">{r.name}</span>
                    <span className="text-[10px] uppercase text-amber-600/70">
                      {r.branch ? `${r.branch} · T${r.tier}` : 'basic'} · {pct}%
                    </span>
                  </div>
                  <div className="text-xs text-amber-200/60 mt-1">
                    {r.requirements.map((req) => (
                      <span key={req.item_id} className={ownedQty(req.item_id) >= req.quantity ? '' : 'text-red-400'}>
                        {req.name} ×{req.quantity} ({ownedQty(req.item_id)})&nbsp;&nbsp;
                      </span>
                    ))}
                  </div>
                  <button
                    onClick={() => handleCraft(r)}
                    disabled={busy || !craftable}
                    className="mt-2 px-4 py-1 text-xs uppercase tracking-wider border bg-amber-900/40 border-amber-500 text-amber-400 hover:bg-amber-800/60 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Craft
                  </button>
                </div>
              );
            })}
          </div>

          {/* Experimentation */}
          <div className="space-y-2">
            <div className="text-sm uppercase text-amber-400">Experiment</div>
            <div className="text-xs text-amber-600/70">Select materials and attempt to discover a recipe.</div>
            <div className="flex flex-wrap gap-2">
              {materials.map((m) => (
                <button
                  key={m.item_id}
                  aria-label={`select material ${m.name}`}
                  aria-pressed={selected.includes(m.item_id)}
                  onClick={() => toggleMaterial(m.item_id)}
                  className={`px-3 py-2 text-xs border ${
                    selected.includes(m.item_id)
                      ? 'bg-amber-900/40 border-amber-500 text-amber-300'
                      : 'bg-slate-800 border-slate-600 text-slate-300'
                  }`}
                >
                  {m.name} ×{m.quantity}
                </button>
              ))}
            </div>
            <button
              onClick={handleExperiment}
              disabled={busy || selected.length === 0}
              className="px-4 py-1 text-xs uppercase tracking-wider border bg-slate-800 border-slate-600 text-slate-300 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Attempt
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
