import React from 'react';

interface AirshipPanelProps {
  airship: any;
}

export default function AirshipPanel({ airship }: AirshipPanelProps) {
  if (!airship) return null;

  return (
    <div className="airship-panel p-4 border-2 border-amber-700 bg-slate-900 rounded-lg shadow-[0_0_15px_rgba(180,83,9,0.3)] w-full max-w-sm mb-4">
      <h3 className="text-lg font-bold font-serif text-amber-500 mb-3 border-b border-amber-900/50 pb-2 uppercase tracking-widest flex items-center gap-2">
        <span>⚙️</span> {airship.name}
      </h3>
      
      <div className="gauges flex flex-col gap-3 mb-4">
        <div className="gauge">
          <div className="flex justify-between mb-1">
            <label className="text-xs font-semibold text-amber-600 uppercase tracking-widest">Hull Integrity</label>
            <span className="text-xs font-mono text-amber-400">{Math.round(airship.hull_integrity)}%</span>
          </div>
          <div className="w-full bg-slate-950 rounded-full h-3 border border-amber-800 shadow-inner overflow-hidden relative">
            <div 
              className="bg-amber-600 h-full transition-all duration-500" 
              style={{ width: `${Math.max(0, Math.min(100, airship.hull_integrity))}%` }}
            ></div>
            <div className="absolute inset-0 bg-gradient-to-b from-white/20 to-transparent"></div>
          </div>
        </div>
        <div className="gauge">
          <div className="flex justify-between mb-1">
            <label className="text-xs font-semibold text-sky-600 uppercase tracking-widest">Fuel Pressure</label>
            <span className="text-xs font-mono text-sky-400">{Math.round(airship.fuel_level)}%</span>
          </div>
          <div className="w-full bg-slate-950 rounded-full h-3 border border-sky-800 shadow-inner overflow-hidden relative">
            <div 
              className="bg-sky-500 h-full transition-all duration-500" 
              style={{ width: `${Math.max(0, Math.min(100, airship.fuel_level))}%` }}
            ></div>
            <div className="absolute inset-0 bg-gradient-to-b from-white/20 to-transparent"></div>
          </div>
        </div>
      </div>

      <div className="modules mt-4 pt-3 border-t border-amber-900/50">
        <h4 className="text-xs font-bold text-amber-600 uppercase tracking-widest mb-2">Installed Modules</h4>
        <ul className="text-xs font-mono text-amber-100/70 space-y-1">
          {airship.modules && airship.modules.length > 0 ? (
            airship.modules.map((m: string, idx: number) => <li key={idx} className="flex items-center gap-2"><span className="text-amber-500">•</span> {m}</li>)
          ) : (
            <li className="italic text-slate-500">No modules installed.</li>
          )}
        </ul>
      </div>
    </div>
  );
}
