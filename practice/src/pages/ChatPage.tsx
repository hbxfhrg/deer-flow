import { ArrowLeft, RefreshCw, HelpCircle, Settings, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { MessageBubble } from '@/components/MessageBubble';
import { EvaluationCard } from '@/components/EvaluationCard';
import { ChatInput } from '@/components/ChatInput';
import { useRoleplay } from '@/hooks/useRoleplay';

export function ChatPage() {
  const navigate = useNavigate();
  const {
    messages,
    isLoading,
    isTyping,
    evaluation,
    evaluationStatus,
    initConversation,
    sendMessage,
    messagesEndRef,
  } = useRoleplay();

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* 顶部导航 */}
      <header className="bg-white border-b border-gray-100 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* 返回按钮 */}
            <button
              onClick={() => navigate('/')}
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </button>
            <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-lg">D</span>
            </div>
            <div>
              <h1 className="font-semibold text-gray-800">销售对练</h1>
              <p className="text-xs text-gray-400">提升您的沟通技巧</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
              <HelpCircle className="w-5 h-5" />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
              <Settings className="w-5 h-5" />
            </button>
            <button className="p-2 text-gray-400 hover:text-danger-500 hover:bg-danger-50 rounded-lg transition-colors">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 消息列表 */}
        <div className="flex-1 flex flex-col">
          {/* 开始按钮 */}
          {messages.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center px-4">
              <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mb-4">
                <RefreshCw className="w-8 h-8 text-primary-500" />
              </div>
              <h2 className="text-xl font-semibold text-gray-800 mb-2">准备开始对练</h2>
              <p className="text-sm text-gray-500 text-center mb-6">
                点击下方按钮开始您的销售技巧训练之旅
              </p>
              <button
                onClick={initConversation}
                disabled={isLoading}
                className="px-8 py-3 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? '初始化中...' : '开始对练'}
              </button>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto px-4 py-4">
              {messages.map((message, index) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  isTyping={isTyping && index === messages.length - 1 && message.role === 'assistant'}
                />
              ))}
              {isTyping && (
                <div className="flex justify-start">
                  <div className="flex items-end gap-2 max-w-[85%]">
                    <div className="w-10 h-10 rounded-full bg-success-500 flex items-center justify-center flex-shrink-0">
                      <span className="text-white text-sm">AI</span>
                    </div>
                    <div className="bg-white px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
                      <div className="flex items-center gap-1">
                        <span className="w-2 h-2 bg-gray-400 rounded-full opacity-70 animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-2 h-2 bg-gray-400 rounded-full opacity-70 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-2 h-2 bg-gray-400 rounded-full opacity-70 animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}

          {/* 输入框 */}
          {messages.length > 0 && (
            <ChatInput onSend={sendMessage} disabled={isLoading} />
          )}
        </div>

        {/* 评估面板（右侧） */}
        {messages.length > 0 && (
          <div className="w-72 bg-gray-50 border-l border-gray-100 p-4 overflow-y-auto hidden lg:block">
            <div className="sticky top-0 bg-gray-50 pb-2">
              <h2 className="font-semibold text-gray-800 mb-2">评估面板</h2>
            </div>
            <EvaluationCard evaluation={evaluation ?? {}} status={evaluationStatus ?? 'not_found'} />
          </div>
        )}
      </div>

      {/* 移动端评估面板 */}
      {messages.length > 0 && evaluation && (
        <div className="lg:hidden bg-white border-t border-gray-100 p-4">
          <EvaluationCard evaluation={evaluation} status="completed" />
        </div>
      )}
    </div>
  );
}