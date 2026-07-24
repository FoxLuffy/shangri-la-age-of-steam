import React, { useState } from 'react';
import { useCodexQuery } from '../api';

const CodexBrowser: React.FC = () => {
  const { data: codexData, isLoading, error } = useCodexQuery();
  const [activeCategory, setActiveCategory] = useState<string | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<any | null>(null);

  if (isLoading) return <div className="p-4 text-center text-amber-500 font-mono">Loading Codex Archives...</div>;
  if (error) return <div className="p-4 text-center text-red-500 font-mono">Error retrieving Codex Archives.</div>;
  if (!codexData || Object.keys(codexData).length === 0) return <div className="p-4 text-center text-amber-500 font-mono">Codex is empty.</div>;

  const categories = Object.keys(codexData);
  const currentCategory = activeCategory || categories[0];
  const entries = codexData[currentCategory] || [];

  return (
    <div className="flex flex-col h-full bg-neutral-900 border border-amber-900/50 rounded-lg overflow-hidden shadow-2xl">
      <div className="bg-neutral-950 p-4 border-b border-amber-900/50">
        <h2 className="text-2xl font-bold text-amber-500 tracking-wider font-mono uppercase mb-4">World Codex</h2>
        <div className="flex space-x-2 overflow-x-auto pb-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => {
                setActiveCategory(category);
                setSelectedEntry(null);
              }}
              className={`px-4 py-2 font-mono text-sm uppercase rounded transition-colors whitespace-nowrap ${
                currentCategory === category
                  ? 'bg-amber-600 text-neutral-950 font-bold'
                  : 'bg-neutral-800 text-amber-500 hover:bg-neutral-700'
              }`}
            >
              {category}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="w-1/3 bg-neutral-900 border-r border-amber-900/50 overflow-y-auto">
          {entries.length === 0 ? (
            <div className="p-4 text-amber-700/50 italic font-mono text-sm">No entries found.</div>
          ) : (
            <ul className="divide-y divide-amber-900/30">
              {entries.map((entry: any, idx: number) => (
                <li key={idx}>
                  <button
                    onClick={() => setSelectedEntry(entry)}
                    className={`w-full text-left p-4 hover:bg-neutral-800 transition-colors ${
                      selectedEntry === entry ? 'bg-neutral-800 border-l-4 border-amber-500' : 'border-l-4 border-transparent'
                    }`}
                  >
                    <div className="font-bold text-amber-400">{entry.name}</div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Content Area */}
        <div className="w-2/3 p-6 overflow-y-auto bg-neutral-950/50">
          {selectedEntry ? (
            <div className="text-neutral-300 font-serif space-y-6">
              <h3 className="text-3xl font-bold text-amber-500 border-b border-amber-900/50 pb-2 font-mono uppercase">{selectedEntry.name}</h3>
              
              {selectedEntry.origin && (
                <div className="bg-neutral-900/80 p-4 rounded border border-amber-900/30 shadow-inner">
                  <h4 className="text-amber-600 font-mono text-sm uppercase mb-2 tracking-widest">Origin</h4>
                  <p className="leading-relaxed">{selectedEntry.origin}</p>
                </div>
              )}

              {selectedEntry.internal_hierarchies && (
                <div className="bg-neutral-900/80 p-4 rounded border border-amber-900/30 shadow-inner">
                  <h4 className="text-amber-600 font-mono text-sm uppercase mb-2 tracking-widest">Internal Hierarchy</h4>
                  <p className="leading-relaxed">{selectedEntry.internal_hierarchies}</p>
                </div>
              )}

              {selectedEntry.signature_technologies && (
                <div className="bg-neutral-900/80 p-4 rounded border border-amber-900/30 shadow-inner">
                  <h4 className="text-amber-600 font-mono text-sm uppercase mb-2 tracking-widest">Signature Technologies</h4>
                  <ul className="list-disc list-inside text-amber-200/80">
                    {selectedEntry.signature_technologies.map((tech: string, i: number) => (
                      <li key={i} className="mb-1">{tech}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedEntry.leader_profile && (
                <div className="bg-neutral-900/80 p-4 rounded border border-amber-900/30 shadow-inner">
                  <h4 className="text-amber-600 font-mono text-sm uppercase mb-2 tracking-widest">Leadership</h4>
                  <p className="font-bold text-amber-400 mb-1">{selectedEntry.leader_profile.name}</p>
                  <p className="leading-relaxed text-sm italic">{selectedEntry.leader_profile.description}</p>
                </div>
              )}

              {selectedEntry.historical_events && (
                <div className="bg-neutral-900/80 p-4 rounded border border-amber-900/30 shadow-inner">
                  <h4 className="text-amber-600 font-mono text-sm uppercase mb-2 tracking-widest">Historical Events</h4>
                  <ul className="space-y-3">
                    {selectedEntry.historical_events.map((event: string, i: number) => {
                      const parts = event.split(':');
                      if (parts.length > 1) {
                        return (
                          <li key={i} className="text-sm">
                            <span className="font-bold text-amber-300">{parts[0]}:</span> {parts.slice(1).join(':')}
                          </li>
                        );
                      }
                      return <li key={i} className="text-sm">{event}</li>;
                    })}
                  </ul>
                </div>
              )}

              {selectedEntry.current_agenda && (
                <div className="bg-neutral-900/80 p-4 rounded border border-amber-900/30 shadow-inner">
                  <h4 className="text-amber-600 font-mono text-sm uppercase mb-2 tracking-widest">Current Agenda</h4>
                  <p className="leading-relaxed text-amber-100">{selectedEntry.current_agenda}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-amber-700/50 font-mono italic">
              Select an entry to read the archives.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CodexBrowser;
