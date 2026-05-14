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