import { Trophy, ThumbsUp, ThumbsDown, Star } from 'lucide-react';
import type { Evaluation } from '@/types';

interface EvaluationCardProps {
  evaluation: Evaluation;
  status: 'pending' | 'completed' | 'not_found';
}

export function EvaluationCard({ evaluation, status }: EvaluationCardProps) {
  if (status === 'pending') {
    return (
      <div className="bg-white rounded-2xl shadow-lg p-4 evaluation-card">
        <div className="flex items-center justify-center gap-2 py-6">
          <div className="w-6 h-6 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-500 text-sm">评估中...</span>
        </div>
      </div>
    );
  }

  if (status === 'not_found' || !evaluation) {
    return null;
  }

  const score = evaluation.total_score ?? 0;
  const getScoreColor = () => {
    if (score >= 80) return 'text-success-500';
    if (score >= 60) return 'text-warning-500';
    return 'text-danger-500';
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-4 evaluation-card">
      {/* 标题 */}
      <div className="flex items-center gap-2 mb-4">
        <Trophy className="w-5 h-5 text-warning-500" />
        <h3 className="font-semibold text-gray-800">评估结果</h3>
        {evaluation.round && (
          <span className="ml-auto text-xs text-gray-400">第 {evaluation.round} 轮</span>
        )}
      </div>

      {/* 总分 */}
      <div className="flex items-center justify-center py-4">
        <div className="text-center">
          <div className={`text-4xl font-bold ${getScoreColor()}`}>{score}</div>
          <div className="flex items-center justify-center gap-1 mt-1">
            {[...Array(5)].map((_, i) => (
              <Star
                key={i}
                className={`w-4 h-4 ${i < Math.floor(score / 20) ? 'text-warning-500 fill-warning-500' : 'text-gray-300'}`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* 维度得分 */}
      {evaluation.dimension_scores && Object.keys(evaluation.dimension_scores).length > 0 && (
        <div className="mb-4">
          <div className="text-sm text-gray-500 mb-2">维度得分</div>
          <div className="space-y-2">
            {Object.entries(evaluation.dimension_scores).map(([key, value]) => (
              <div key={key} className="flex items-center gap-2">
                <span className="text-xs text-gray-600 w-20 truncate">{key}</span>
                <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div 
                    className={`h-full ${getScoreColor()}`}
                    style={{ width: `${value}%` }}
                  />
                </div>
                <span className={`text-xs font-medium w-8 text-right ${getScoreColor()}`}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 优点 */}
      {evaluation.strengths && evaluation.strengths.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-1 text-sm text-success-600 mb-2">
            <ThumbsUp className="w-4 h-4" />
            <span>优点</span>
          </div>
          <ul className="space-y-1">
            {evaluation.strengths.map((item, index) => (
              <li key={index} className="text-xs text-gray-600 pl-5 relative">
                <span className="absolute left-0 top-1 w-1.5 h-1.5 bg-success-500 rounded-full" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 改进建议 */}
      {evaluation.improvements && evaluation.improvements.length > 0 && (
        <div>
          <div className="flex items-center gap-1 text-sm text-warning-600 mb-2">
            <ThumbsDown className="w-4 h-4" />
            <span>改进建议</span>
          </div>
          <ul className="space-y-1">
            {evaluation.improvements.map((item, index) => (
              <li key={index} className="text-xs text-gray-600 pl-5 relative">
                <span className="absolute left-0 top-1 w-1.5 h-1.5 bg-warning-500 rounded-full" />
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 总结 */}
      {evaluation.summary && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="text-xs text-gray-500 mb-1">总结</div>
          <p className="text-sm text-gray-700">{evaluation.summary}</p>
        </div>
      )}
    </div>
  );
}