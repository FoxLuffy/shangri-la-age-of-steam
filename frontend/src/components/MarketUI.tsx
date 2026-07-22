import { useEffect, useState } from 'react';
import { getMarket, tradeMarket } from '../api';

interface MarketItem {
  name: string;
  price: number;
}

interface MarketUIProps {
  character: any;
  onClose: () => void;
  onUpdateCharacter: (char: any) => void;
}

export default function MarketUI({ character, onClose, onUpdateCharacter }: MarketUIProps) {
  const [marketItems, setMarketItems] = useState<MarketItem[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchMarket = async () => {
    try {
      const data = await getMarket();
      setMarketItems(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchMarket();
    
    // Listen for market sync events from the global websocket
    const handleMarketSync = (e: any) => {
      const data = e.detail;
      if (data && data.market) {
        setMarketItems(data.market);
      }
    };
    window.addEventListener('saos_market_sync', handleMarketSync);
    return () => window.removeEventListener('saos_market_sync', handleMarketSync);
  }, []);

  const handleTrade = async (resourceName: string, action: string) => {
    if (loading) return;
    setLoading(true);
    try {
      const res = await tradeMarket(character.id, resourceName, 1, action);
      onUpdateCharacter({ ...character, brass_coins: res.brass_coins });
      // Update the local market prices manually for instant feedback before websocket syncs
      setMarketItems(prev => prev.map(m => m.name === resourceName ? { ...m, price: res.new_price } : m));
    } catch (e: any) {
      alert(e.response?.data?.detail || "Trade failed");
    } finally {
      setLoading(false);
    }
  };

  // Check inventory for resource count
  // We will just let the backend fail it if they don't have enough

  return (
    <div className="absolute inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 font-mono text-amber-100">
      <div className="bg-slate-900 border-2 border-amber-900 w-full max-w-2xl shadow-[0_0_30px_rgba(217,119,6,0.2)]">
        <div className="flex justify-between items-center p-4 border-b border-amber-900/50 bg-slate-950">
          <h2 className="text-xl font-serif text-amber-500 uppercase tracking-widest flex items-center gap-2">
            <span>🌐</span> Global Resource Exchange
          </h2>
          <button 
            onClick={onClose}
            className="text-amber-600 hover:text-amber-400 font-bold px-2 py-1"
          >
            ✕
          </button>
        </div>

        <div className="p-6">
          <div className="mb-6 flex justify-between items-center bg-slate-950 border border-amber-900/30 p-3">
            <div className="text-sm text-amber-600/70 uppercase">Account Balance</div>
            <div className="text-xl font-bold text-amber-400">{character?.brass_coins || 0} <span className="text-sm">Brass</span></div>
          </div>

          <div className="text-xs text-amber-500/70 mb-4 italic font-serif">
            Prices fluctuate based on global supply and demand. Buy low, sell high.
          </div>

          <div className="space-y-3">
            {marketItems.map((item) => (
              <div key={item.name} className="flex items-center justify-between p-3 border border-amber-900/40 bg-slate-800/50">
                <div className="font-bold text-amber-200">{item.name}</div>
                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="text-lg font-bold text-amber-400">{item.price.toFixed(2)}</div>
                    <div className="text-[10px] text-amber-600 uppercase">per unit</div>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      disabled={loading || (character?.brass_coins || 0) < item.price}
                      onClick={() => handleTrade(item.name, 'buy')}
                      className="px-4 py-2 bg-emerald-900/30 border border-emerald-700/50 text-emerald-400 hover:bg-emerald-800/50 disabled:opacity-50 text-xs font-bold uppercase transition-colors"
                    >
                      Buy 1
                    </button>
                    <button 
                      disabled={loading}
                      onClick={() => handleTrade(item.name, 'sell')}
                      className="px-4 py-2 bg-rose-900/30 border border-rose-700/50 text-rose-400 hover:bg-rose-800/50 disabled:opacity-50 text-xs font-bold uppercase transition-colors"
                    >
                      Sell 1
                    </button>
                  </div>
                </div>
              </div>
            ))}
            
            {marketItems.length === 0 && (
              <div className="text-center p-8 text-amber-600/50">
                Connecting to global exchange ticker...
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
