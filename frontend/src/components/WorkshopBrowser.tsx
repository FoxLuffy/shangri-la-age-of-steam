import React, { useState, useEffect, useCallback } from "react";
import { fetchWorkshopMods, installWorkshopMod, rateMod } from "../api";
import type { WorkshopMod } from "../api";

type SortKey = "rating" | "downloads";

export const WorkshopBrowser: React.FC<{ userId?: number | null }> = ({ userId }) => {
  const [mods, setMods] = useState<WorkshopMod[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [message, setMessage] = useState<string>("");
  const [sortKey, setSortKey] = useState<SortKey>("rating");

  const loadMods = useCallback(async () => {
    setLoading(true);
    try {
      setMods(await fetchWorkshopMods());
    } catch (err) {
      console.error(err);
      setMessage("Failed to load mods.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMods();
  }, [loadMods]);

  const handleInstall = async (modId: string) => {
    setMessage(`Installing mod ${modId}...`);
    try {
      const res = await installWorkshopMod(modId);
      setMessage(res.message || "Mod installed successfully!");
    } catch (err: any) {
      console.error(err);
      setMessage(err.response?.data?.detail || "Failed to install mod.");
    }
  };

  const handleRate = async (modId: string, stars: number) => {
    if (!userId) return;
    try {
      await rateMod(modId, userId, stars);
      setMessage(`Rated ${modId}: ${stars}★`);
      await loadMods();
    } catch (err) {
      console.error(err);
      setMessage("Failed to submit rating.");
    }
  };

  const sorted = [...mods].sort((a, b) =>
    sortKey === "rating" ? b.avg_rating - a.avg_rating : b.downloads - a.downloads,
  );
  const featured = mods.filter((m) => m.featured);

  const stars = (mod: WorkshopMod) => (
    <div className="flex items-center gap-1 mt-1">
      {[1, 2, 3, 4, 5].map((n) => (
        <button
          key={n}
          aria-label={`rate ${mod.id} ${n} stars`}
          disabled={!userId}
          onClick={() => handleRate(mod.id, n)}
          className={`text-sm ${n <= Math.round(mod.avg_rating) ? "text-amber-400" : "text-slate-600"} disabled:opacity-50`}
        >
          ★
        </button>
      ))}
      <span className="text-xs text-slate-400 ml-2">
        {mod.avg_rating.toFixed(1)} ({mod.rating_count})
      </span>
    </div>
  );

  const card = (mod: WorkshopMod) => (
    <div key={mod.id} className="mod-card border border-slate-600 p-4 rounded bg-slate-900 flex justify-between items-center gap-4">
      <div>
        <h3 className="text-xl text-amber-400 font-semibold">
          {mod.name} <span className="text-sm text-slate-400">by {mod.author}</span>
        </h3>
        <p className="text-slate-300 mt-1">{mod.description}</p>
        {stars(mod)}
        {mod.dependencies && mod.dependencies.length > 0 && (
          <div className="mt-1 text-xs text-sky-400">Requires: {mod.dependencies.join(", ")}</div>
        )}
        <div className="mt-2 text-xs text-slate-500">Downloads: {mod.downloads}</div>
      </div>
      <button
        onClick={() => handleInstall(mod.id)}
        className="bg-amber-700 hover:bg-amber-600 text-white px-4 py-2 rounded font-bold"
      >
        Install
      </button>
    </div>
  );

  return (
    <div className="workshop-browser p-4 bg-slate-800 text-white rounded border border-slate-700 mt-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-amber-500">Steam Workshop / Mod Browser</h2>
        <label className="text-xs text-slate-300">
          Sort:{" "}
          <select
            value={sortKey}
            onChange={(e) => setSortKey(e.target.value as SortKey)}
            className="bg-slate-900 border border-slate-600 rounded px-2 py-1 text-amber-200"
          >
            <option value="rating">Rating</option>
            <option value="downloads">Downloads</option>
          </select>
        </label>
      </div>

      {message && <div className="mb-4 p-2 bg-slate-700 text-amber-200 rounded">{message}</div>}

      {loading ? (
        <p>Loading modules...</p>
      ) : mods.length === 0 ? (
        <p>No mods available at the moment.</p>
      ) : (
        <>
          {featured.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm uppercase tracking-wider text-amber-500 mb-2">★ Featured</h3>
              <div data-testid="featured-carousel" className="flex gap-4 overflow-x-auto pb-2">
                {featured.map((mod) => (
                  <div key={mod.id} className="min-w-[220px] border border-amber-700/60 bg-slate-900 rounded p-3">
                    <div className="text-amber-400 font-semibold">{mod.name}</div>
                    <div className="text-xs text-slate-400">by {mod.author}</div>
                    <div className="text-xs text-amber-300 mt-1">
                      ★ {mod.avg_rating.toFixed(1)} ({mod.rating_count})
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="flex flex-col gap-4">{sorted.map(card)}</div>
        </>
      )}
    </div>
  );
};
