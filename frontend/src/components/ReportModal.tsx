import { useState } from 'react';
import { BACKEND_URL } from '../api';

interface ReportModalProps {
  userId: number | null;
  onClose: () => void;
}

export default function ReportModal({ userId, onClose }: ReportModalProps) {
  const [type, setType] = useState('bug');
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${BACKEND_URL}/bugreports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, text, type })
      });
      if (!res.ok) {
        throw new Error('Failed to submit report');
      }
      setSuccess(true);
      setTimeout(onClose, 2000);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="absolute inset-0 bg-slate-950/80 z-[200] flex items-center justify-center p-4 font-mono text-amber-500">
      <div className="bg-slate-900 border border-amber-900 w-full max-w-lg p-6 rounded-lg shadow-2xl">
        <h2 className="text-xl font-bold mb-4 text-amber-400">Submit a Report</h2>
        {success ? (
          <div className="text-green-400 py-8 text-center">
            Report submitted successfully!
            <br/><span className="text-sm text-slate-400">Our AI agents are analyzing it.</span>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex flex-col gap-2">
              <label className="text-sm font-bold text-amber-500">Report Type</label>
              <select 
                value={type} 
                onChange={e => setType(e.target.value)}
                className="bg-slate-950 border border-amber-900/50 rounded p-2 text-amber-100 focus:outline-none focus:border-amber-500"
                disabled={loading}
              >
                <option value="bug">Bug Report</option>
                <option value="feature">Feature Request</option>
              </select>
            </div>
            <p className="text-sm text-slate-400 mb-2">
              Describe the {type === 'bug' ? 'issue you encountered' : 'feature you would like'}. Be as specific as possible so our AI can automatically generate an implementation prompt.
            </p>
            <textarea
              className="w-full h-32 bg-slate-950 border border-amber-900/50 rounded p-2 focus:outline-none focus:border-amber-500 text-amber-100"
              placeholder="E.g. When I click on..."
              value={text}
              onChange={e => setText(e.target.value)}
              disabled={loading}
              required
            />
            {error && <div className="text-red-500 text-sm">{error}</div>}
            <div className="flex justify-end gap-2 mt-4">
              <button 
                type="button" 
                onClick={onClose}
                className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                type="submit"
                className="px-4 py-2 bg-amber-700 hover:bg-amber-600 text-white rounded font-bold transition-colors disabled:opacity-50"
                disabled={loading || !text.trim()}
              >
                {loading ? 'Submitting...' : 'Submit Report'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
