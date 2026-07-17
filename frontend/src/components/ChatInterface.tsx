import React, { useState, useEffect, useRef } from 'react';
import { sendAction } from './api';

/**
 * A terminal-style chat interface component for the Shangri-la: Age of Steam RPG.
 * Features a scrollable narrative area, an input field, and a dark-themed aesthetic.
 */
const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const currentInput = input;
    setInput('');
    setIsLoading(true);
    setMessages((prev) => [...prev, { role: 'user', content: currentInput }]);

    try {
      const result = await sendAction(currentInput);
      const content = result.text || result.message || JSON.stringify(result);
      setMessages((prev) => [...prev, { role: 'assistant', content }]);
    } catch (error) {
      console.error('Error sending action:', error);
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Error connecting to backend.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-black text-green-500 font-mono p-4 border-x border-green-900">
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto mb-4 space-y-2 border border-green-900 p-4 rounded bg-gray-900/50"
      >
        {messages.length === 0 && (
          <div className="opacity-50">
            Welcome to Shangri-la: Age of Steam. Type your first action below...
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === 'user' ? 'text-white' : 'text-green-400'}>
            <span className="opacity-50">
              {msg.role === 'user' ? '> ' : '[SYSTEM]: '}
            </span>
            {msg.content}
          </div>
        ))}
        {isLoading && (
          <div className="text-green-400 animate-pulse">
            [SYSTEM]: Processing...
          </div>
        )}
      </div

      <form onSubmit={handleSendMessage} className="flex gap-2 border-t border-green-900 pt-4">
        <span className="opacity-50">#</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 bg-black border border-green-900 text-green-500 px-4 py-2 focus:outline-none focus:border-green-500"
          placeholder="Enter your action..."
          autoComplete="off"
        />
        <button
          type="submit"
          disabled={isLoading}
          className={`px-4 py-2 font-bold transition-colors ${
            isLoading ? 'bg-gray-800 text-gray-500' : 'bg-green-900 text-black hover:bg-green-800'
          }`}
        >
          {isLoading ? 'WAIT' : 'EXECUTE'}
        </button>
      </form>
    </div>
  );
};

export default ChatInterface;
