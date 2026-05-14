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
        console.log('Evaluation poll result:', result);
        setEvaluationStatus(result.status);

        // 检查多种可能的评估数据格式
        let evaluationData: Evaluation | null = null;
        if (result.evaluation?.evaluation) {
          evaluationData = result.evaluation.evaluation;
        } else if (result.evaluation && typeof result.evaluation === 'object' && !('evaluation' in result.evaluation)) {
          evaluationData = result.evaluation as Evaluation;
        }

        if (result.status === 'completed' && evaluationData) {
          setEvaluation(evaluationData);
          if (pollingRef.current) {
            clearTimeout(pollingRef.current);
            pollingRef.current = null;
          }
        } else if (result.status === 'pending') {
          pollingRef.current = window.setTimeout(poll, 1000);
        } else if (result.status === 'completed') {
          // 评估已完成但没有数据，停止轮询
          if (pollingRef.current) {
            clearTimeout(pollingRef.current);
            pollingRef.current = null;
          }
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

  // 解析消息数据
  const parseMessagesFromEvent = (eventData: string): Message[] => {
    try {
      const data = JSON.parse(eventData);
      console.log('Parsed event data:', data);
      
      // 尝试多种可能的数据格式
      let messagesData: any[] = [];
      
      // 格式1: 直接在根级别
      if (Array.isArray(data)) {
        messagesData = data;
      }
      // 格式2: data.messages
      else if (data.messages && Array.isArray(data.messages)) {
        messagesData = data.messages;
      }
      // 格式3: data.data.messages
      else if (data.data && data.data.messages && Array.isArray(data.data.messages)) {
        messagesData = data.data.messages;
      }
      // 格式4: 检查 values 字段（来自日志）
      else if (data.values && Array.isArray(data.values)) {
        messagesData = data.values;
      }
      // 格式5: data.data.values
      else if (data.data && data.data.values && Array.isArray(data.data.values)) {
        messagesData = data.data.values;
      }
      // 格式6: 检查 state 字段（LangGraph 格式）
      else if (data.state && data.state.messages && Array.isArray(data.state.messages)) {
        messagesData = data.state.messages;
      }
      
      console.log('Extracted messages:', messagesData);
      
      // 转换为 Message 类型
      return messagesData.map((msg: any) => {
        // 根据 type 字段判断角色
        let role: 'user' | 'assistant' = 'assistant';
        if (msg.role) {
          role = msg.role === 'user' ? 'user' : 'assistant';
        } else if (msg.type) {
          // LangChain 格式：human 表示用户，ai 或 assistant 表示助手
          if (msg.type === 'human' || msg.type === 'user') {
            role = 'user';
          } else if (msg.type === 'ai' || msg.type === 'assistant') {
            role = 'assistant';
          }
        }
        
        // 提取内容，处理多种格式
        let content = '';
        if (typeof msg.content === 'string') {
          content = msg.content;
        } else if (msg.content && typeof msg.content === 'object') {
          // LangChain 格式：content 可能是对象
          if (msg.content.text) {
            content = msg.content.text;
          } else if (msg.content.content) {
            content = msg.content.content;
          }
        }
        
        return {
          id: msg.id || msg.uuid || `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          role,
          content,
          createdAt: msg.createdAt || msg.timestamp || new Date().toISOString(),
        };
      });
    } catch (e) {
      console.error('Failed to parse event data:', e);
      return [];
    }
  };

  // 处理 SSE 事件
  const handleSseEvent = useCallback((event: MessageEvent) => {
    console.log('SSE event received:', event.type, event.data);
    
    try {
      const allMessages = parseMessagesFromEvent(event.data);
      const aiMessages = allMessages.filter((m: Message) => m.role === 'assistant');
      
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
    } catch (e) {
      console.error('Failed to process SSE event:', e);
    }
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
      
      // 监听所有类型的事件
      eventSource.addEventListener('values', handleSseEvent);
      eventSource.addEventListener('messages', handleSseEvent);
      eventSource.addEventListener('message', handleSseEvent);
      
      eventSource.onerror = () => {
        console.error('EventSource error');
        eventSource.close();
        setIsTyping(false);
        setIsLoading(false);
      };
      
      eventSource.addEventListener('end', () => {
        console.log('EventSource ended');
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
  }, [startEvaluationPolling, handleSseEvent]);

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

      // 监听所有类型的事件
      eventSource.addEventListener('values', handleSseEvent);
      eventSource.addEventListener('messages', handleSseEvent);
      eventSource.addEventListener('message', handleSseEvent);

      eventSource.onerror = (err) => {
        console.error('EventSource error:', err);
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
  }, [currentThreadId, isLoading, startEvaluationPolling, handleSseEvent]);

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