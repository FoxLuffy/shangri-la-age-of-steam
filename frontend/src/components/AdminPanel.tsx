import { useState, useEffect } from 'react';
import { BACKEND_URL } from '../api';

interface AdminPanelProps {
  token: string;
  onClose: () => void;
}

export default function AdminPanel({ token, onClose }: AdminPanelProps) {
  const [activeTab, setActiveTab] = useState<'users' | 'logs' | 'bugreports' | 'settings' | 'prompts'>('users');
  const [users, setUsers] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [bugreports, setBugReports] = useState<any[]>([]);
  const [npcs, setNpcs] = useState<any[]>([]);
  const [globalPrompt, setGlobalPrompt] = useState<string>('');
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
      setGlobalPrompt(data.global_system_prompt || '');
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchBugReports = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${baseUrl}/admin/bugreports`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch bug reports');
      const data = await res.json();
      setBugReports(data.bugreports);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchNpcs = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${baseUrl}/admin/npcs`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to fetch npcs');
      const data = await res.json();
      setNpcs(data.npcs);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveGlobalPrompt = async () => {
    try {
      const res = await fetch(`${baseUrl}/admin/settings`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ registration_open: registrationOpen, global_system_prompt: globalPrompt })
      });
      if (!res.ok) throw new Error('Update failed');
      alert('Global prompt saved successfully');
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleSaveNpcPrompt = async (npcId: string, customPrompt: string) => {
    try {
      const res = await fetch(`${baseUrl}/admin/npcs/${npcId}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify({ custom_system_prompt: customPrompt })
      });
      if (!res.ok) throw new Error('Update failed');
      alert('NPC prompt saved successfully');
    } catch (err: any) {
      setError(err.message);
    }
  };


  useEffect(() => {
    if (activeTab === 'users') fetchUsers();
    else if (activeTab === 'logs') fetchLogs();
    else if (activeTab === 'bugreports') fetchBugReports();
    else if (activeTab === 'settings') fetchSettings();
    else if (activeTab === 'prompts') {
      fetchSettings();
      fetchNpcs();
    }
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

  const handleDeleteBugReport = async (bugId: number) => {
    if (!confirm('Delete this bug report?')) return;
    try {
      const res = await fetch(`${baseUrl}/admin/bugreports/${bugId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Delete failed');
      setBugReports(bugreports.filter(b => b.id !== bugId));
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
            className={`flex-1 py-2 ${activeTab === 'bugreports' ? 'bg-amber-900/50 text-amber-300' : 'hover:bg-slate-800'}`}
            onClick={() => setActiveTab('bugreports')}
          >
            Reports
          </button>
          <button 
            className={`flex-1 py-2 ${activeTab === 'settings' ? 'bg-amber-900/50 text-amber-300' : 'hover:bg-slate-800'}`}
            onClick={() => setActiveTab('settings')}
          >
            System Settings
          </button>
          <button 
            className={`flex-1 py-2 ${activeTab === 'prompts' ? 'bg-amber-900/50 text-amber-300' : 'hover:bg-slate-800'}`}
            onClick={() => setActiveTab('prompts')}
          >
            AI Prompts
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

              {activeTab === 'bugreports' && (
                <div className="space-y-4">
                  <div className="flex justify-end mb-4">
                    <button 
                      onClick={() => {
                        let content = "# Generated Roadmap Input\n\n";
                        content += "Here are the compiled bug reports and feature requests from the user community. Please analyze them and create a prioritized roadmap.\n\n";
                        bugreports.forEach(report => {
                          content += `## ${report.type === 'feature' ? 'Feature Request' : 'Bug Report'} #${report.id}\n`;
                          content += `**Date:** ${new Date(report.created_at).toLocaleString()}\n`;
                          content += `**Status:** ${report.status}\n`;
                          content += `### Original Request\n${report.original_text}\n\n`;
                          if (report.optimized_text) {
                            content += `### AI Optimized Prompt\n${report.optimized_text}\n\n`;
                          }
                          content += "---\n\n";
                        });

                        const blob = new Blob([content], { type: 'text/markdown' });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `saos_roadmap_input_${new Date().toISOString().split('T')[0]}.md`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        URL.revokeObjectURL(url);
                      }}
                      className="px-4 py-2 bg-emerald-700 hover:bg-emerald-600 text-white rounded font-bold transition-colors"
                    >
                      Export Roadmap for Gemini
                    </button>
                  </div>
                  {bugreports.map(bug => (
                    <div key={bug.id} className="border border-orange-900 bg-slate-950 p-4 rounded flex flex-col gap-4 relative">
                      <button 
                        onClick={() => handleDeleteBugReport(bug.id)}
                        className="absolute top-2 right-2 text-xs bg-red-900/50 hover:bg-red-900 text-red-200 px-2 py-1 rounded"
                      >
                        DELETE
                      </button>
                      <div className="flex justify-between text-xs text-orange-500 border-b border-orange-900/50 pb-2">
                        <span>[{bug.type === 'feature' ? 'Feature' : 'Bug'}] Report ID: {bug.id} | User ID: {bug.user_id}</span>
                        <span className="mr-16">{new Date(bug.created_at).toLocaleString()}</span>
                      </div>
                      <div>
                        <h4 className="text-orange-300 font-bold mb-1">User Input (Original):</h4>
                        <div className="text-orange-100 bg-orange-950/20 p-2 rounded text-sm whitespace-pre-wrap">
                          {bug.original_text}
                        </div>
                      </div>
                      {bug.optimized_text && (
                        <div className="relative">
                          <h4 className="text-green-400 font-bold mb-1">AI Optimized Prompt:</h4>
                          <button 
                            onClick={() => {
                              navigator.clipboard.writeText(bug.optimized_text);
                              alert('Copied to clipboard!');
                            }}
                            className="absolute top-0 right-0 text-xs bg-green-900/50 hover:bg-green-900 text-green-200 px-2 py-1 rounded"
                          >
                            COPY
                          </button>
                          <div className="text-green-100 bg-green-950/20 p-2 rounded text-sm whitespace-pre-wrap mt-2">
                            {bug.optimized_text}
                          </div>
                        </div>
                      )}
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

              {activeTab === 'prompts' && (
                <div className="space-y-6">
                  <div className="border border-slate-700 bg-slate-950 p-6 rounded flex flex-col gap-4">
                    <div>
                      <h3 className="text-lg font-bold text-amber-400">Global System Prompt Override</h3>
                      <p className="text-sm text-slate-400">Appended or used as the global instructions for the engine.</p>
                    </div>
                    <textarea 
                      className="w-full h-32 bg-slate-900 border border-slate-700 p-2 text-sm text-slate-200"
                      value={globalPrompt}
                      onChange={e => setGlobalPrompt(e.target.value)}
                      placeholder="Enter global prompt instructions here..."
                    />
                    <button 
                      onClick={handleSaveGlobalPrompt}
                      className="self-end px-4 py-2 bg-amber-700 hover:bg-amber-600 text-white rounded font-bold"
                    >
                      Save Global Prompt
                    </button>
                  </div>
                  
                  <div className="border border-slate-700 bg-slate-950 p-6 rounded flex flex-col gap-4">
                    <div>
                      <h3 className="text-lg font-bold text-amber-400">NPC Custom Prompts</h3>
                      <p className="text-sm text-slate-400">Tweak narrative prompt parameters for specific NPCs.</p>
                    </div>
                    {npcs.map(npc => (
                      <div key={npc.id} className="border border-slate-800 p-4 rounded bg-slate-900 flex flex-col gap-2">
                        <div className="font-bold text-amber-500">{npc.name} (ID: {npc.id})</div>
                        <textarea 
                          className="w-full h-20 bg-slate-950 border border-slate-700 p-2 text-sm text-slate-200"
                          defaultValue={npc.custom_system_prompt || ''}
                          onBlur={(e) => {
                            if (e.target.value !== npc.custom_system_prompt) {
                              setNpcs(npcs.map(n => n.id === npc.id ? { ...n, custom_system_prompt: e.target.value } : n));
                            }
                          }}
                          placeholder={`Custom instructions for ${npc.name}...`}
                        />
                        <button 
                          onClick={() => handleSaveNpcPrompt(npc.id, npcs.find(n => n.id === npc.id)?.custom_system_prompt || '')}
                          className="self-end px-4 py-1 bg-amber-800 hover:bg-amber-700 text-white rounded text-xs font-bold"
                        >
                          Save NPC Prompt
                        </button>
                      </div>
                    ))}
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
