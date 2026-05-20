export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt?: string;
}

export interface Evaluation {
  round?: number;
  total_score?: number;
  dimension_scores?: Record<string, number>;
  strengths?: string[];
  improvements?: string[];
  summary?: string;
}

export interface EvaluationResult {
  thread_id: string;
  run_id: string;
  status: 'pending' | 'completed' | 'not_found';
  evaluation?: {
    evaluation?: Evaluation;
  };
}

export interface Thread {
  thread_id: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface Run {
  run_id: string;
  thread_id: string;
  status: string;
  created_at: string;
}

export interface StreamEvent {
  event: string;
  data: {
    messages?: Message[];
    status?: string;
  };
}

// 场景设置类型（与数据库字段对齐）
export interface Scene {
  scene_id: string;
  scene_name: string;
  scene_description: string;
  enabled: boolean;
  rounds: number;
  difficulty: '简单' | '中等' | '困难';
  practiceMode?: string; // 练习模式：剧本式/自由式
  timePerRound?: number; // 每轮时间限制（秒）
  totalTimeLimit?: number; // 总时长限制（秒）
  knowledgeBase?: string; // 知识库内容
  summaryText?: string; // 摘要信息（格式：分类:要点，每行一个）
  examCategories?: string; // 考核范围（逗号分隔）
  scoringRules?: string; // 评分规则
  modelName?: string; // 大模型名称
  promptTemplate?: string; // 摘要提取自定义提示词模板
}

// 认证相关类型
export interface UserInfo {
  user_id: number;
  user_name: string;
  nick_name?: string;
  email?: string;
  phonenumber?: string;
  token?: string;
  expire_time?: string;
}

export interface LoginResponse {
  success: boolean;
  message: string;
  data?: UserInfo;
}