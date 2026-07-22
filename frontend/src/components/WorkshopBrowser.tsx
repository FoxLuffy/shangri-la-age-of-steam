import React, { useState, useEffect } from "react";
import { fetchWorkshopMods, installWorkshopMod } from "../api";

export const WorkshopBrowser: React.FC = () => {
  const [mods, setMods] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [message, setMessage] = useState<string>("");

  useEffect(() => {
    loadMods();
  }, []);

  const loadMods = async () => {
    setLoading(true);
    try {
      const data = await fetchWorkshopMods();
      setMods(data);
    } catch (err) {
      console.error(err);
      setMessage("Failed to load mods.");
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div className="workshop-browser p-4 bg-slate-800 text-white rounded border border-slate-700 mt-4">
      <h2 className="text-2xl mb-4 font-bold text-amber-500">Steam Workshop / Mod Browser</h2>
      {message && <div className="mb-4 p-2 bg-slate-700 text-amber-200 rounded">{message}</div>}
      
      {loading ? (
        <p>Loading modules...</p>
      ) : mods.length === 0 ? (
        <p>No mods available at the moment.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {mods.map((mod) => (
            <div key={mod.id} className="mod-card border border-slate-600 p-4 rounded bg-slate-900 flex justify-between items-center">
              <div>
                <h3 className="text-xl text-amber-400 font-semibold">{mod.name} <span className="text-sm text-slate-400">by {mod.author}</span></h3>
                <p className="text-slate-300 mt-1">{mod.description}</p>
                <div className="mt-2 text-xs text-slate-500">Downloads: {mod.downloads}</div>
              </div>
              <button
                onClick={() => handleInstall(mod.id)}
                className="bg-amber-700 hover:bg-amber-600 text-white px-4 py-2 rounded font-bold"
              >
                Install
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

