import { useEffect, useState } from 'react';

interface Augmentation {
  id: string;
  name: string;
  body_part: string;
  cost: number;
  strain: number;
  stats: Record<string, number>;
}

interface InstalledAug {
  id: number;
  body_part: string;
  augmentation_name: string;
  stat_bonus: Record<string, number>;
}

interface AugmentationPanelProps {
  characterId: number;
  brassCoins: number;
  totalStrain: number;
  installedAugmentations: InstalledAug[];
  onClose: () => void;
  onUpdate: () => void;
}

export default function AugmentationPanel({
  characterId,
  brassCoins,
  totalStrain,
  installedAugmentations,
  onClose,
  onUpdate
}: AugmentationPanelProps) {
  const [catalog, setCatalog] = useState<Augmentation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/gameplay/augmentations/catalog')
      .then(res => res.json())
      .then(data => setCatalog(data))
      .catch(err => console.error("Failed to load catalog", err));
  }, []);

  const handleInstall = async (augId: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/gameplay/augmentations/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          character_id: characterId,
          augmentation_id: augId
        })
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to install augmentation');
      }
      onUpdate();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border-2 border-amber-600 rounded-lg p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-amber-500 font-serif">Chirurgeon's Clinic</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-2xl leading-none">&times;</button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Status Panel */}
          <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
            <h3 className="text-lg font-semibold text-sky-400 mb-3 border-b border-sky-800 pb-2">Patient Status</h3>
            <div className="space-y-2 mb-4">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Available Funds:</span>
                <span className="text-amber-400 font-bold">{brassCoins} 🪙</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Total Strain:</span>
                <span className="text-rose-400 font-bold">{totalStrain} / 100</span>
              </div>
            </div>
            
            <h4 className="text-sm font-semibold text-slate-300 mb-2">Installed Modifications</h4>
            {installedAugmentations.length === 0 ? (
              <p className="text-xs text-slate-500 italic">Pure biology. No cybernetics detected.</p>
            ) : (
              <ul className="space-y-2">
                {installedAugmentations.map((aug, idx) => (
                  <li key={idx} className="bg-slate-900 p-2 rounded border border-slate-700 text-xs">
                    <div className="font-bold text-amber-300">{aug.augmentation_name}</div>
                    <div className="text-slate-400">Part: {aug.body_part}</div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Catalog Panel */}
          <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
            <h3 className="text-lg font-semibold text-emerald-400 mb-3 border-b border-emerald-800 pb-2">Available Augmentations</h3>
            
            {error && (
              <div className="bg-rose-900/50 border border-rose-500 text-rose-200 p-2 rounded text-xs mb-3">
                {error}
              </div>
            )}

            <div className="space-y-3">
              {catalog.map(aug => (
                <div key={aug.id} className="bg-slate-900 p-3 rounded-lg border border-slate-700">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-bold text-amber-400">{aug.name}</h4>
                      <div className="text-xs text-slate-400">Replaces: {aug.body_part}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-amber-300 font-bold text-sm">{aug.cost} 🪙</div>
                      <div className="text-rose-400 text-xs">Strain: {aug.strain}</div>
                    </div>
                  </div>
                  
                  <div className="text-xs text-emerald-300 mb-3">
                    Bonus: {Object.entries(aug.stats).map(([k, v]) => `${k} +${v}`).join(', ')}
                  </div>
                  
                  <button
                    onClick={() => handleInstall(aug.id)}
                    disabled={loading || brassCoins < aug.cost}
                    className="w-full bg-emerald-700 hover:bg-emerald-600 disabled:opacity-50 disabled:bg-slate-700 text-white py-1.5 rounded text-sm font-semibold transition-colors"
                  >
                    Install Procedure
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
