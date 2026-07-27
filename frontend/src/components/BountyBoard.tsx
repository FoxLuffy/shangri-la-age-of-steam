import { useState, useEffect } from 'react';
import { fetchBounties, acceptBounty } from '../api';
import type { Bounty } from '../api';

interface BountyBoardProps {
  isOpen: boolean;
  onClose: () => void;
  characterId: number;
}

export default function BountyBoard({ isOpen, onClose, characterId }: BountyBoardProps) {
  const [available, setAvailable] = useState<Bounty[]>([]);
  const [active, setActive] = useState<Bounty[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadBounties = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchBounties(characterId);
      setAvailable(data.available || []);
      setActive(data.active || []);
    } catch {
      setError("Failed to load bounties.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && characterId) {
      loadBounties();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, characterId]);

  const handleAccept = async (bountyId: number) => {
    try {
      await acceptBounty(characterId, bountyId);
      // Reload so the active bounty + replace-semantics (a prior active returns to the
      // pool) are reflected accurately.
      await loadBounties();
    } catch {
      setError("Failed to accept contract.");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="bg-[#2a241b] border-4 border-[#4a3928] rounded text-[#e0c7a8] w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden font-serif" style={{ backgroundImage: "url('https://www.transparenttextures.com/patterns/wood-pattern.png')" }}>
        <div className="bg-[#1f1a14] border-b-4 border-[#3a2c1e] px-6 py-4 flex items-center justify-between">
          <h2 className="text-3xl font-bold tracking-widest text-[#d4af37] drop-shadow-md">WANTED: BOUNTY BOARD</h2>
          <button
            onClick={onClose}
            className="text-[#a08a70] hover:text-[#e0c7a8] text-2xl font-bold hover:scale-110 transition-transform"
          >
            ✕
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1 flex flex-col gap-6">
          {isLoading && <p className="text-center text-xl animate-pulse">Checking postings...</p>}
          {error && <p className="text-red-400 text-center font-sans">{error}</p>}

          {!isLoading && active.length > 0 && (
            <div className="border-2 border-[#d4af37] bg-[#1f1a14]/60 rounded p-4">
              <h3 className="text-lg font-bold tracking-widest text-[#d4af37] mb-3 uppercase">Your Active Contract</h3>
              {active.map(bounty => (
                <div key={bounty.id} className="bg-[#f4e4c1] text-[#2c1e0b] p-4 border border-[#c4a97a] shadow-lg">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-lg font-black uppercase">{bounty.title}</h4>
                    <span className="text-[10px] font-bold uppercase bg-green-800 text-[#f4e4c1] px-2 py-0.5 rounded">Active</span>
                  </div>
                  <p className="text-sm font-semibold text-red-900 mb-1">TARGET: {bounty.target_npc_type}</p>
                  <p className="text-sm mb-2 leading-relaxed font-sans">{bounty.description}</p>
                  <p className="text-sm font-bold text-amber-700">REWARD: {bounty.reward_coins} Coins — defeat the target to claim it.</p>
                </div>
              ))}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {!isLoading && available.map(bounty => (
              <div key={bounty.id} className="relative bg-[#f4e4c1] text-[#2c1e0b] p-5 shadow-lg transform -rotate-1 hover:rotate-0 transition-transform cursor-pointer border border-[#c4a97a]" style={{ backgroundImage: "url('https://www.transparenttextures.com/patterns/cream-paper.png')" }}>
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 w-4 h-4 rounded-full bg-red-800 shadow-sm border border-red-950 z-10" />
                <h3 className="text-xl font-black uppercase text-center mb-2 border-b-2 border-[#8c6d46] pb-2">{bounty.title}</h3>
                <p className="text-sm font-semibold text-center text-red-900 mb-2">TARGET: {bounty.target_npc_type}</p>
                <p className="text-sm mb-4 leading-relaxed font-sans">{bounty.description}</p>
                <div className="text-center">
                  <p className="text-lg font-bold text-amber-700 mb-3">REWARD: {bounty.reward_coins} Coins</p>
                  <button
                    onClick={() => handleAccept(bounty.id)}
                    className="w-full py-2 bg-red-900 hover:bg-red-800 text-[#f4e4c1] font-bold tracking-wider rounded uppercase text-sm border-2 border-red-950 transition-colors"
                  >
                    Accept Contract
                  </button>
                </div>
              </div>
            ))}
            {!isLoading && available.length === 0 && (
              <div className="col-span-full text-center text-xl text-[#a08a70] italic border-2 border-dashed border-[#4a3928] p-8">
                No new postings at this time. Check back later.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
