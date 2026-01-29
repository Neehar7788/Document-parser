import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, Tag } from 'lucide-react';

function SourceCard({ source, index }) {
  const [expanded, setExpanded] = useState(false);

  const getTypeColor = (type) => {
    switch (type) {
      case 'text':
        return 'bg-blue-100 text-blue-700';
      case 'table':
        return 'bg-green-100 text-green-700';
      case 'image':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getSimilarityColor = (score) => {
    if (score >= 0.7) return 'text-green-600';
    if (score >= 0.5) return 'text-yellow-600';
    return 'text-orange-600';
  };

  return (
    <div className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
      {/* Header */}
      <div className="p-3 bg-white border-b border-gray-200">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
            <FileText className="w-5 h-5 text-primary-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="font-medium text-gray-900 text-sm truncate">
              {source.file_name}
            </h4>
            <div className="flex items-center gap-2 mt-1 flex-wrap">
              <span className="text-xs text-gray-600">Page {source.page_num}</span>
              <span className={`text-xs px-2 py-0.5 rounded ${getTypeColor(source.chunk_type)}`}>
                {source.chunk_type}
              </span>
              <span className={`text-xs font-medium ${getSimilarityColor(source.similarity_score)}`}>
                {(source.similarity_score * 100).toFixed(1)}% match
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Content Preview */}
      <div className="p-3">
        <p className="text-sm text-gray-700 line-clamp-3">
          {source.chunk_text}
        </p>
        
        {/* Expand Button */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1"
        >
          {expanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              Show less
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              Show more
            </>
          )}
        </button>

        {/* Expanded Content */}
        {expanded && (
          <div className="mt-3 pt-3 border-t border-gray-200 space-y-3">
            <div>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {source.chunk_text}
              </p>
            </div>

            {/* Keywords */}
            {source.keywords && source.keywords.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Tag className="w-4 h-4 text-gray-500" />
                  <span className="text-xs font-medium text-gray-700">Keywords:</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {source.keywords.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="text-xs bg-white border border-gray-300 text-gray-700 px-2 py-1 rounded"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Financial Keywords */}
            {source.financial_keywords && source.financial_keywords.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Tag className="w-4 h-4 text-green-600" />
                  <span className="text-xs font-medium text-gray-700">Financial Keywords:</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {source.financial_keywords.map((keyword, idx) => (
                    <span
                      key={idx}
                      className="text-xs bg-green-50 border border-green-300 text-green-700 px-2 py-1 rounded"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="text-xs text-gray-600 space-y-1">
              <div>Chunk ID: {source.chunk_id}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default SourceCard;
