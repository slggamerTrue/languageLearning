import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Message } from '../types';

interface MessageDisplayProps {
  message: Message;
}

export const MessageDisplay: React.FC<MessageDisplayProps> = ({ message }) => {
  const isAssistant = message.role === 'assistant';
  const isWaiting = message.content === '正在准备评估...';

  return (
    <div className={`flex flex-col ${isAssistant ? 'items-start' : 'items-end'} w-full`}>
      {/* 如果是助手消息且有displayText，显示在单独的容器中 */}
      {isAssistant && message.displayText && (
        <div className="w-full max-w-[90%] mb-6 bg-white rounded-xl p-6">
          <div className="markdown-content prose prose-headings:text-blue-900 prose-headings:font-bold prose-headings:mb-4 prose-p:text-gray-900 prose-p:text-base prose-p:leading-relaxed prose-li:text-gray-900 prose-blockquote:text-gray-500 prose-blockquote:border-l-blue-500 max-w-none space-y-4">
            <ReactMarkdown>{message.displayText}</ReactMarkdown>
            {isWaiting && (
              <div className="flex items-center justify-center mt-4">
                <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full mr-2"></div>
                <span className="text-gray-500">正在准备中...</span>
              </div>
            )}
          </div>
        </div>
      )}
      {/* 主要消息内容 */}
      {!isWaiting && (
        <div
          className={`max-w-[80%] rounded-lg p-4 mt-2 ${
            isAssistant
              ? 'bg-white text-gray-900'
              : 'bg-blue-600 text-white'
          }`}
        >
          <div className="whitespace-pre-wrap">
            {isAssistant ? message.speechText || message.content : message.content}
          </div>
        </div>
      )}
    </div>
  );
};
