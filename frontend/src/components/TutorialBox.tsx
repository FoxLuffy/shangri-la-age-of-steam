import { useState } from 'react';

export default function TutorialBox({ title, message, isEnabled }: { title: string, message: string, isEnabled: boolean }) {
  const [dismissed, setDismissed] = useState(false);

  if (!isEnabled || dismissed) return null;

  return (
    <div className="bg-sky-900/40 border border-sky-500/50 p-4 mb-4 rounded relative shadow-lg shadow-sky-900/20 animate-fade-in">
      <div className="absolute top-0 left-0 w-1 h-full bg-sky-400"></div>
      <div className="flex justify-between items-start">
        <div>
          <div className="text-sky-300 font-mono text-xs uppercase tracking-widest mb-1 flex items-center gap-2">
            <span>ℹ️</span> Tutorial: {title}
          </div>
          <div className="text-sky-100/80 text-sm font-serif leading-relaxed">
            {message}
          </div>
        </div>
        <button 
          onClick={() => setDismissed(true)}
          className="text-sky-400 hover:text-sky-200 ml-4 text-sm px-2"
          title="Dismiss this tip"
        >
          ✕
        </button>
      </div>
    </div>
  );
}
