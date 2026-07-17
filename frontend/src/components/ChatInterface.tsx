import React, { useState, useEffect, useRef } from 'react';
import { sendAction } from '../api';

export default function ChatInterface() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

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
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Error.' }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', backgroundColor: 'black', color: 'green', minHeight: '100vh' }}>
      <div ref={scrollRef} style={{ height: '80vh', overflowY: 'auto', marginBottom: '20px', border: '1px solid green', padding: '10px' }}>
        {messages.map((msg, i) => (
          <div key={i}>
            {msg.content}
          </div>
        ))}
        {isLoading && <div>Loading...</div>}
      </div>
      <form onSubmit={handleSendMessage}>
        <input type="text" value={input} onChange={(e) => setInput(e.target.value)} />
        <button type="submit">Send</button>
      </form>
    </div>
  );
};
