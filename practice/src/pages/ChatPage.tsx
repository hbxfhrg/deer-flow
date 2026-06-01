import { ArrowLeft, Power } from 'lucide-react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { MessageBubble } from '@/components/MessageBubble';
import { EvaluationCard } from '@/components/EvaluationCard';
import { ChatInput } from '@/components/ChatInput';
import { InspirationPanel } from '@/components/InspirationPanel';
import { useRoleplay } from '@/hooks/useRoleplay';
import api from '../api';
import type { Course, Scene } from '@/types';

export function ChatPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const courseId = searchParams.get('courseId');
  const recordId = searchParams.get('recordId');
  const [courseInfo, setCourseInfo] = useState<Course | null>(null);
  const [sceneInfo, setSceneInfo] = useState<Scene | null>(null);
  const [showEndConfirm, setShowEndConfirm] = useState(false);

  // 加载课程信息
  useEffect(() => {
    if (courseId) {
      api.courses.get(Number(courseId)).then(data => {
        if (data) {
          setCourseInfo(data);
          // 如果课程有场景ID，加载场景信息
          if (data.sceneId) {
            api.scenes.get(String(data.sceneId)).then(scene => {
              if (scene) setSceneInfo(scene);
            }).catch(() => {});
          }
        }
      }).catch(() => {});
    }
  }, [courseId]);

  const {
    messages,
    isLoading,
    isTyping,
    evaluation,
    isComplete,
    currentRound,
    totalRounds,
    recordId: currentRecordId,
    showCompleteModal,
    isReportReady,
    practiceMode,
    initConversation,
    sendMessage,
    endPractice,
    confirmComplete,
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

  // 点击确认按钮后跳转到结果页面
  const handleConfirmComplete = () => {
    confirmComplete();
    if (currentRecordId) {
      navigate(`/result?recordId=${currentRecordId}`);
    }
  };

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
            {/* 轮次显示 */}
            {messages.length > 0 && (
              <div className="px-3 py-1.5 bg-gray-100 rounded-full">
                <span className="text-xs text-gray-600">
                  {currentRound}/{totalRounds}
                </span>
              </div>
            )}
            {/* 结束对练按钮 - 电源符号 */}
            {messages.length > 0 && !isComplete && (
              <button
                onClick={() => setShowEndConfirm(true)}
                disabled={isLoading}
                className="p-2 text-gray-400 hover:text-danger-500 hover:bg-danger-50 rounded-lg transition-colors disabled:opacity-50"
                title="结束对练"
              >
                <Power className="w-5 h-5" />
              </button>
            )}
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
                  practiceMode={practiceMode}
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
            <div className="relative px-4 pb-4">
              <div className="flex items-center gap-3">
                <InspirationPanel
                  recordId={currentRecordId}
                  knowledgeBase={sceneInfo?.knowledgeBase}
                  summaryText={sceneInfo?.summaryText}
                />
                <div className="flex-1">
                  <ChatInput onSend={sendMessage} disabled={isLoading} practiceMode={practiceMode} />
                </div>
              </div>
            </div>
          )}

          {isComplete && (
            <div className="bg-green-50 border-t border-green-100 px-4 py-3 text-center">
              <span className="text-sm text-green-600 font-medium">✓ 对练已完成，正在跳转...</span>
            </div>
          )}
        </div>

        {/* 右侧面板 - 评估信息 */}
        <div className="w-80 bg-white border-l border-gray-100 p-4 overflow-y-auto hidden lg:block">
          {evaluation && !isComplete ? (
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

      {/* 对练完成模态框 */}
      {showCompleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm overflow-hidden">
            {/* 图标 */}
            <div className="flex justify-center pt-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            
            {/* 标题和描述 */}
            <div className="text-center px-6 py-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">本轮对练已结束</h3>
              <p className="text-sm text-gray-500">
                {isReportReady ? '查看评测报告' : '评测报告生成中...'}
              </p>
            </div>
            
            {/* 按钮 */}
            <div className="px-6 pb-6">
              <button
                onClick={handleConfirmComplete}
                disabled={!isReportReady}
                className="w-full py-3 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isReportReady ? (
                  '查看评测报告'
                ) : (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    生成中
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 结束对练确认对话框 */}
      {showEndConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm overflow-hidden">
            {/* 图标 */}
            <div className="flex justify-center pt-6">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-orange-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
            </div>
            
            {/* 标题和描述 */}
            <div className="text-center px-6 py-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">确定要结束这次练习吗？</h3>
              <p className="text-sm text-gray-500">
                结束后将跳转到评测报告页面
              </p>
            </div>
            
            {/* 按钮 */}
            <div className="px-6 pb-6 space-y-3">
              <button
                onClick={() => {
                  endPractice();
                  setShowEndConfirm(false);
                }}
                disabled={isLoading}
                className="w-full py-3 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                结束对话，并查看评测报告
              </button>
              <button
                onClick={() => setShowEndConfirm(false)}
                className="w-full py-3 bg-gray-100 text-gray-600 rounded-xl font-medium hover:bg-gray-200 transition-colors"
              >
                继续练习
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
