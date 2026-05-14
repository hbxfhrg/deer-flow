import { User, Trophy, BookOpen, Settings, HelpCircle, LogOut, ChevronRight, Star } from 'lucide-react';
import { useState } from 'react';

export function ProfilePage() {
  const [activeSection, setActiveSection] = useState<string>('overview');

  const userStats = [
    { label: '练习次数', value: '45', icon: BookOpen, color: 'bg-blue-100 text-blue-600' },
    { label: '平均得分', value: '82', icon: Trophy, color: 'bg-yellow-100 text-yellow-600' },
    { label: '连续天数', value: '15', icon: Star, color: 'bg-purple-100 text-purple-600' },
  ];

  const menuItems = [
    { id: 'overview', label: '学习概览', icon: BookOpen },
    { id: 'history', label: '练习记录', icon: Trophy },
    { id: 'achievements', label: '成就徽章', icon: Star },
    { id: 'settings', label: '设置', icon: Settings },
    { id: 'help', label: '帮助与反馈', icon: HelpCircle },
  ];

  const achievements = [
    { id: '1', name: '初学者', description: '完成第一次练习', unlocked: true },
    { id: '2', name: '坚持不懈', description: '连续练习7天', unlocked: true },
    { id: '3', name: '销售之星', description: '获得10次满分', unlocked: false },
    { id: '4', name: '全能选手', description: '完成所有场景', unlocked: false },
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

            {/* 学习进度 */}
            <div className="bg-white rounded-xl p-4">
              <h3 className="font-semibold text-gray-800 mb-3">学习进度</h3>
              <div className="space-y-3">
                {['汽车销售', '手机销售', '保险推销'].map((item, index) => (
                  <div key={index}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600">{item}</span>
                      <span className="text-primary-500 font-medium">{Math.floor(Math.random() * 60 + 40)}%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary-500 rounded-full"
                        style={{ width: `${Math.floor(Math.random() * 60 + 40)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 最近练习 */}
            <div className="bg-white rounded-xl p-4">
              <h3 className="font-semibold text-gray-800 mb-3">最近练习</h3>
              <div className="space-y-3">
                {[
                  { scene: '汽车销售', date: '今天', score: 85 },
                  { scene: '手机销售', date: '昨天', score: 78 },
                  { scene: '汽车销售', date: '2天前', score: 92 },
                ].map((item, index) => (
                  <div key={index} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{item.scene}</p>
                      <p className="text-xs text-gray-400">{item.date}</p>
                    </div>
                    <div className="text-right">
                      <p className={`text-lg font-bold ${item.score >= 80 ? 'text-success-500' : item.score >= 60 ? 'text-yellow-500' : 'text-danger-500'}`}>
                        {item.score}
                      </p>
                      <p className="text-xs text-gray-400">分</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      
      case 'achievements':
        return (
          <div className="space-y-3">
            {achievements.map((achievement) => (
              <div key={achievement.id} className={`bg-white rounded-xl p-4 flex items-center gap-3 ${!achievement.unlocked ? 'opacity-50' : ''}`}>
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${achievement.unlocked ? 'bg-primary-100 text-primary-500' : 'bg-gray-100 text-gray-400'}`}>
                  <Star className={`w-6 h-6 ${achievement.unlocked ? 'fill-current' : ''}`} />
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-800">{achievement.name}</h4>
                  <p className="text-xs text-gray-500">{achievement.description}</p>
                </div>
                <div className={`text-sm font-medium ${achievement.unlocked ? 'text-success-500' : 'text-gray-400'}`}>
                  {achievement.unlocked ? '已解锁' : '未解锁'}
                </div>
              </div>
            ))}
          </div>
        );
      
      case 'history':
        return (
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((item) => (
              <div key={item} className="bg-white rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-gray-800">汽车销售练习 #{item}</span>
                  <span className="text-xs text-gray-400">2026-05-{14 - item}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`text-2xl font-bold ${item % 3 === 0 ? 'text-success-500' : 'text-primary-500'}`}>
                      {75 + item * 3}
                    </span>
                    <span className="text-sm text-gray-500">分</span>
                  </div>
                  <button className="text-sm text-primary-500 hover:text-primary-600">查看详情</button>
                </div>
              </div>
            ))}
          </div>
        );
      
      case 'settings':
        return (
          <div className="space-y-2">
            {[
              { label: '语言设置', value: '中文' },
              { label: '音效设置', value: '开启' },
              { label: '震动反馈', value: '开启' },
              { label: '数据同步', value: '开启' },
            ].map((item, index) => (
              <div key={index} className="bg-white rounded-xl p-4 flex items-center justify-between">
                <span className="text-gray-800">{item.label}</span>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">{item.value}</span>
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
              </div>
            ))}
          </div>
        );
      
      case 'help':
        return (
          <div className="space-y-4">
            <div className="bg-white rounded-xl p-4">
              <h3 className="font-semibold text-gray-800 mb-2">常见问题</h3>
              <div className="space-y-2">
                {['如何开始练习？', '如何选择场景？', '如何查看评估报告？'].map((q, i) => (
                  <div key={i} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                    <span className="text-sm text-gray-600">{q}</span>
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-white rounded-xl p-4">
              <h3 className="font-semibold text-gray-800 mb-2">联系我们</h3>
              <p className="text-sm text-gray-500 mb-3">如有任何问题或建议，请通过以下方式联系我们：</p>
              <div className="space-y-2">
                <p className="text-sm text-gray-600">📧 邮箱：support@deerflow.com</p>
                <p className="text-sm text-gray-600">📱 客服热线：400-123-4567</p>
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
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center">
            <User className="w-8 h-8" />
          </div>
          <div>
            <h2 className="text-xl font-bold">销售精英</h2>
            <p className="text-primary-100 text-sm">Lv.8 资深学员</p>
          </div>
        </div>
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
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-danger-500 hover:bg-danger-50 transition-colors">
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