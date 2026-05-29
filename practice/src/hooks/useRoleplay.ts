import { useState, useCallback, useEffect, useRef } from 'react';
import api from '@/api';
import type { Message, Evaluation, EvaluationReport } from '@/types';

export function useRoleplay(courseId: number | null, existingRecordId: number | null = null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [recordId, setRecordId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [isEvaluating] = useState(false); // 评价生成中状态
  const [currentRound, setCurrentRound] = useState(0);
  const [totalRounds, setTotalRounds] = useState(0);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [showCompleteModal, setShowCompleteModal] = useState(false); // 对练完成模态框
  const [isReportReady, setIsReportReady] = useState(false); // 报告是否准备好
  const [pendingCompleteModal, setPendingCompleteModal] = useState(false); // 待显示的完成模态框（等待AI消息渲染）
  const [practiceMode, setPracticeMode] = useState<string>('text'); // 练习模式：text | voice
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // 自动滚动
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 等待消息渲染完成后显示完成模态框
  useEffect(() => {
    if (pendingCompleteModal && messages.length > 0) {
      // 使用 setTimeout 确保消息已经渲染到DOM
      const timer = setTimeout(() => {
        setShowCompleteModal(true);
        setPendingCompleteModal(false);
      }, 300); // 等待300ms确保DOM渲染完成
      return () => clearTimeout(timer);
    }
  }, [messages, pendingCompleteModal]);

  // 开始对练
  const initConversation = useCallback(async () => {
    if (!courseId && !existingRecordId) return;
    setIsLoading(true);
    setIsComplete(false);
    setReport(null);
    setEvaluation(null);
    try {
      if (existingRecordId) {
        // 从历史记录继续
        await resumeConversation(existingRecordId);
      } else {
        // 开始新对练
        const res = await api.practice.start(courseId!);
        setRecordId(res.recordId);
        setTotalRounds(res.totalRounds);
        setCurrentRound(1);
        setPracticeMode(res.practiceMode || 'text');
        const aiMsg: Message = {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: res.customerMessage,
          createdAt: new Date().toISOString(),
        };
        setMessages([aiMsg]);
      }
    } catch (e) {
      console.error('Failed to start practice:', e);
    } finally {
      setIsLoading(false);
    }
  }, [courseId, existingRecordId]);

  // 从历史记录恢复对话
  const resumeConversation = useCallback(async (existingRecordId: number) => {
    try {
      // 获取对话历史
      const result = await api.practice.history(existingRecordId);
      const history = result.history;
      const loadedMessages: Message[] = history.map((item: any, index: number) => ({
        id: `msg-${index}`,
        role: item.speaker === 1 ? 'user' : 'assistant',
        content: item.content,
        createdAt: item.create_time || new Date().toISOString(),
      }));
      setMessages(loadedMessages);
      setRecordId(existingRecordId);
      
      // 获取最后一条消息的轮次作为当前轮次
      if (history.length > 0) {
        const lastRound = history[history.length - 1].round_number;
        setCurrentRound(lastRound);
      }
      
      // 从后端获取总轮次
      if (result.totalRounds) {
        setTotalRounds(result.totalRounds);
      } else {
        // 默认总轮次为5（自由式对练）
        setTotalRounds(5);
      }
    } catch (e) {
      console.error('Failed to resume conversation:', e);
    }
  }, []);

  // 发送消息
  const sendMessage = useCallback(async (content: string) => {
    if (!recordId || isLoading || content.trim() === '') return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      createdAt: new Date().toISOString(),
      isEvaluating: true, // 标记正在评价中
      roundNumber: currentRound,
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setIsTyping(true);

    try {
      const res = await api.practice.turn(recordId, content.trim());

      // 更新最新消息的评价数据
      setMessages(prev => {
        const updated = [...prev];
        const lastMsgIndex = updated.findIndex(m => m.id === userMsg.id);
        if (lastMsgIndex !== -1 && res.evaluation) {
          updated[lastMsgIndex] = {
            ...updated[lastMsgIndex],
            isEvaluating: false, // 评价完成
            evaluation: {
              score: res.evaluation.roundScore,
              dimensionScores: res.evaluation.dimensionScores,
              summary: res.evaluation.feedback,
            },
          };
        }
        return updated;
      });

      // 更新评估
      if (res.evaluation) {
        setEvaluation({
          round: res.round,
          total_score: res.evaluation.roundScore,
          dimension_scores: res.evaluation.dimensionScores,
          strengths: [],
          improvements: [],
          summary: res.evaluation.feedback,
        });
      }

      // 客户回复（无论是否完成都显示，包括结束语）
      if (res.customerMessage && res.customerMessage.trim()) {
        const aiMsg: Message = {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: res.customerMessage,
          createdAt: new Date().toISOString(),
          roundNumber: res.round,
        };
        setMessages(prev => [...prev, aiMsg]);
      }

      setCurrentRound(res.round);
      if (res.totalRounds) {
        setTotalRounds(res.totalRounds);
      }

      if (res.isComplete) {
        setIsComplete(true);
        if (res.report) {
          setReport(res.report);
          setIsReportReady(true);
        } else {
          setIsReportReady(false);
        }
        // 将需要显示模态框的请求存入状态，等待消息渲染完成后再显示
        setPendingCompleteModal(true);
      }
    } catch (e) {
      console.error('Failed to send message:', e);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  }, [recordId, isLoading, currentRound]);

  // 手动结束对练
  const endPractice = useCallback(async () => {
    if (!recordId) return;
    setIsLoading(true);
    try {
      const res = await api.practice.end(recordId);
      setIsComplete(true);
      setReport(res.report);
    } catch (e) {
      console.error('Failed to end practice:', e);
    } finally {
      setIsLoading(false);
    }
  }, [recordId]);

  // 重置状态（用于重新开始）
  const reset = useCallback(() => {
    setMessages([]);
    setRecordId(null);
    setIsComplete(false);
    setReport(null);
    setEvaluation(null);
    setCurrentRound(0);
    setTotalRounds(0);
    setShowCompleteModal(false);
    setIsReportReady(false);
  }, []);

  // 关闭完成模态框（不跳转）
  const closeCompleteModal = useCallback(() => {
    setShowCompleteModal(false);
  }, []);

  // 确认完成并关闭模态框（用于外部跳转）
  const confirmComplete = useCallback(() => {
    setShowCompleteModal(false);
  }, []);

  return {
    messages,
    isLoading,
    isTyping,
    isEvaluating,
    evaluation,
    report,
    isComplete,
    currentRound,
    totalRounds,
    recordId,
    showCompleteModal,
    isReportReady,
    practiceMode,
    initConversation,
    sendMessage,
    endPractice,
    reset,
    closeCompleteModal,
    confirmComplete,
    messagesEndRef,
  };
}