import { useState, KeyboardEvent } from 'react';
import { Send, Mic, Smile } from 'lucide-react';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [content, setContent] = useState('');

  const handleSend = () => {
    if (content.trim() && !disabled) {
      onSend(content);
      setContent('');
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
  };

  return (
    <div className="bg-white border-t border-gray-100 px-4 py-3">
      <div className="flex items-end gap-3">
        {/* 表情按钮 */}
        <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0">
          <Smile className="w-5 h-5" />
        </button>

        {/* 输入框 */}
        <div className="flex-1 relative">
          <textarea
            value={content}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="输入您的回复..."
            className="w-full px-4 py-3 bg-gray-50 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            rows={1}
            style={{
              minHeight: '48px',
              maxHeight: '120px',
            }}
          />
        </div>

        {/* 语音按钮 */}
        <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0">
          <Mic className="w-5 h-5" />
        </button>

        {/* 发送按钮 */}
        <button
          onClick={handleSend}
          disabled={!content.trim() || disabled}
          className={`p-3 rounded-xl transition-all flex-shrink-0 ${
            content.trim() && !disabled
              ? 'bg-primary-500 text-white hover:bg-primary-600'
              : 'bg-gray-100 text-gray-300 cursor-not-allowed'
          }`}
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}