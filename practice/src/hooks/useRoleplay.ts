import { useState, useCallback, useEffect, useRef } from 'react';
import api from '@/api';
import type { Message, Evaluation, EvaluationReport } from '@/types';

export function useRoleplay(courseId: number | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [recordId, setRecordId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [currentRound, setCurrentRound] = useState(0);
  const [totalRounds, setTotalRounds] = useState(0);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [report, setReport] = useState<EvaluationReport | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // 自动滚动
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 开始对练
  const initConversation = useCallback(async () => {
    if (!courseId) return;
    setIsLoading(true);
    setIsComplete(false);
    setReport(null);
    setEvaluation(null);
    try {
      const res = await api.practice.start(courseId);
      setRecordId(res.recordId);
      setTotalRounds(res.totalRounds);
      setCurrentRound(1);
      const aiMsg: Message = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: res.customerMessage,
        createdAt: new Date().toISOString(),
      };
      setMessages([aiMsg]);
    } catch (e) {
      console.error('Failed to start practice:', e);
    } finally {
      setIsLoading(false);
    }
  }, [courseId]);

  // 发送消息
  const sendMessage = useCallback(async (content: string) => {
    if (!recordId || isLoading || content.trim() === '') return;

    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      createdAt: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setIsTyping(true);

    try {
      const res = await api.practice.turn(recordId, content.trim());

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

      // 客户回复
      if (res.customerMessage) {
        const aiMsg: Message = {
          id: `ai-${Date.now()}`,
          role: 'assistant',
          content: res.customerMessage,
          createdAt: new Date().toISOString(),
        };
        setMessages(prev => [...prev, aiMsg]);
      }

      setCurrentRound(res.round);

      if (res.isComplete) {
        setIsComplete(true);
        if (res.report) setReport(res.report);
      }
    } catch (e) {
      console.error('Failed to send message:', e);
    } finally {
      setIsLoading(false);
      setIsTyping(false);
    }
  }, [recordId, isLoading]);

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
  }, []);

  return {
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
    reset,
    messagesEndRef,
  };
}
