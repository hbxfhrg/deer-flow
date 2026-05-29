import { ArrowLeft, Power, RefreshCw } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { MessageBubble } from '@/components/MessageBubble';
import { ReportPanel } from '@/components/ReportPanel';
import api from '../api';
import type { Message, EvaluationReport } from '@/types';

export function ResultPage() {
  const navigate = useNavigate();
  const params = useParams();
  const recordId = params.id;
  const [activeTab, setActiveTab] = useState<'conversation' | 'report'>('report'); // 默认显示报告
  const [messages, setMessages] = useState<Message[]>([]);
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isReportGenerating, setIsReportGenerating] = useState(true);
  const [generateProgress, setGenerateProgress] = useState(0);
  const [isRegenerating, setIsRegenerating] = useState(false);

  // 加载对话历史和报告
  useEffect(() => {
    if (!recordId) return;

    const loadData = async () => {
      setIsLoading(true);
      try {
        // 加载对话历史
        const result = await api.practice.history(Number(recordId));
        const history = result.history || [];
        const loadedMessages: Message[] = history.map((item: any, index: number) => ({
          id: `msg-${index}`,
          role: item.speaker === 1 ? 'user' : 'assistant',
          content: item.content,
          createdAt: item.create_time || new Date().toISOString(),
          roundNumber: item.round_number,
          evaluation: item.evaluation ? {
            score: item.evaluation.round_score,
            dimensionScores: item.evaluation.dimension_scores || {},
            summary: item.evaluation.feedback,
          } : undefined,
        }));
        setMessages(loadedMessages);

        // 尝试获取报告
        const reportResult = await api.practice.getReport(Number(recordId));
        // 检查报告是否完成：success=true 且 report 存在 或者 status=completed
        if ((reportResult.success && reportResult.report) || reportResult.status === 'completed') {
          if (reportResult.report) {
            setReport(reportResult.report);
          }
          setIsReportGenerating(false);
        } else {
          // 报告正在生成，轮询等待
          pollForReport(Number(recordId));
        }
      } catch (error) {
        console.error('Failed to load result:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [recordId]);

  // 轮询获取报告
  const pollForReport = async (recordId: number) => {
    const interval = setInterval(async () => {
      try {
        const reportResult = await api.practice.getReport(recordId);
        // 检查报告是否完成：success=true 且 report 存在 或者 status=completed
        if ((reportResult.success && reportResult.report) || reportResult.status === 'completed') {
          if (reportResult.report) {
            setReport(reportResult.report);
          }
          setIsReportGenerating(false);
          setIsRegenerating(false);  // 同时重置重新生成状态
          clearInterval(interval);
        } else {
          // 更新进度模拟
          setGenerateProgress(prev => Math.min(prev + 10, 90));
        }
      } catch (error) {
        clearInterval(interval);
        setIsRegenerating(false);  // 出错时也重置状态
      }
    }, 2000);
  };

  // 再来一次
  const handleRetry = () => {
    navigate('/');
  };

  // 生成后通知我
  const handleNotify = () => {
    alert('报告生成后将通知您');
  };

  // 重新生成报告
  const handleRegenerateReport = async () => {
    if (!recordId || isRegenerating) return;
    
    setIsRegenerating(true);
    setIsReportGenerating(true);
    setGenerateProgress(0);
    setReport(null);
    
    try {
      // 调用后端重新生成报告 API
      await api.practice.regenerateReport(Number(recordId));
      
      // 轮询获取新报告
      pollForReport(Number(recordId));
    } catch (error) {
      console.error('重新生成报告失败:', error);
      setIsRegenerating(false);
      setIsReportGenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-gray-500">正在加载结果...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gray-50">
      {/* 顶部导航 - 与系统风格一致 */}
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
              <h1 className="font-semibold text-gray-800">AI 对练</h1>
              <p className="text-xs text-gray-400">评测报告</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={handleRegenerateReport}
              disabled={isRegenerating || !report}
              className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="重新生成报告"
            >
              <RefreshCw className={`w-5 h-5 ${isRegenerating ? 'animate-spin' : ''}`} />
            </button>
            <button 
              onClick={() => navigate('/')}
              className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              title="退出"
            >
              <Power className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* 页签 - 与系统风格一致 */}
        <div className="flex justify-center mt-3 bg-gray-100 rounded-full p-1 w-fit mx-auto">
          <button
            onClick={() => setActiveTab('report')}
            className={`px-6 py-1.5 rounded-full text-sm font-medium transition-colors ${
              activeTab === 'report'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            报告
          </button>
          <button
            onClick={() => setActiveTab('conversation')}
            className={`px-6 py-1.5 rounded-full text-sm font-medium transition-colors ${
              activeTab === 'conversation'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            对话
          </button>
        </div>
      </header>

      {/* 主内容区 */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'report' ? (
          /* 报告页签 */
          <div className="bg-white">
            {/* 生成状态提示 */}
            {isReportGenerating && (
              <div className="bg-gray-50 border-b border-gray-100 px-4 py-3">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-700 font-medium">报告生成中...</span>
                  <span className="text-gray-500 text-sm">预计1-2分钟</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 transition-all duration-500 animate-pulse"
                    style={{ width: `${generateProgress > 80 ? 80 : generateProgress}%` }}
                  ></div>
                </div>
                <p className="text-gray-500 text-sm mt-2">
                  正在生成报告，请稍候...
                </p>
              </div>
            )}

            {/* 报告内容 */}
            {report ? (
              <ReportPanel report={report} onRegenerate={handleRegenerateReport} isRegenerating={isRegenerating} />
            ) : (
              <div className="flex flex-col items-center justify-center h-64 px-4">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                  <div className="w-8 h-8 border-4 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                </div>
                <p className="text-gray-500">报告生成中，请稍候...</p>
              </div>
            )}
          </div>
        ) : (
          /* 对话页签 */
          <div className="bg-gray-50">
            {messages.length > 0 ? (
              <div className="px-4 py-4">
                {messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    isTyping={false}
                    recordId={Number(recordId)}
                    isEvaluating={false}
                  />
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 px-4">
                <p className="text-gray-400">暂无对话记录</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 底部按钮 - 与系统风格一致 */}
      <div className="bg-white border-t border-gray-100 px-4 py-3 flex gap-3">
        <button
          onClick={handleRetry}
          className="flex-1 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
        >
          再来一次
        </button>
        <button
          onClick={handleNotify}
          disabled={!isReportGenerating}
          className="flex-1 py-3 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isReportGenerating ? '不等了，生成后通知我' : '分享报告'}
        </button>
      </div>
    </div>
  );
}
