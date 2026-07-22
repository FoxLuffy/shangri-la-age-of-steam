import { useState } from 'react';
import { BACKEND_URL } from '../api';

interface AccountManagerProps {
  onLogin: (token: string, userId: number, isAdmin: boolean) => void;
}

export default function AccountManager({ onLogin }: AccountManagerProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [adminSecret, setAdminSecret] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const endpoint = isLogin ? '/auth/login' : '/auth/register';
    const baseUrl = BACKEND_URL;

    try {
      const res = await fetch(`${baseUrl}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, admin_secret: adminSecret || undefined })
      });
      
      const data = await res.json();
      
      if (!res.ok) {
        throw new Error(data.detail || 'Authentication failed');
      }

      if (data.status === 'success') {
        onLogin(data.token, data.user_id, !!data.is_admin);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-950 font-mono text-amber-500">
      <div className="bg-slate-900 p-8 rounded-lg border border-amber-900/50 shadow-2xl max-w-md w-full">
        <h2 className="text-2xl font-bold text-center mb-6 text-amber-400">
          {isLogin ? 'Access Terminal' : 'Register New Operative'}
        </h2>
        
        {error && (
          <div className="bg-red-900/20 border border-red-500/50 text-red-400 p-3 rounded mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm mb-1 text-amber-600">Callsign (Username)</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-slate-950 border border-amber-900 rounded p-2 text-amber-100 focus:outline-none focus:border-amber-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm mb-1 text-amber-600">Access Code (Password)</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-slate-950 border border-amber-900 rounded p-2 text-amber-100 focus:outline-none focus:border-amber-500"
              required
            />
          </div>
          
          {!isLogin && (
            <div>
              <label className="block text-sm mb-1 text-amber-600">Admin Override Code (Optional)</label>
              <input
                type="password"
                value={adminSecret}
                onChange={(e) => setAdminSecret(e.target.value)}
                placeholder="Leave blank for standard user"
                className="w-full bg-slate-950 border border-amber-900 rounded p-2 text-amber-100 focus:outline-none focus:border-amber-500"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading || !username || !password}
            className="w-full bg-amber-600 hover:bg-amber-500 text-slate-950 font-bold py-2 px-4 rounded transition-colors disabled:opacity-50"
          >
            {loading ? 'Processing...' : (isLogin ? 'Initialize Uplink' : 'Forge Credentials')}
          </button>
        </form>

        <div className="mt-6 text-center text-sm text-slate-400">
          {isLogin ? "Don't have credentials? " : "Already registered? "}
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-amber-500 hover:text-amber-400 underline decoration-amber-500/30"
          >
            {isLogin ? 'Register' : 'Login'}
          </button>
        </div>
      </div>
    </div>
  );
}
