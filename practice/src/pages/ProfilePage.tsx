import { User, Trophy, BookOpen, HelpCircle, LogOut, ChevronRight, Star } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronDown } from 'lucide-react';
import { api } from '@/api';
import type { UserInfo } from '@/types';

interface PracticeRecord {
  id: number;
  courseName: string;
  sceneName: string;
  totalScore: number;
  startTime: string;
  practiceMode: string;
}

export function ProfilePage() {
  const navigate = useNavigate();
  const [activeSection, setActiveSection] = useState<string>('overview');
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedHelp, setExpandedHelp] = useState<string | null>(null);
  const [userStats, setUserStats] = useState([
    { label: '练习次数', value: '0', icon: BookOpen, color: 'bg-blue-100 text-blue-600' },
    { label: '平均得分', value: '0', icon: Trophy, color: 'bg-yellow-100 text-yellow-600' },
    { label: '连续天数', value: '0', icon: Star, color: 'bg-purple-100 text-purple-600' },
  ]);
  const [practiceHistory, setPracticeHistory] = useState<PracticeRecord[]>([]);

  useEffect(() => {
    loadUserInfo();
    loadUserStats();
    loadPracticeHistory();
  }, []);

  const loadUserInfo = async () => {
    try {
      const user = await api.auth.getCurrentUserInfo();
      setUserInfo(user);
    } catch (error) {
      console.error('Failed to load user info:', error);
    }
  };

  const loadUserStats = async () => {
    try {
      const user = api.auth.getCurrentUser();
      if (user) {
        const stats = await api.statistics.getUserStats(user.user_name || '');
        setUserStats([
          { label: '练习次数', value: stats.practice_count?.toString() || '0', icon: BookOpen, color: 'bg-blue-100 text-blue-600' },
          { label: '平均得分', value: stats.avg_score?.toString() || '0', icon: Trophy, color: 'bg-yellow-100 text-yellow-600' },
          { label: '连续天数', value: stats.continuous_days?.toString() || '0', icon: Star, color: 'bg-purple-100 text-purple-600' },
        ]);
      }
    } catch (error) {
      console.error('Failed to load user stats:', error);
    }
  };

  const loadPracticeHistory = async () => {
    try {
      const user = api.auth.getCurrentUser();
      if (user) {
        const records = await api.practiceRecords.list(undefined, user.user_name, undefined, undefined, 'completed', 1, 10);
        const history: PracticeRecord[] = records.map((item: any) => ({
          id: item.recordId,
          courseName: item.courseName || '未知课程',
          sceneName: item.sceneName || '未知场景',
          totalScore: item.totalScore || 0,
          startTime: item.startTime,
          practiceMode: item.practiceMode || 'text',
        }));
        setPracticeHistory(history);
      }
    } catch (error) {
      console.error('Failed to load practice history:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    if (window.confirm('确定要退出登录吗？')) {
      await api.auth.logout();
    }
  };

  const menuItems = [
    { id: 'overview', label: '学习概览', icon: BookOpen },
    { id: 'history', label: '练习记录', icon: Trophy },
    { id: 'help', label: '帮助与反馈', icon: HelpCircle },
  ];

  const renderContent = () => {
    switch (activeSection) {
      case 'overview':
        return (
          <div className="space-y-6">
            {/* 统计卡片 */}
            <div className="grid grid-cols-3 gap-3">
              {userStats.map((stat, index) => {
                const Icon = stat.icon;
                return (
                  <div key={index} className="bg-white rounded-xl p-3 text-center">
                    <div className={`w-10 h-10 mx-auto mb-2 rounded-full flex items-center justify-center ${stat.color}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <p className="text-xl font-bold text-gray-800">{stat.value}</p>
                    <p className="text-xs text-gray-500">{stat.label}</p>
                  </div>
                );
              })}
            </div>
          </div>
        );
      case 'history':
        return (
          <div className="space-y-3">
            {practiceHistory.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Trophy className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>暂无练习记录</p>
              </div>
            ) : (
              practiceHistory.map((record) => {
                const dateStr = record.startTime ? new Date(record.startTime).toLocaleDateString('zh-CN') : '';
                const isHighScore = record.totalScore >= 80;
                return (
                  <div key={record.id} className="bg-white rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-gray-800">{record.courseName}</span>
                      <span className="text-xs text-gray-400">{dateStr}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`text-2xl font-bold ${isHighScore ? 'text-success-500' : 'text-primary-500'}`}>
                          {record.totalScore}
                        </span>
                        <span className="text-sm text-gray-500">分</span>
                      </div>
                      <button 
                        onClick={() => navigate(`/result/${record.id}`)}
                        className="text-sm text-primary-500 hover:text-primary-600"
                      >查看详情</button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        );
      
      case 'help':
        const faqs = [
          {
            id: 'start',
            question: '如何开始练习？',
            answer: (
              <div className="text-sm text-gray-600 space-y-2">
                <p><strong>1. 登录系统</strong></p>
                <p>打开浏览器，访问系统首页，使用账号密码登录系统。</p>
                <p><strong>2. 进入练习入口</strong></p>
                <p>登录成功后，在首页或导航栏找到"开始练习"按钮，点击进入练习选择页面。</p>
                <p><strong>3. 开始对练</strong></p>
                <p>选择一个练习场景，点击"开始练习"按钮进入对练界面。阅读场景描述和问题后，在输入框中输入您的回复，点击发送或按回车键提交。等待AI回复后，继续进行下一轮对话。</p>
              </div>
            ),
          },
          {
            id: 'select',
            question: '如何选择场景？',
            answer: (
              <div className="text-sm text-gray-600 space-y-2">
                <p><strong>场景分类：</strong></p>
                <ul className="list-disc list-inside space-y-1">
                  <li><strong>基础场景</strong>：适合新手入门，难度较低（如：初次拜访客户、产品介绍）</li>
                  <li><strong>进阶场景</strong>：中等难度，需要一定技巧（如：处理客户异议、价格谈判）</li>
                  <li><strong>高级场景</strong>：高难度，综合能力考核（如：复杂需求挖掘、危机处理）</li>
                </ul>
                <p><strong>选择建议：</strong></p>
                <ul className="list-disc list-inside">
                  <li>新手用户：建议从基础场景开始</li>
                  <li>有经验用户：可根据自身薄弱环节选择相应场景进行专项练习</li>
                </ul>
              </div>
            ),
          },
          {
            id: 'report',
            question: '如何查看评估报告？',
            answer: (
              <div className="text-sm text-gray-600 space-y-2">
                <p><strong>1. 自动生成报告</strong></p>
                <p>完成一轮对练后，系统会自动生成评估报告。对练结束时会弹出"查看总结"弹窗，点击弹窗中的"查看报告"按钮即可查看详细报告。</p>
                <p><strong>2. 从历史记录查看</strong></p>
                <p>在个人中心页面，点击"练习记录"菜单，选择想要查看的历史练习记录，点击记录卡片即可查看该次练习的评估报告。</p>
                <p><strong>报告内容：</strong></p>
                <ul className="list-disc list-inside">
                  <li>得分图表：按考核维度展示整体得分</li>
                  <li>维度建议：每个考核维度都会给出针对性建议，包含优点和改进建议</li>
                  <li>重新生成：可点击"重新生成总结"按钮获取不同角度的评估结果</li>
                </ul>
              </div>
            ),
          },
        ];

        return (
          <div className="space-y-4">
            <div className="bg-white rounded-xl p-4">
              <h3 className="font-semibold text-gray-800 mb-3">常见问题</h3>
              <div className="space-y-2">
                {faqs.map((faq) => (
                  <div key={faq.id} className="border-b border-gray-50 last:border-0">
                    <button
                      onClick={() => setExpandedHelp(expandedHelp === faq.id ? null : faq.id)}
                      className="w-full flex items-center justify-between py-3 text-left"
                    >
                      <span className="text-sm text-gray-600">{faq.question}</span>
                      <ChevronDown
                        className={`w-4 h-4 text-gray-400 transition-transform ${
                          expandedHelp === faq.id ? 'rotate-180' : ''
                        }`}
                      />
                    </button>
                    {expandedHelp === faq.id && (
                      <div className="pb-3 pl-1 border-t border-gray-100 pt-3">
                        {faq.answer}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="px-4 py-6">
      {/* 用户信息 */}
      <div className="bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl p-6 text-white mb-6">
        {loading ? (
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center animate-pulse">
              <User className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-xl font-bold">加载中...</h2>
              <p className="text-primary-100 text-sm">请稍候</p>
            </div>
          </div>
        ) : userInfo ? (
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
              <User className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-xl font-bold">{userInfo.nick_name || userInfo.user_name}</h2>
              <p className="text-primary-100 text-sm">@{userInfo.user_name}</p>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
              <User className="w-8 h-8" />
            </div>
            <div>
              <h2 className="text-xl font-bold">未登录</h2>
              <p className="text-primary-100 text-sm">请重新登录</p>
            </div>
          </div>
        )}
      </div>

      {/* 菜单列表 */}
      <div className="bg-white rounded-xl p-2 mb-6">
        {menuItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveSection(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                isActive ? 'bg-primary-50 text-primary-600' : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="flex-1 text-left font-medium">{item.label}</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          );
        })}
        
        <div className="border-t border-gray-100 mt-2">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-danger-500 hover:bg-danger-50 transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span className="flex-1 text-left font-medium">退出登录</span>
          </button>
        </div>
      </div>

      {/* 内容区域 */}
      {renderContent()}
    </div>
  );
}