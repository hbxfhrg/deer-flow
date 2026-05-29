import axios, { AxiosInstance } from 'axios';
import type { Thread, Run, EvaluationResult, Message, UserInfo, LoginResponse, Scene, Course, PracticeStartResponse, PracticeTurnResponse, PracticeEndResponse } from '@/types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 添加请求拦截器，自动带上token
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('roleplay_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 添加响应拦截器，处理401未授权
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('roleplay_token');
      localStorage.removeItem('roleplay_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const api = {
  // 认证接口
  auth: {
    async login(username: string, password: string): Promise<LoginResponse> {
      const response = await axiosInstance.post('/roleplay/auth/login', {
        username,
        password,
      });
      if (response.data.success) {
        localStorage.setItem('roleplay_token', response.data.data.token);
        localStorage.setItem('roleplay_user', JSON.stringify(response.data.data));
      }
      return response.data;
    },
    
    async getUserInfo(userId: number): Promise<UserInfo> {
      const response = await axiosInstance.get(`/roleplay/auth/user/${userId}`);
      return response.data;
    },
    
    async logout(): Promise<void> {
      try {
        await axiosInstance.post('/roleplay/auth/logout');
      } catch (e) {
        // ignore error
      } finally {
        localStorage.removeItem('roleplay_token');
        localStorage.removeItem('roleplay_user');
        window.location.href = '/login';
      }
    },
    
    async getCurrentUserInfo(): Promise<UserInfo | null> {
      const user = this.getCurrentUser();
      if (!user) return null;
      try {
        const response = await axiosInstance.get(`/roleplay/auth/user/${user.user_id}`);
        return response.data.data;
      } catch {
        return user;
      }
    },
    
    getCurrentUser(): UserInfo | null {
      const userStr = localStorage.getItem('roleplay_user');
      return userStr ? JSON.parse(userStr) : null;
    },
    
    isLoggedIn(): boolean {
      return !!localStorage.getItem('roleplay_token');
    },
  },

  // 场景接口
  scenes: {
    async list(): Promise<Scene[]> {
      const response = await axiosInstance.get('/roleplay/scenes');
      return response.data.scenes;
    },
    
    async get(sceneId: string): Promise<Scene> {
      const response = await axiosInstance.get(`/roleplay/scenes/${sceneId}`);
      return response.data;
    },
    
    async create(data: Partial<Scene>): Promise<{ message: string; scene_id: string }> {
      const response = await axiosInstance.post('/roleplay/scenes', data);
      return response.data;
    },
    
    async update(sceneId: string, data: Partial<Scene>): Promise<{ message: string }> {
      const response = await axiosInstance.put(`/roleplay/scenes/${sceneId}`, data);
      return response.data;
    },
    
    async delete(sceneId: string): Promise<{ message: string }> {
      const response = await axiosInstance.delete(`/roleplay/scenes/${sceneId}`);
      return response.data;
    },
    
    async extractSummary(data: { knowledgeBase: string; promptTemplate?: string; modelName?: string }): Promise<{ 
      success: boolean; 
      summaryText?: string; 
      categories?: string[];
      message?: string;
    }> {
      const response = await axiosInstance.post('/roleplay/scenes/extract-summary', data);
      return response.data;
    },
  },

  // 课程接口
  courses: {
    async list(): Promise<Course[]> {
      const response = await axiosInstance.get('/roleplay/courses');
      return response.data.courses;
    },
    
    async get(courseId: number): Promise<Course> {
      const response = await axiosInstance.get(`/roleplay/courses/${courseId}`);
      return response.data;
    },
    
    async create(data: Partial<Course>): Promise<{ message: string; course_id: number }> {
      const response = await axiosInstance.post('/roleplay/courses', data);
      return response.data;
    },
    
    async update(courseId: number, data: Partial<Course>): Promise<{ message: string }> {
      const response = await axiosInstance.put(`/roleplay/courses/${courseId}`, data);
      return response.data;
    },
    
    async delete(courseId: number): Promise<{ message: string }> {
      const response = await axiosInstance.delete(`/roleplay/courses/${courseId}`);
      return response.data;
    },
  },

  // 评估接口
  evaluations: {
    async list(threadId?: string, userId?: string): Promise<any[]> {
      const params: Record<string, string> = {};
      if (threadId) params.thread_id = threadId;
      if (userId) params.user_id = userId;
      const response = await axiosInstance.get('/roleplay/evaluations', { params });
      return response.data.evaluations;
    },
    
    async get(evalId: string): Promise<any> {
      const response = await axiosInstance.get(`/roleplay/evaluations/${evalId}`);
      return response.data;
    },
    
    async create(data: any): Promise<any> {
      const response = await axiosInstance.post('/roleplay/evaluations', data);
      return response.data;
    },
  },

  // 练习记录接口
  practiceRecords: {
    async list(
      courseId?: number, 
      userName?: string,
      startTime?: string,
      endTime?: string,
      status?: string,
      page: number = 1,
      pageSize: number = 20
    ): Promise<any[]> {
      const params: Record<string, string> = {};
      if (courseId) params.course_id = courseId.toString();
      if (userName) params.user_name = userName;
      if (startTime) params.start_time = startTime;
      if (endTime) params.end_time = endTime;
      if (status) params.status = status;
      params.page = page.toString();
      params.page_size = pageSize.toString();
      const response = await axiosInstance.get('/roleplay/practice-records', { params });
      return response.data.records;
    },
    
    async create(data: any): Promise<any> {
      const response = await axiosInstance.post('/roleplay/practice-records', data);
      return response.data;
    },
    
    async complete(recordId: string, data: any): Promise<any> {
      const response = await axiosInstance.post(`/roleplay/practice-records/${recordId}/complete`, data);
      return response.data;
    },
  },

  // 统计接口
  statistics: {
    async getUserStats(userId: string): Promise<any> {
      const response = await axiosInstance.get(`/roleplay/statistics/user/${userId}`);
      return response.data;
    },
    
    async getSceneStats(sceneId?: string): Promise<any> {
      const params: Record<string, string> = {};
      if (sceneId) params.scene_id = sceneId;
      const response = await axiosInstance.get('/roleplay/statistics/scenes', { params });
      return response.data;
    },
    
    async getLeaderboard(limit: number = 10): Promise<any> {
      const response = await axiosInstance.get('/roleplay/statistics/leaderboard', {
        params: { limit },
      });
      return response.data;
    },
  },

  // 自由式对练接口
  practice: {
    async start(courseId: number): Promise<PracticeStartResponse> {
      const userStr = localStorage.getItem('roleplay_user');
      const user = userStr ? JSON.parse(userStr) : null;
      const response = await axiosInstance.post('/roleplay/practice/start', {
        courseId,
        userName: user?.user_name || 'anonymous',
      });
      return response.data;
    },
    
    async history(recordId: number): Promise<{ history: any[], totalRounds?: number }> {
      const response = await axiosInstance.get(`/roleplay/practice/${recordId}/history`);
      return response.data;
    },
    
    async turn(recordId: number, message: string): Promise<PracticeTurnResponse> {
      const response = await axiosInstance.post('/roleplay/practice/turn', {
        recordId,
        message,
      });
      return response.data;
    },
    
    async end(recordId: number): Promise<PracticeEndResponse> {
      const response = await axiosInstance.post('/roleplay/practice/end', {
        recordId,
      });
      return response.data;
    },
    
    async getSuggestions(recordId: number, dialogId: number): Promise<{
      suggestions: string[];
      polishedExpression: string;
    }> {
      const response = await axiosInstance.get(`/roleplay/practice/${recordId}/suggestions/${dialogId}`);
      return response.data;
    },
    
    async getReport(recordId: number): Promise<{
      success: boolean;
      report?: any;
      message?: string;
      status?: string;
    }> {
      const response = await axiosInstance.get(`/roleplay/practice/${recordId}/report`);
      return response.data;
    },
    
    async getInspiration(recordId: number): Promise<{
      recordId: number;
      currentRound: number;
      currentCategory: string;
      inspiration: Array<{ category: string; content: string }>;
    }> {
      const response = await axiosInstance.get(`/roleplay/practice/${recordId}/inspiration`);
      return response.data;
    },
    
    async regenerateReport(recordId: number): Promise<{
      success: boolean;
      report?: any;
    }> {
      const response = await axiosInstance.post(`/roleplay/practice/${recordId}/report/regenerate`);
      return response.data;
    },
  },

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