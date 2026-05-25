import { ArrowLeft, HelpCircle, Settings, LogOut } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { MessageBubble } from '@/components/MessageBubble';
import { EvaluationCard } from '@/components/EvaluationCard';
import { ReportPanel } from '@/components/ReportPanel';
import { ChatInput } from '@/components/ChatInput';
import { useRoleplay } from '@/hooks/useRoleplay';
import api from '../api';
import type { Course } from '@/types';

export function ChatPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const courseId = searchParams.get('courseId');
  const recordId = searchParams.get('recordId');
  const [courseInfo, setCourseInfo] = useState<Course | null>(null);

  // 加载课程信息
  useEffect(() => {
    if (courseId) {
      api.courses.get(Number(courseId)).then(data => {
        if (data) setCourseInfo(data);
      }).catch(() => {});
    }
  }, [courseId]);

  const {
    messages,
    isLoading,
    isTyping,
    evaluation,
    report,
    isComplete,
    currentRound,
    totalRounds,
    initConversation,
    sendMessage,
    endPractice,
    messagesEndRef,
  } = useRoleplay(
    courseId ? Number(courseId) : null,
    recordId ? Number(recordId) : null
  );

  // 如果有recordId（从历史记录进入），自动初始化对话
  useEffect(() => {
    if (recordId) {
      initConversation();
    }
  }, [recordId, initConversation]);

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
              <h1 className="font-semibold text-gray-800">AI对练</h1>
              <p className="text-xs text-gray-400">提升您的专业技能</p>
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
              {/* 如果是从历史记录进入，显示加载状态 */}
              {recordId && isLoading ? (
                <div className="flex flex-col items-center">
                  <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mb-4"></div>
                  <p className="text-gray-500">正在加载对话历史...</p>
                </div>
              ) : (
                <>
                  {/* 场景信息 */}
                  {courseInfo?.sceneName && (
                    <div className="w-full max-w-md text-center mb-6">
                      <h2 className="text-xl font-bold text-gray-800 mb-2">{courseInfo.sceneName}</h2>
                      {courseInfo.sceneDescription && (
                        <p className="text-sm text-gray-500">{courseInfo.sceneDescription}</p>
                      )}
                    </div>
                  )}

                  <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center mb-4">
                    <div className="w-8 h-8 text-primary-500">
                      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                      </svg>
                    </div>
                  </div>
                  <h2 className="text-xl font-semibold text-gray-800 mb-2">准备开始对练</h2>
                  <p className="text-sm text-gray-500 text-center mb-6">
                    点击下方按钮开始您的练习之旅
                  </p>
                  <button
                    onClick={initConversation}
                    disabled={isLoading}
                    className="px-8 py-3 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? '初始化中...' : '开始对练'}
                  </button>
                </>
              )}
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto px-4 py-4">
              {messages.map((message, index) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  isTyping={isTyping && index === messages.length - 1 && message.role === 'assistant'}
                  recordId={Number(recordId) || undefined}
                  isEvaluating={message.isEvaluating}
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

          {/* 输入框 / 结束面板 */}
          {messages.length > 0 && !isComplete && (
            <ChatInput onSend={sendMessage} disabled={isLoading} />
          )}
          {messages.length > 0 && !isComplete && (
            <div className="bg-gray-50 border-t border-gray-100 px-4 py-2 flex items-center justify-between">
              <span className="text-xs text-gray-400">
                第 {currentRound} / {totalRounds} 轮
              </span>
              <button
                onClick={endPractice}
                disabled={isLoading}
                className="px-4 py-1.5 text-xs text-red-500 border border-red-200 rounded-lg hover:bg-red-50 transition-colors disabled:opacity-50"
              >
                结束对练
              </button>
            </div>
          )}
          {isComplete && (
            <div className="bg-green-50 border-t border-green-100 px-4 py-3 text-center">
              <span className="text-sm text-green-600 font-medium">✓ 对练已完成</span>
            </div>
          )}
        </div>

        {/* 右侧面板 */}
        <div className="w-80 bg-white border-l border-gray-100 p-4 overflow-y-auto hidden lg:block">
          {isComplete && report ? (
            <ReportPanel report={report} />
          ) : evaluation && !isComplete ? (
            <EvaluationCard evaluation={evaluation} status="completed" />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-3">
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <p className="text-xs">开始对话后将显示评估</p>
            </div>
          )}
        </div>
      </div>

      {/* 移动端：已完成的报告 */}
      {isComplete && report && (
        <div className="lg:hidden bg-white border-t border-gray-100 p-4 overflow-y-auto max-h-[50vh]">
          <ReportPanel report={report} />
        </div>
      )}


    </div>
  );
}
