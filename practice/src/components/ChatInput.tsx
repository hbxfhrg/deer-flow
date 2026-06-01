import { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { Send, Mic, Square } from 'lucide-react';

interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  practiceMode?: string; // text | voice
}

export function ChatInput({ onSend, disabled, practiceMode = 'text' }: ChatInputProps) {
  const [content, setContent] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordDuration, setRecordDuration] = useState(0);
  const [, setRecordedAudio] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);

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

  // 开始录音
  const startRecording = () => {
    if (disabled) return;
    
    setIsRecording(true);
    setRecordDuration(0);
    setRecordedAudio(null);
    
    // 模拟录音计时
    timerRef.current = window.setInterval(() => {
      setRecordDuration(prev => prev + 1);
    }, 1000);
  };

  // 停止录音
  const stopRecording = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    setIsRecording(false);
    
    // 模拟语音转文字（实际项目中调用语音识别API）
    if (recordDuration > 0) {
      // 模拟识别结果
      const mockResult = `语音输入内容（时长${recordDuration}秒）`;
      setContent(mockResult);
      setRecordedAudio('data:audio/wav;base64,模拟音频数据');
    }
  };

  // 清理定时器
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  // 格式化时长显示
  const formatDuration = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="px-4 py-3">
      {/* 语音模式 - 录音按钮占满整行 */}
      {practiceMode === 'voice' && !content && (
        <button
          onClick={isRecording ? stopRecording : startRecording}
          disabled={disabled}
          className={`w-full flex items-center justify-center gap-3 py-4 rounded-xl transition-all font-medium ${
            isRecording
              ? 'bg-red-500 text-white animate-pulse'
              : 'bg-primary-500 text-white hover:bg-primary-600'
          } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          {isRecording ? (
            <>
              <Square className="w-5 h-5" />
              <span>{formatDuration(recordDuration)}</span>
              {/* 录音波形指示 */}
              <div className="flex items-center gap-0.5">
                {[1, 2, 3, 4, 5].map((i) => (
                  <span
                    key={i}
                    className="w-1 bg-white rounded-full animate-pulse"
                    style={{
                      height: `${8 + Math.random() * 12}px`,
                      animationDelay: `${i * 0.1}s`,
                    }}
                  />
                ))}
              </div>
            </>
          ) : (
            <>
              <Mic className="w-5 h-5" />
              <span>点击说话</span>
            </>
          )}
        </button>
      )}

      {/* 语音模式 - 识别结果输入框 */}
      {practiceMode === 'voice' && content && (
        <div className="flex items-end gap-3">
          <div className="flex-1 relative">
            <textarea
              value={content}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              placeholder="语音识别结果..."
              className="w-full px-4 py-3 bg-gray-50 rounded-xl text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              rows={1}
              style={{
                minHeight: '48px',
                maxHeight: '120px',
              }}
            />
          </div>
          <button
            onClick={handleSend}
            disabled={disabled || !content.trim()}
            className="p-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* 文本模式 - 输入框 */}
      {practiceMode === 'text' && (
        <div className="flex items-end gap-3">
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
          <button
            onClick={handleSend}
            disabled={disabled || !content.trim()}
            className="p-3 bg-primary-500 text-white rounded-xl hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      )}
    </div>
  );
}
