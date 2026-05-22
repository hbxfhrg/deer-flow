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
  practiceMode?: string; // 练习模式：剧本式/自由式
  knowledgeBase?: string; // 知识库内容
  summaryText?: string; // 摘要信息（格式：分类:要点，每行一个）
  examCategories?: string; // 考核范围（逗号分隔）
  scoringRules?: string; // 评分规则
  modelName?: string; // 大模型名称
  promptTemplate?: string; // 摘要提取自定义提示词模板
  createBy?: string; // 创建者用户ID
}

// 练习课程类型（与 pract_course 表对齐）
export interface Course {
  courseId: number;
  course_name: string;
  courseType: number; // 1: 练习，2: 考试
  sceneId?: number | null;
  sceneName?: string | null; // 关联的场景名称（后端返回）
  sceneDescription?: string | null; // 关联的场景描述（后端返回）
  simulatedRoleId?: number | null; // 关联的模拟角色 ID
  practiceMode: string; // text: 文本，voice: 语音，call: 模拟电话
  difficulty?: number | null;
  totalScore?: number;
  passingScore?: number;
  timeLimit?: number | null; // 单次练习时长限制（分钟）
  maxAttempts?: number;
  startTime?: string | null;
  endTime?: string | null;
  status: number; // 0: 未发布，1: 已发布，2: 已结束
  create_by?: string;
  createdAt?: string;
}

// ── 自由式对练类型 ──

export interface EvaluationReport {
  total_score: number;
  dimension_scores: Record<string, number>;
  strengths: string[];
  improvements: string[];
  summary: string;
}

export interface PracticeStartResponse {
  recordId: number;
  courseName: string;
  sceneName: string;
  sceneDescription: string;
  totalRounds: number;
  customerMessage: string;
  round: number;
}

export interface PracticeTurnResponse {
  recordId: number;
  round: number;
  evaluation: {
    roundScore: number;
    dimensionScores: Record<string, number>;
    feedback: string;
  };
  customerMessage: string;
  isComplete: boolean;
  report?: EvaluationReport;
}

export interface PracticeEndResponse {
  recordId: number;
  totalRounds: number;
  report: EvaluationReport;
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