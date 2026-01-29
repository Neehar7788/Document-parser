import React from 'react';
import { 
  Menu, 
  X, 
  Database, 
  FileText, 
  Layers, 
  Activity,
  Github,
  ExternalLink
} from 'lucide-react';

function Sidebar({ isOpen, onToggle, stats, lastUpdate }) {
  // Format last update time
  const formatLastUpdate = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    
    if (diffSecs < 60) return 'Just now';
    if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`;
    
    return date.toLocaleTimeString();
  };

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={onToggle}
        className="fixed top-4 left-4 z-50 lg:hidden bg-white p-2 rounded-lg shadow-lg border border-gray-200"
      >
        {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
      </button>

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:relative inset-y-0 left-0 z-40
          w-80 bg-white border-r border-gray-200 
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          flex flex-col
        `}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Document Database</h2>
          <p className="text-sm text-gray-600 mt-1">System Overview</p>
          {lastUpdate && (
            <p className="text-xs text-gray-500 mt-2">
              Last updated: {formatLastUpdate(lastUpdate)}
            </p>
          )}
        </div>

        {/* Stats */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {stats ? (
            <>
              {/* Total Chunks */}
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200">
                <div className="flex items-center gap-3 mb-2">
                  <div className="bg-blue-500 p-2 rounded-lg">
                    <Database className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="font-semibold text-gray-900">Total Chunks</h3>
                </div>
                <p className="text-3xl font-bold text-blue-600">
                  {stats.total_chunks?.toLocaleString() || '0'}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  Indexed document chunks
                </p>
              </div>

              {/* Unique Files */}
              <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200">
                <div className="flex items-center gap-3 mb-2">
                  <div className="bg-green-500 p-2 rounded-lg">
                    <FileText className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="font-semibold text-gray-900">Documents</h3>
                </div>
                <p className="text-3xl font-bold text-green-600">
                  {stats.unique_files?.toLocaleString() || '0'}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  Unique PDF files
                </p>
              </div>

              {/* Models Info */}
              <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4 border border-purple-200">
                <div className="flex items-center gap-3 mb-2">
                  <div className="bg-purple-500 p-2 rounded-lg">
                    <Layers className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="font-semibold text-gray-900">AI Models</h3>
                </div>
                <div className="space-y-2 mt-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Embeddings:</span>
                    <span className="font-medium text-gray-900">
                      {stats.embedding_model || 'N/A'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">LLM:</span>
                    <span className="font-medium text-gray-900">
                      {stats.llm_model || 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {/* System Status */}
              <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4 border border-gray-200">
                <div className="flex items-center gap-3 mb-2">
                  <div className="bg-gray-500 p-2 rounded-lg">
                    <Activity className="w-5 h-5 text-white" />
                  </div>
                  <h3 className="font-semibold text-gray-900">System Status</h3>
                </div>
                <div className="space-y-2 mt-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Database:</span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                      <span className="font-medium text-green-600">Connected</span>
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">API:</span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                      <span className="font-medium text-green-600">Online</span>
                    </span>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            </div>
          )}

          {/* Features */}
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-3">Features</h3>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Hybrid search (vector + keyword)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Context-aware responses</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Source citations</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Financial keyword extraction</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">✓</span>
                <span>Multi-document support</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 space-y-3">
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
          >
            <Github className="w-4 h-4" />
            <span>View on GitHub</span>
            <ExternalLink className="w-3 h-3" />
          </a>
          <div className="text-xs text-gray-500">
            Powered by Gemini AI & Supabase
          </div>
        </div>
      </aside>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
          onClick={onToggle}
        />
      )}
    </>
  );
}

export default Sidebar;
