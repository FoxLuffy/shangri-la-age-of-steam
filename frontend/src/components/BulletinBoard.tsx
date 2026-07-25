import { useState, useEffect } from 'react';
import { fetchMessages, sendMessage } from '../api';

export default function BulletinBoard({ characterId, locationId, onClose }: { characterId: number, locationId: string, onClose: () => void }) {
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState('');
  
  const loadMessages = async () => {
    try {
      setLoading(true);
      const data = await fetchMessages(locationId);
      setMessages(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMessages();
  }, [locationId]);

  const handlePost = async () => {
    if (!content.trim()) return;
    try {
      setLoading(true);
      await sendMessage(characterId, locationId, content);
      setContent('');
      await loadMessages();
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  return (
    <div className="absolute inset-0 bg-slate-950/80 z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-amber-900 rounded-xl p-6 w-full max-w-2xl shadow-2xl relative h-[80vh] flex flex-col">
        <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-white">✕</button>
        <h2 className="text-xl font-bold text-amber-500 mb-4 flex items-center gap-2">
          <span>📜</span> Bulletin Board - Notices
        </h2>
        
        <div className="flex-1 overflow-y-auto mb-4 pr-2 flex flex-col gap-3">
          {messages.length === 0 ? (
            <div className="text-slate-500 italic text-center mt-10">No messages posted here yet.</div>
          ) : (
            messages.map(m => (
              <div key={m.id} className="bg-slate-800 p-3 rounded-lg border border-slate-700 shadow">
                <div className="text-xs text-amber-400 mb-1 flex justify-between">
                  <span>Author ID: {m.author_id}</span>
                  <span className="text-slate-500">{new Date(m.timestamp).toLocaleString()}</span>
                </div>
                <div className="text-sm text-slate-200">
                  {m.content}
                </div>
              </div>
            ))
          )}
        </div>

        <div className="mt-auto border-t border-slate-700 pt-4 flex gap-2">
          <input 
            type="text" 
            className="flex-1 bg-slate-950 border border-slate-700 rounded p-2 text-sm text-slate-200 focus:outline-none focus:border-amber-500" 
            placeholder="Write a public notice..." 
            value={content} 
            onChange={e => setContent(e.target.value)} 
            onKeyDown={e => e.key === 'Enter' && handlePost()}
          />
          <button 
            onClick={handlePost} 
            disabled={loading || !content.trim()} 
            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-slate-950 font-bold rounded transition-colors"
          >
            Post
          </button>
        </div>
      </div>
    </div>
  );
}
