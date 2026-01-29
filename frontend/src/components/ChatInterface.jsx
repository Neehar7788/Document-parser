import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, AlertCircle } from 'lucide-react';
import ChatMessage from './ChatMessage';
import SourceCard from './SourceCard';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentSources, setCurrentSources] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);
    setCurrentSources([]);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        question: userMessage.content,
        conversation_history: messages.slice(-10), // Last 10 messages for context
        top_k: 5
      });

      const assistantMessage = {
        role: 'assistant',
        content: response.data.answer,
        timestamp: new Date().toISOString(),
        keywords: response.data.query_keywords
      };

      setMessages(prev => [...prev, assistantMessage]);
      setCurrentSources(response.data.sources);
    } catch (err) {
      console.error('Chat error:', err);
      setError(err.response?.data?.detail || 'Failed to get response. Please try again.');
      
      const errorMessage = {
        role: 'assistant',
        content: '❌ Sorry, I encountered an error. Please try again or rephrase your question.',
        timestamp: new Date().toISOString(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setCurrentSources([]);
    setError(null);
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center max-w-md">
                <div className="bg-primary-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Send className="w-10 h-10 text-primary-600" />
                </div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">
                  Ask me anything about your documents
                </h2>
                <p className="text-gray-600 mb-6">
                  I can help you find information, analyze data, and answer questions from your document collection.
                </p>
                <div className="grid grid-cols-1 gap-2 text-sm">
                  <div className="bg-white p-3 rounded-lg border border-gray-200 text-left">
                    <p className="text-gray-700">💡 "What was the revenue in Q4 2023?"</p>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-gray-200 text-left">
                    <p className="text-gray-700">📊 "Show me the profit margins from the annual report"</p>
                  </div>
                  <div className="bg-white p-3 rounded-lg border border-gray-200 text-left">
                    <p className="text-gray-700">🔍 "Summarize the key financial metrics"</p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((message, index) => (
                <ChatMessage key={index} message={message} />
              ))}
              {loading && (
                <div className="flex items-center gap-3 text-gray-600">
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Searching documents and generating response...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="px-4 py-2 bg-red-50 border-t border-red-200">
            <div className="max-w-4xl mx-auto flex items-center gap-2 text-red-700">
              <AlertCircle className="w-5 h-5" />
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="border-t border-gray-200 bg-white px-4 py-4">
          <div className="max-w-4xl mx-auto">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a question about your documents..."
                className="flex-1 resize-none rounded-lg border border-gray-300 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                rows="1"
                style={{ minHeight: '48px', maxHeight: '120px' }}
                disabled={loading}
              />
              <button
                type="submit"
                disabled={!input.trim() || loading}
                className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
                <span className="hidden sm:inline">Send</span>
              </button>
            </form>
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                className="mt-2 text-sm text-gray-600 hover:text-gray-800"
              >
                Clear chat
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Sources Sidebar */}
      {currentSources.length > 0 && (
        <div className="w-96 border-l border-gray-200 bg-white overflow-y-auto">
          <div className="p-4 border-b border-gray-200 bg-gray-50">
            <h3 className="font-semibold text-gray-900">Sources ({currentSources.length})</h3>
            <p className="text-sm text-gray-600 mt-1">
              Documents used to generate the response
            </p>
          </div>
          <div className="p-4 space-y-3">
            {currentSources.map((source, index) => (
              <SourceCard key={index} source={source} index={index} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ChatInterface;
