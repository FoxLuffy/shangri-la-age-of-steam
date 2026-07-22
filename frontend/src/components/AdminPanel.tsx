import { useState, useEffect } from 'react';
import { BACKEND_URL } from '../api';

interface AdminPanelProps {
  token: string;
  onClose: () => void;
}

export default function AdminPanel({ token, onClose }: AdminPanelProps) {
  const [activeTab, setActiveTab] = useState<'users' | 'logs' | 'settings'>('users');
  const [users, setUsers] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [registrationOpen, setRegistrationOpen] = useState<boolean>(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const baseUrl = BACKEND_URL;

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${baseUrl}/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch users');
      const data = await res.json();
      setUsers(data.users);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${baseUrl}/admin/logs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch logs');
      const data = await res.json();
      setLogs(data.logs);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchSettings = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${baseUrl}/admin/settings`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch settings');
      const data = await res.json();
      setRegistrationOpen(data.registration_open);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'users') fetchUsers();
    else if (activeTab === 'logs') fetchLogs();
    else if (activeTab === 'settings') fetchSettings();
  }, [activeTab]);

  const handleDeleteUser = async (userId: number) => {
    if (!confirm('Are you sure you want to terminate this operative?')) return;
    try {
      const res = await fetch(`${baseUrl}/admin/users/${userId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Delete failed');
      setUsers(users.filter(u => u.id !== userId));
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleToggleRegistration = async () => {
    try {
      const newState = !registrationOpen;
      const res = await fetch(`${baseUrl}/admin/settings`, {
        method: 'POST',
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ registration_open: newState })
      });
      if (!res.ok) throw new Error('Failed to update settings');
      setRegistrationOpen(newState);
    } catch (err: any) {
      alert(err.message);
    }
  };

  return (
    <div className="absolute inset-0 bg-slate-950/90 z-[100] flex items-center justify-center p-4 font-mono text-amber-500">
      <div className="bg-slate-900 border border-amber-900 w-full max-w-4xl h-[80vh] flex flex-col rounded-lg shadow-2xl shadow-amber-900/20">
        <div className="flex justify-between items-center p-4 border-b border-amber-900 bg-slate-950">
          <h2 className="text-xl font-bold text-amber-400">ADMINISTRATOR CONSOLE</h2>
          <button onClick={onClose} className="text-amber-500 hover:text-red-500">
            [CLOSE]
          </button>
        </div>
        
        <div className="flex border-b border-amber-900">
          <button 
            className={`flex-1 py-2 ${activeTab === 'users' ? 'bg-amber-900/50 text-amber-300' : 'hover:bg-slate-800'}`}
            onClick={() => setActiveTab('users')}
          >
            Operatives (Users)
          </button>
          <button 
            className={`flex-1 py-2 ${activeTab === 'logs' ? 'bg-amber-900/50 text-amber-300' : 'hover:bg-slate-800'}`}
            onClick={() => setActiveTab('logs')}
          >
            Narrative Logs (Audit)
          </button>
          <button 
            className={`flex-1 py-2 ${activeTab === 'settings' ? 'bg-amber-900/50 text-amber-300' : 'hover:bg-slate-800'}`}
            onClick={() => setActiveTab('settings')}
          >
            System Settings
          </button>
        </div>

        <div className="flex-1 overflow-auto p-4">
          {error && <div className="text-red-500 mb-4">{error}</div>}
          {loading ? (
            <div className="text-center py-10">Accessing Database...</div>
          ) : (
            <>
              {activeTab === 'users' && (
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-amber-900 text-amber-600">
                      <th className="pb-2">ID</th>
                      <th className="pb-2">Callsign</th>
                      <th className="pb-2">Privilege</th>
                      <th className="pb-2 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(u => (
                      <tr key={u.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                        <td className="py-2">{u.id}</td>
                        <td className="py-2 font-bold">{u.username}</td>
                        <td className="py-2">{u.is_admin ? 'Admin' : 'Standard'}</td>
                        <td className="py-2 text-right space-x-2">
                          <button onClick={() => handleDeleteUser(u.id)} className="text-red-400 hover:text-red-300 text-xs border border-red-900 px-2 py-1 rounded">
                            TERMINATE
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}

              {activeTab === 'logs' && (
                <div className="space-y-4">
                  {logs.map(log => (
                    <div key={log.id} className="border border-slate-700 bg-slate-950 p-3 rounded">
                      <div className="flex justify-between text-xs text-amber-700 mb-2 border-b border-slate-800 pb-1">
                        <span>Log ID: {log.id} | Char ID: {log.character_id}</span>
                        <span>{new Date(log.timestamp).toLocaleString()}</span>
                      </div>
                      <div className="text-sm">
                        <span className="text-amber-300 font-bold">Action: </span>
                        {log.action}
                      </div>
                      <div className="text-sm mt-1">
                        <span className="text-blue-300 font-bold">Narration: </span>
                        {log.narration}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'settings' && (
                <div className="space-y-6">
                  <div className="border border-slate-700 bg-slate-950 p-6 rounded flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-bold text-amber-400">New User Registration</h3>
                      <p className="text-sm text-slate-400">Toggle whether new users are allowed to create accounts.</p>
                    </div>
                    <button 
                      onClick={handleToggleRegistration}
                      className={`px-6 py-2 font-bold rounded transition-colors ${registrationOpen ? 'bg-green-600 hover:bg-green-500 text-white' : 'bg-red-600 hover:bg-red-500 text-white'}`}
                    >
                      {registrationOpen ? 'OPEN (ALLOW NEW)' : 'CLOSED (BLOCK NEW)'}
                    </button>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
