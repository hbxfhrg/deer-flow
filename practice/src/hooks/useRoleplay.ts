import { useState, useCallback, useEffect, useRef } from 'react';
import api from '@/api';
import type { Message, Evaluation, EvaluationResult } from '@/types';

export function useRoleplay() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null);
  const [evaluationStatus, setEvaluationStatus] = useState<'pending' | 'completed' | 'not_found' | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<number | null>(null);

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // 轮询评估结果
  const startEvaluationPolling = useCallback((threadId: string, runId: string) => {
    const poll = async () => {
      try {
        const result: EvaluationResult = await api.evaluation.get(threadId, runId);
        setEvaluationStatus(result.status);

        if (result.status === 'completed' && result.evaluation?.evaluation) {
          setEvaluation(result.evaluation.evaluation);
          if (pollingRef.current) {
            clearTimeout(pollingRef.current);
            pollingRef.current = null;
          }
        } else if (result.status === 'pending') {
          pollingRef.current = window.setTimeout(poll, 500);
        }
      } catch (error) {
        console.error('Failed to poll evaluation:', error);
        if (pollingRef.current) {
          clearTimeout(pollingRef.current);
          pollingRef.current = null;
        }
      }
    };

    poll();
  }, []);

  // 初始化新对话并发送第一条消息
  const initConversation = useCallback(async () => {
    setIsLoading(true);
    try {
      const thread = await api.threads.create({
        roleplay_mode: true,
        scenario: 'sales_training',
      });
      setCurrentThreadId(thread.thread_id);
      setEvaluation(null);
      setEvaluationStatus(null);
      
      // 发送第一条消息触发 AI 回复
      const starterMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: '你好，请开始今天的销售对练，请扮演客户',
        createdAt: new Date().toISOString(),
      };
      
      setMessages([starterMessage]);
      setIsTyping(true);
      
      // 创建运行并获取 AI 回复
      const run = await api.runs.create(thread.thread_id, [starterMessage]);
      setCurrentRunId(run.run_id);
      
      // 启动流式响应
      const eventSource = api.stream.create(thread.thread_id, run.run_id);
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const messagesData = data.data?.messages;
          
          if (messagesData && Array.isArray(messagesData)) {
            const aiMessages = messagesData.filter((m: Message) => m.role === 'assistant');
            if (aiMessages.length > 0) {
              const latestAiMessage = aiMessages[aiMessages.length - 1];
              setMessages(prev => {
                const existingAiIndex = prev.findIndex(m => m.role === 'assistant' && m.id === latestAiMessage.id);
                if (existingAiIndex >= 0) {
                  const updated = [...prev];
                  updated[existingAiIndex] = latestAiMessage;
                  return updated;
                }
                return [...prev, latestAiMessage];
              });
            }
          }
        } catch (e) {
          console.error('Failed to parse stream event:', e);
        }
      };
      
      eventSource.onerror = () => {
        eventSource.close();
        setIsTyping(false);
        setIsLoading(false);
      };
      
      eventSource.addEventListener('end', () => {
        eventSource.close();
        setIsTyping(false);
        setIsLoading(false);
        
        // 开始轮询评估结果
        startEvaluationPolling(thread.thread_id, run.run_id);
      });
      
    } catch (error) {
      console.error('Failed to create thread:', error);
      setIsLoading(false);
    }
  }, [startEvaluationPolling]);

  // 发送消息并启动流式响应
  const sendMessage = useCallback(async (content: string) => {
    console.log('sendMessage called:', { content, currentThreadId, isLoading });
    
    if (!currentThreadId || isLoading || content.trim() === '') {
      console.warn('sendMessage rejected:', { hasThreadId: !!currentThreadId, isLoading, hasContent: content.trim() !== '' });
      return;
    }

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: content.trim(),
      createdAt: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setIsTyping(true);
    setEvaluation(null);
    setEvaluationStatus(null);

    try {
      console.log('Creating run with thread:', currentThreadId);
      const run = await api.runs.create(currentThreadId, [userMessage]);
      console.log('Run created:', run);
      setCurrentRunId(run.run_id);

      // 启动流式响应
      console.log('Creating EventSource for:', currentThreadId, run.run_id);
      const eventSource = api.stream.create(currentThreadId, run.run_id);

      eventSource.onmessage = (event) => {
        console.log('EventSource message received:', event.data);
        try {
          const data = JSON.parse(event.data);
          const messagesData = data.data?.messages;
          
          if (messagesData && Array.isArray(messagesData)) {
            const aiMessages = messagesData.filter((m: Message) => m.role === 'assistant');
            if (aiMessages.length > 0) {
              const latestAiMessage = aiMessages[aiMessages.length - 1];
              setMessages(prev => {
                const existingAiIndex = prev.findIndex(m => m.role === 'assistant' && m.id === latestAiMessage.id);
                if (existingAiIndex >= 0) {
                  const updated = [...prev];
                  updated[existingAiIndex] = latestAiMessage;
                  return updated;
                }
                return [...prev, latestAiMessage];
              });
            }
          }
        } catch (e) {
          console.error('Failed to parse stream event:', e);
        }
      };

      eventSource.onerror = (err) => {
        console.error('EventSource error:', err);
        // 不要立即关闭，等待 end 事件
        // eventSource.close();
        // setIsTyping(false);
        // setIsLoading(false);
      };

      eventSource.addEventListener('end', () => {
        console.log('EventSource ended');
        eventSource.close();
        setIsTyping(false);
        setIsLoading(false);
        
        // 开始轮询评估结果
        startEvaluationPolling(currentThreadId, run.run_id);
      });

    } catch (error) {
      console.error('Failed to send message:', error);
      setIsTyping(false);
      setIsLoading(false);
    }
  }, [currentThreadId, isLoading, startEvaluationPolling]);

  // 清理轮询
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearTimeout(pollingRef.current);
      }
    };
  }, []);

  // 自动滚动
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  return {
    messages,
    currentThreadId,
    currentRunId,
    isLoading,
    isTyping,
    evaluation,
    evaluationStatus,
    initConversation,
    sendMessage,
    messagesEndRef,
  };
}