import { useState, KeyboardEvent } from 'react';
import { Send, Mic } from 'lucide-react';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  practiceMode?: string; // text | voice
}

export function ChatInput({ onSend, disabled, practiceMode = 'text' }: ChatInputProps) {
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
        {/* 输入框 - 仅文本模式显示 */}
        {practiceMode === 'text' && (
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
        )}

        {/* 语音按钮 - 仅语音模式显示 */}
        {practiceMode === 'voice' && (
          <button className="flex-1 flex items-center justify-center gap-2 py-4 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors">
            <Mic className="w-5 h-5" />
            <span className="text-sm font-medium">点击说话</span>
          </button>
        )}

        {/* 语音模式下的发送按钮不显示 */}
        {practiceMode === 'text' && (
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
        )}
      </div>
    </div>
  );
}