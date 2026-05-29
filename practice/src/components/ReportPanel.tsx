import { Trophy, Star, ThumbsUp, ThumbsDown, TrendingUp, RefreshCw } from 'lucide-react';
import type { EvaluationReport } from '@/types';

interface ReportPanelProps {
  report: EvaluationReport;
  onRegenerate?: () => void;
  isRegenerating?: boolean;
}

function getScoreColor(score: number): string {
  if (score >= 80) return 'text-green-500';
  if (score >= 60) return 'text-yellow-500';
  return 'text-red-500';
}

function getScoreBg(score: number): string {
  if (score >= 80) return 'bg-green-500';
  if (score >= 60) return 'bg-yellow-500';
  return 'bg-red-500';
}

export function ReportPanel({ report, onRegenerate, isRegenerating }: ReportPanelProps) {
  const totalScore = report.total_score ?? 0;
  const dimensionScores = report.dimension_scores || {};
  const dimensionFeedbacks = report.dimension_feedbacks || {};
  const strengths = report.strengths || [];
  const improvements = report.improvements || [];
  const summary = report.summary || '';

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 animate-fadeIn">
      {/* 标题 */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Trophy className="w-6 h-6 text-yellow-500" />
          <h2 className="text-xl font-bold text-gray-800">对练报告</h2>
        </div>
        {onRegenerate && (
          <button
            onClick={onRegenerate}
            disabled={isRegenerating}
            className={`p-2 rounded-lg transition-colors ${
              isRegenerating
                ? 'text-gray-400 bg-gray-100 cursor-not-allowed'
                : 'text-primary-600 bg-primary-50 hover:bg-primary-100'
            }`}
            title={isRegenerating ? '正在生成中...' : '重新生成总结'}
          >
            <RefreshCw className={`w-4 h-4 ${isRegenerating ? 'animate-spin' : ''}`} />
          </button>
        )}
      </div>

      {/* 总分 */}
      <div className="flex flex-col items-center py-6 mb-6 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl">
        <div className={`text-5xl font-bold ${getScoreColor(totalScore)}`}>
          {totalScore}
        </div>
        <div className="text-sm text-gray-400 mt-1">综合评分</div>
        <div className="flex items-center gap-1 mt-2">
          {[...Array(5)].map((_, i) => (
            <Star
              key={i}
              className={`w-5 h-5 ${i < Math.floor(totalScore / 20) ? 'text-yellow-500 fill-yellow-500' : 'text-gray-200'}`}
            />
          ))}
        </div>
      </div>

      {/* 维度得分与反馈 */}
      {Object.keys(dimensionScores).length > 0 && (
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-blue-500" />
            <h3 className="font-semibold text-gray-700">维度评估</h3>
          </div>
          <div className="space-y-4">
            {Object.entries(dimensionScores).map(([key, value]) => (
              <div key={key} className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-700">{key}</span>
                  <span className={`text-lg font-bold ${getScoreColor(value)}`}>
                    {value}分
                  </span>
                </div>
                <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-3">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${getScoreBg(value)}`}
                    style={{ width: `${value}%` }}
                  />
                </div>
                {/* 维度详细反馈 */}
                {dimensionFeedbacks[key] && (
                  <p className="text-sm text-gray-600 leading-relaxed bg-white px-3 py-2 rounded-lg">
                    {dimensionFeedbacks[key]}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 优点 */}
      {strengths.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-1 text-sm text-green-600 font-medium mb-2">
            <ThumbsUp className="w-4 h-4" />
            <span>表现亮点</span>
          </div>
          <ul className="space-y-2">
            {strengths.map((item, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full mt-1.5 flex-shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 改进建议 */}
      {improvements.length > 0 && (
        <div className="mb-4">
          <div className="flex items-center gap-1 text-sm text-amber-600 font-medium mb-2">
            <ThumbsDown className="w-4 h-4" />
            <span>待改进</span>
          </div>
          <ul className="space-y-2">
            {improvements.map((item, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-gray-600">
                <span className="w-1.5 h-1.5 bg-amber-500 rounded-full mt-1.5 flex-shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 整体评价 */}
      {summary && (
        <div className="mt-6 pt-4 border-t border-gray-100">
          <h3 className="font-semibold text-gray-700 mb-2">整体评价</h3>
          <p className="text-sm text-gray-600 leading-relaxed">{summary}</p>
        </div>
      )}
    </div>
  );
}
