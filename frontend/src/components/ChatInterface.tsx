import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

// Assuming the backend is running at this URL
const BACKEND_URL = 'http://localhost:8000';

function ChatInterface() {
  const [messages, setMessages] = useState<{ role: string; content: string; }[]>([]);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');

    try {
      const response = await axios.post(`${BACKEND_URL}/chat`, {
        action: input,
      });
      
      const assistantMsg = { 
        role: 'assistant', 
        content: response.data.content || response.data.message || 'No response from backend.' 
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { role: 'system', content: 'Error: Could not connect to backend.' }]);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-black text-green-500 font-mono p-4">
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto mb-4 space-y-2 border border-green-900 p-4 rounded"
      >
        {messages.map((msg, i) => (
          <div key={i} className={`${msg.role === 'user' ? 'text-white' : 'text-green-400'}`}>
            <span className="opacity-50">[{msg.role}]: </span>
            {msg.content}
          </div>
        ))}
      </div>
      <form onSubmit={handleSendMessage} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-gray-900 border border-green-900 text-green-500 px-4 py-2 focus:outline-none focus:border-green-500"
          placeholder="Type an action..."
        />
        <button type="submit" className="bg-green-900 text-black px-4 py-2 hover:bg-green-800">
          Send
        </button>
      </form>
    </div>
  );
}

export default ChatInterface;
