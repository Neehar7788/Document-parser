import React, { useState, useEffect, useRef } from 'react';
import ChatInterface from './components/ChatInterface';
import Sidebar from './components/Sidebar';
import { MessageSquare } from 'lucide-react';
import config from './config';

function App() {
  const [stats, setStats] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(null);
  const pollIntervalRef = useRef(null);

  // Initial fetch on mount
  useEffect(() => {
    fetchStats();
    
    // Set up polling interval (only if enabled)
    if (config.STATS_POLL_INTERVAL > 0) {
      pollIntervalRef.current = setInterval(() => {
        fetchStats();
      }, config.STATS_POLL_INTERVAL);
    }

    // Cleanup interval on unmount
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${config.API_BASE_URL}/stats`);
      const data = await response.json();
      
      // Check if stats have changed
      const hasChanged = !stats || 
        stats.total_chunks !== data.total_chunks || 
        stats.unique_files !== data.unique_files;
      
      if (hasChanged && stats) {
        console.log('📊 Database updated:', {
          chunks: `${stats.total_chunks} → ${data.total_chunks}`,
          files: `${stats.unique_files} → ${data.unique_files}`
        });
      }
      
      setStats(data);
      setLastUpdate(new Date().toISOString());
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <Sidebar 
        isOpen={sidebarOpen} 
        onToggle={() => setSidebarOpen(!sidebarOpen)}
        stats={stats}
        lastUpdate={lastUpdate}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="bg-primary-500 p-2 rounded-lg">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Document Chatbot</h1>
              <p className="text-sm text-gray-600">
                AI-powered assistant for your documents
              </p>
            </div>
          </div>
        </header>

        {/* Chat Interface */}
        <ChatInterface />
      </div>
    </div>
  );
}

export default App;
