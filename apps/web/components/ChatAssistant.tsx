'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Loader2, User, Bot } from 'lucide-react';
import axios from 'axios';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export function ChatAssistant({ solutionId, isOpen, onClose }: { solutionId: string, isOpen: boolean, onClose: () => void }) {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hi! I can help you analyze this data graph. Ask me anything!' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) {
        scrollToBottom();
    }
  }, [messages, isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      // Use local Next.js API Route (Proxy) to avoid CORS issues
      const response = await axios.post(`/api/solutions/${solutionId}/chat`, {
        question: userMsg
      });
      
      setMessages(prev => [...prev, { role: 'assistant', content: response.data.answer }]);
    } catch (error) {
      console.error("Chat error:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I couldn't connect to the server." }]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col items-end pointer-events-auto">
      {/* Chat Window */}
        <div className="bg-white dark:bg-zinc-900 border shadow-2xl rounded-lg w-80 md:w-96 h-[500px] flex flex-col mb-4 overflow-hidden animate-in slide-in-from-bottom-5 fade-in duration-200">
          {/* Header */}
          <div className="bg-blue-600 p-4 flex justify-between items-center text-white">
            <h3 className="font-semibold flex items-center gap-2">
              <Bot size={20} /> Data Assistant
            </h3>
            <button 
              onClick={onClose}
              className="hover:bg-blue-700 p-1 rounded transition-colors"
            >
              <X size={18} />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50 dark:bg-zinc-950">
            {messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                    <Bot size={14} className="text-blue-600" />
                  </div>
                )}
                <div 
                  className={`max-w-[80%] p-3 rounded-lg text-sm ${
                    msg.role === 'user' 
                      ? 'bg-blue-600 text-white rounded-br-none' 
                      : 'bg-white dark:bg-zinc-800 border dark:border-zinc-700 shadow-sm rounded-bl-none'
                  }`}
                >
                  {msg.content}
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
                    <User size={14} className="text-gray-600" />
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <div className="flex gap-3 justify-start">
                 <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                    <Bot size={14} className="text-blue-600" />
                  </div>
                  <div className="bg-white dark:bg-zinc-800 p-3 rounded-lg rounded-bl-none border shadow-sm">
                    <Loader2 size={16} className="animate-spin text-gray-500" />
                  </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={handleSubmit} className="p-3 bg-white dark:bg-zinc-900 border-t flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your data..."
              className="flex-1 text-sm border rounded-md px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500 dark:bg-zinc-800 dark:border-zinc-700"
            />
            <button 
              type="submit" 
              disabled={loading || !input.trim()}
              className="bg-blue-600 text-white p-2 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              <Send size={18} />
            </button>
          </form>
        </div>
    </div>
  );
}