import React from 'react';
import { User, Bot, Tag } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const isError = message.isError;

  return (
    <div className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
          isError ? 'bg-red-100' : 'bg-primary-100'
        }`}>
          <Bot className={`w-6 h-6 ${isError ? 'text-red-600' : 'text-primary-600'}`} />
        </div>
      )}

      <div className={`flex-1 max-w-3xl ${isUser ? 'flex justify-end' : ''}`}>
        <div
          className={`rounded-lg px-4 py-3 ${
            isUser
              ? 'bg-primary-600 text-white'
              : isError
              ? 'bg-red-50 border border-red-200'
              : 'bg-white border border-gray-200 shadow-sm'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className={`markdown-content ${isError ? 'text-red-800' : ''}`}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Keywords Display */}
          {message.keywords && message.keywords.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="flex items-center gap-2 flex-wrap">
                <Tag className="w-4 h-4 text-gray-500" />
                <span className="text-xs text-gray-600 font-medium">Keywords:</span>
                {message.keywords.map((keyword, idx) => (
                  <span
                    key={idx}
                    className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
                  >
                    {keyword}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Timestamp */}
          <div className={`text-xs mt-2 ${isUser ? 'text-primary-100' : 'text-gray-500'}`}>
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center">
          <User className="w-6 h-6 text-white" />
        </div>
      )}
    </div>
  );
}

export default ChatMessage;
