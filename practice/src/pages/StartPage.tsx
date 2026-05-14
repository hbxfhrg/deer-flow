import { RefreshCw, Target, Trophy, TrendingUp } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export function StartPage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [selectedScene, setSelectedScene] = useState<string | null>(null);

  const scenes = [
    {
      id: 'sales_car',
      title: '汽车销售',
      description: '模拟汽车销售场景，提升产品介绍能力',
      icon: Target,
      color: 'bg-blue-100 text-blue-600',
      stats: { completed: 12, score: 85 },
    },
    {
      id: 'sales_phone',
      title: '手机销售',
      description: '学习如何介绍手机产品特点',
      icon: Trophy,
      color: 'bg-green-100 text-green-600',
      stats: { completed: 8, score: 78 },
    },
    {
      id: 'insurance',
      title: '保险推销',
      description: '掌握保险产品的销售技巧',
      icon: TrendingUp,
      color: 'bg-purple-100 text-purple-600',
      stats: { completed: 5, score: 72 },
    },
  ];

  const handleStartPractice = async () => {
    setIsLoading(true);
    // 模拟加载延迟
    await new Promise(resolve => setTimeout(resolve, 1500));
    // 使用 React Router 导航
    navigate('/chat');
  };

  return (
    <div className="px-4 py-6">
      {/* 欢迎区域 */}
      <div className="bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl p-6 text-white mb-6">
        <h2 className="text-xl font-bold mb-2">欢迎回来！</h2>
        <p className="text-primary-100 text-sm">今天也要努力提升销售技巧哦</p>
        <div className="flex items-center gap-6 mt-4">
          <div>
            <p className="text-2xl font-bold">12</p>
            <p className="text-xs text-primary-100">已完成练习</p>
          </div>
          <div>
            <p className="text-2xl font-bold">85</p>
            <p className="text-xs text-primary-100">平均得分</p>
          </div>
          <div>
            <p className="text-2xl font-bold">5</p>
            <p className="text-xs text-primary-100">连续天数</p>
          </div>
        </div>
      </div>

      {/* 快速开始 */}
      <div className="mb-6">
        <button
          onClick={handleStartPractice}
          disabled={isLoading}
          className="w-full bg-primary-500 text-white rounded-xl py-4 font-semibold hover:bg-primary-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <RefreshCw className={`w-5 h-5 ${isLoading ? 'animate-spin' : ''}`} />
          {isLoading ? '正在进入...' : '快速开始对练'}
        </button>
      </div>

      {/* 场景选择 */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-800 mb-3">选择练习场景</h3>
        <div className="space-y-3">
          {scenes.map((scene) => {
            const Icon = scene.icon;
            return (
              <button
                key={scene.id}
                onClick={() => setSelectedScene(selectedScene === scene.id ? null : scene.id)}
                className={`w-full bg-white rounded-xl p-4 border-2 transition-all text-left ${
                  selectedScene === scene.id
                    ? 'border-primary-500 shadow-lg'
                    : 'border-gray-100 hover:border-gray-200'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${scene.color}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-800">{scene.title}</h4>
                    <p className="text-xs text-gray-500">{scene.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-gray-400">完成 {scene.stats.completed} 次</p>
                    <p className="text-sm font-semibold text-primary-500">{scene.stats.score}分</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 今日建议 */}
      <div className="bg-amber-50 rounded-xl p-4">
        <h3 className="font-semibold text-amber-800 mb-2">💡 今日建议</h3>
        <p className="text-sm text-amber-700">
          今天可以尝试汽车销售场景，重点练习客户异议处理技巧。记住要多使用具体数据来说服客户！
        </p>
      </div>
    </div>
  );
}