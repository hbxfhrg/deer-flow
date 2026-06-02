import { useState, useEffect } from 'react';
import { User, Bot, Pencil, Sparkles, RotateCcw, Volume2 } from 'lucide-react';
import type { Message, MessageEvaluation } from '@/types';
import { api } from '@/api';

interface MessageBubbleProps {
  message: Message;
  isTyping?: boolean;
  recordId?: number;
  isEvaluating?: boolean; // 评价生成中状态
  onRetry?: () => void; // 重录回调
  practiceMode?: string; // 练习模式：text 或 voice
}

export function MessageBubble({ message, isTyping, recordId, isEvaluating, onRetry, practiceMode }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [isExpanded, setIsExpanded] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackProgress, setPlaybackProgress] = useState(0);
  
  // 计算语音时长（模拟）
  const getVoiceDuration = () => {
    // 根据文本长度估算语音时长（中文字符数 * 0.3 秒）
    if (!message.content) return 0;
    return Math.ceil(message.content.length * 0.3);
  };
  
  // 使用 Web Audio API 播放音频
  const handlePlayVoice = async () => {
    if (isPlaying) {
      // 停止播放
      setIsPlaying(false);
      setPlaybackProgress(0);
      return;
    }
    
    // 检查是否有音频URL
    if (!message.contentUrl) {
      console.warn('No audio URL available');
      return;
    }
    
    try {
      setIsPlaying(true);
      
      // 创建 Audio 对象播放实际音频
      const audio = new Audio(message.contentUrl);
      
      // 获取音频时长
      audio.onloadedmetadata = () => {
        const duration = audio.duration || getVoiceDuration() || 30;
        
        // 更新播放进度
        const updateProgress = () => {
          if (audio.currentTime > 0 && duration > 0) {
            setPlaybackProgress((audio.currentTime / duration) * 100);
          }
        };
        
        // 每100ms更新进度
        const interval = setInterval(updateProgress, 100);
        
        // 播放结束处理
        audio.onended = () => {
          clearInterval(interval);
          setIsPlaying(false);
          setPlaybackProgress(0);
        };
        
        // 播放错误处理
        audio.onerror = () => {
          clearInterval(interval);
          setIsPlaying(false);
          setPlaybackProgress(0);
          console.error('Failed to play audio');
        };
        
        // 开始播放
        audio.play().catch(err => {
          console.error('Playback failed:', err);
          clearInterval(interval);
          setIsPlaying(false);
          setPlaybackProgress(0);
        });
      };
      
      // 加载元数据失败时的回退
      audio.onerror = () => {
        setIsPlaying(false);
        console.error('Failed to load audio metadata');
      };
      
    } catch (error) {
      console.error('Error playing voice:', error);
      setIsPlaying(false);
    }
  };
  const [isLoading, setIsLoading] = useState(false);
  const [detailedEvaluation, setDetailedEvaluation] = useState<MessageEvaluation | null>(null);

  // 合并基础评价和详细评价
  const evaluation = {
    ...message.evaluation,
    ...detailedEvaluation,
  };

  // const hasEvaluation = isUser && (message.evaluation || detailedEvaluation);

  // 当展开时获取详细评价建议
  useEffect(() => {
    if (isExpanded && recordId && message.id && !detailedEvaluation) {
      const fetchSuggestions = async () => {
        setIsLoading(true);
        try {
          // 从 message.id 中提取 dialog_id（格式：msg-{dialog_id}）
          const dialogId = parseInt(message.id.replace('msg-', ''));
          // 检查 dialogId 是否有效
          if (isNaN(dialogId)) {
            console.warn('Invalid dialogId:', message.id);
            return;
          }
          const response = await api.practice.getSuggestions(recordId, dialogId);
          setDetailedEvaluation({
            suggestions: response.suggestions,
            polishedExpression: response.polishedExpression,
          });
        } catch (error) {
          console.error('Failed to fetch suggestions:', error);
        } finally {
          setIsLoading(false);
        }
      };
      fetchSuggestions();
    }
  }, [isExpanded, recordId, message.id, detailedEvaluation]);

  return (
    <div className={`flex mb-4 message-bubble ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`flex flex-col gap-2 max-w-[85%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* 消息主体 */}
        <div className={`flex items-start gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
          {/* 头像 */}
          <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
            isUser ? 'bg-primary-500' : 'bg-success-500'
          }`}>
            {isUser ? (
              <User className="w-5 h-5 text-white" />
            ) : (
              <Bot className="w-5 h-5 text-white" />
            )}
          </div>
          
          {/* 内容区域（语音标签 + 消息内容） */}
          <div className="flex flex-col gap-2">
            {/* 语音时长标签（语音模式下或消息为音频类型时显示） */}
            {String(message.contentType) === '2' && (
              <button 
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  backgroundColor: '#22c55e',
                  borderRadius: '9999px',
                  color: 'white',
                  fontSize: '14px',
                  cursor: 'pointer',
                  border: 'none',
                  outline: 'none',
                  width: '100%'
                }}
                onClick={() => {
                  console.log('Play voice clicked!', message.id);
                  handlePlayVoice();
                }}
              >
                <span style={{ fontSize: '18px' }}>{isPlaying ? '🎵' : '🔊'}</span>
                <span>{getVoiceDuration() || 30}"</span>
                {isPlaying && (
                  <div style={{
                    flex: 1,
                    height: '6px',
                    backgroundColor: 'rgba(255,255,255,0.3)',
                    borderRadius: '3px',
                    overflow: 'hidden',
                    marginLeft: '8px'
                  }}>
                    <div 
                      style={{
                        height: '100%',
                        backgroundColor: 'white',
                        borderRadius: '3px',
                        transition: 'width 0.1s',
                        width: `${playbackProgress}%`
                      }}
                    />
                  </div>
                )}
              </button>
            )}
            
            {/* 消息内容 */}
            <div className={`relative px-4 py-3 rounded-2xl ${
              isUser 
                ? 'bg-white text-gray-800 rounded-br-md border border-gray-100 shadow-sm' 
                : 'bg-success-500 text-white rounded-bl-md'
            }`}>
            {isTyping ? (
              <div className="flex items-center gap-1">
                <span className="w-2 h-2 bg-current rounded-full opacity-70 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-2 h-2 bg-current rounded-full opacity-70 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-2 h-2 bg-current rounded-full opacity-70 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            ) : (
              <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                {message.content}
              </p>
            )}

            {/* 用户消息下方的评价内容 */}
            {isUser && (
              <>
                {/* 评价生成中状态 */}
                {isEvaluating && (
                  <div className="flex items-center justify-between gap-2 mt-2 pt-2 border-t border-gray-100">
                    {onRetry && (
                      <button
                        onClick={onRetry}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-all"
                      >
                        <RotateCcw className="w-4 h-4" />
                        重录
                      </button>
                    )}
                    <div className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-green-600">
                      <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin"></div>
                      回答分析生成中...
                    </div>
                  </div>
                )}

                {/* 评价结果 - 默认只显示按钮 */}
                {!isEvaluating && message.evaluation && (
                  <>
                    {/* 默认状态：只显示重录和改进建议按钮 */}
                    <div className="flex items-center justify-between gap-2 mt-2 pt-2 border-t border-gray-100">
                      {onRetry && (
                        <button
                          onClick={onRetry}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-100 transition-all"
                        >
                          <RotateCcw className="w-4 h-4" />
                          重录
                        </button>
                      )}
                      <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                          isExpanded 
                            ? 'bg-green-500 text-white' 
                            : 'bg-green-50 text-green-600 hover:bg-green-100'
                        }`}
                      >
                        <Pencil className="w-4 h-4" />
                        {isExpanded ? '收起建议' : '改进建议'}
                      </button>
                    </div>

                    {/* 展开的评价详情 */}
                    {isExpanded && (
                      <div className="mt-2 pt-2 border-t border-gray-100 bg-gray-50 -mx-4 -mb-3 px-4 py-3 rounded-b-xl">
                        {isLoading ? (
                          <div className="flex justify-center py-2">
                            <div className="w-4 h-4 border-2 border-green-500 border-t-transparent rounded-full animate-spin"></div>
                          </div>
                        ) : (
                          <>
                            {/* 分数 */}
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-2">
                                <span className="text-2xl font-bold text-red-500">{message.evaluation?.score || message.evaluation?.roundScore || 0}</span>
                                <div className="flex">
                                  {[1, 2, 3, 4, 5].map((star) => (
                                    <span key={star} className={`text-lg ${star <= Math.ceil((message.evaluation?.score || message.evaluation?.roundScore || 0) / 20) ? 'text-yellow-400' : 'text-gray-200'}`}>★</span>
                                  ))}
                                </div>
                              </div>
                              <span className="text-xs text-gray-400">第 {message.roundNumber || 1} 轮</span>
                            </div>

                            {/* 维度得分 */}
                            {message.evaluation?.dimensionScores && (
                              <div className="mb-3">
                                {Object.entries(message.evaluation?.dimensionScores || {}).map(([dimension, score]) => (
                                  <div key={dimension} className="flex items-center justify-between text-xs text-gray-500 mb-1">
                                    <span>{dimension}</span>
                                    <div className="flex items-center gap-2">
                                      <div className="w-24 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                        <div 
                                          className="h-full bg-green-500 rounded-full" 
                                          style={{ width: `${score}%` }}
                                        />
                                      </div>
                                      <span className="text-green-600 font-medium">{score}</span>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}

                            {/* 总结 */}
                            {message.evaluation.summary && (
                              <p className="text-xs text-gray-600 leading-relaxed mb-3">
                                {message.evaluation.summary}
                              </p>
                            )}

                            {/* 改进建议 */}
                            {evaluation.suggestions && evaluation.suggestions.length > 0 && (
                              <div className="mb-3">
                                <div className="flex items-center gap-2 mb-2">
                                  <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
                                    <Pencil className="w-3 h-3 text-green-600" />
                                  </div>
                                  <span className="text-xs font-semibold text-gray-800">改进建议</span>
                                </div>
                                <div className="text-xs text-gray-600 leading-relaxed pl-7">
                                  {evaluation.suggestions.join('\n')}
                                </div>
                              </div>
                            )}

                            {/* 润色表达 */}
                            {evaluation.polishedExpression && (
                              <div>
                                <div className="flex items-center gap-2 mb-2">
                                  <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center">
                                    <Sparkles className="w-3 h-3 text-green-600" />
                                  </div>
                                  <span className="text-xs font-semibold text-gray-800">润色表达</span>
                                </div>
                                <div className="text-xs text-gray-600 leading-relaxed pl-7 whitespace-pre-wrap">
                                  {evaluation.polishedExpression}
                                </div>
                              </div>
                            )}
                          </>
                        )}
                      </div>
                    )}
                  </>
                )}
              </>
            )}
          </div>
          {/* 闭合内容区域容器 */}
        </div>
        {/* 闭合消息主体 */}
      </div>
      {/* 闭合内层容器 */}
    </div>
    {/* 闭合外层容器 */}
  </div>
  );
}