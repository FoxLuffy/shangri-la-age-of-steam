import { useState, useEffect } from 'react';

interface Bounty {
  id: number;
  title: string;
  description: string;
  target_npc_type: string;
  reward_coins: number;
  status: string;
}

interface BountyBoardProps {
  isOpen: boolean;
  onClose: () => void;
  characterId: number;
}

export default function BountyBoard({ isOpen, onClose, characterId }: BountyBoardProps) {
  const [available, setAvailable] = useState<Bounty[]>([]);
  const [_activeIds, setActiveIds] = useState<number[]>([]);
  const [_completedIds, setCompletedIds] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchBounties = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/gameplay/bounties?character_id=${characterId}`);
      if (!res.ok) throw new Error("Failed to fetch bounties");
      const data = await res.json();
      setAvailable(data.available || []);
      setActiveIds(data.active_ids || []);
      setCompletedIds(data.completed_ids || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && characterId) {
      fetchBounties();
    }
  }, [isOpen, characterId]);

  const acceptBounty = async (bountyId: number) => {
    try {
      const res = await fetch(`/api/gameplay/bounties/accept?character_id=${characterId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bounty_id: bountyId })
      });
      if (!res.ok) throw new Error("Failed to accept bounty");
      
      // Optimistic update
      setActiveIds((prev) => [...prev, bountyId]);
      setAvailable((prev) => prev.filter(b => b.id !== bountyId));
    } catch (err: any) {
      alert(err.message);
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
                    onClick={() => acceptBounty(bounty.id)}
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
