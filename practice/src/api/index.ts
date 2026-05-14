import axios, { AxiosInstance } from 'axios';
import type { Thread, Run, EvaluationResult, Message } from '@/types';

const API_BASE_URL = '/api';

const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // 线程管理
  threads: {
    async create(metadata?: Record<string, any>): Promise<Thread> {
      const response = await axiosInstance.post('/threads', { metadata });
      return response.data;
    },
    
    async get(threadId: string): Promise<Thread> {
      const response = await axiosInstance.get(`/threads/${threadId}`);
      return response.data;
    },
    
    async list(): Promise<Thread[]> {
      const response = await axiosInstance.get('/threads');
      return response.data;
    },
    
    async delete(threadId: string): Promise<void> {
      await axiosInstance.delete(`/threads/${threadId}`);
    },
  },
  
  // 运行管理
  runs: {
    async create(threadId: string, messages: Message[]): Promise<Run> {
      console.log('API: Creating run for thread:', threadId, 'with messages:', messages);
      const response = await axiosInstance.post(`/threads/${threadId}/runs`, {
        input: { messages },
        config: {
          thinking_enabled: false,
          configurable: {
            agent_name: 'roleplay-agent',
          },
        },
      });
      console.log('API: Run created:', response.data);
      return response.data;
    },
    
    async get(threadId: string, runId: string): Promise<Run> {
      const response = await axiosInstance.get(`/threads/${threadId}/runs/${runId}`);
      return response.data;
    },
    
    async delete(threadId: string, runId: string): Promise<void> {
      await axiosInstance.delete(`/threads/${threadId}/runs/${runId}`);
    },
  },
  
  // 消息管理
  messages: {
    async list(threadId: string): Promise<Message[]> {
      const response = await axiosInstance.get(`/threads/${threadId}/messages`);
      return response.data;
    },
  },
  
  // 评估结果
  evaluation: {
    async get(threadId: string, runId: string): Promise<EvaluationResult> {
      const response = await axiosInstance.get(`/threads/${threadId}/runs/${runId}/evaluation`);
      return response.data;
    },
  },
  
  // 流式响应
  stream: {
    create(threadId: string, runId: string): EventSource {
      return new EventSource(`${API_BASE_URL}/threads/${threadId}/runs/${runId}/stream`);
    },
  },
};

export default api;