import React, { useState } from 'react';
import { fetchHealth } from './api';

function App() {
  const [status, setStatus] = useState<string | null>(null);

  const checkStatus = async () => {
    try {
      const data = await fetchHealth();
      setStatus(data.status || 'OK');
    } catch (error) {
      setStatus('Error reaching backend');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col items-center justify-center p-4">
      <h1 className="text-4xl font-bold mb-8">Shangri-La: Age of Steam</h1>
      <div className="bg-gray-800 p-8 rounded-lg shadow-xl border border-gray-700">
        <p className="mb-4 text-xl">Backend Status: <span className="font-mono">{status || 'Unknown'}</span></p>
        <button 
          onClick={checkStatus}
          className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded font-bold transition"
        >
          Check Backend Status
        </button>
      </div>
    </div>
  );
}

export default App;
