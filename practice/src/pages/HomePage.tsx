import { useState } from 'react';
import { Play, Settings, User } from 'lucide-react';
import { StartPage } from './StartPage';
import { ScenePage } from './ScenePage';
import { ProfilePage } from './ProfilePage';

type TabType = 'start' | 'scene' | 'profile';

export function HomePage() {
  const [activeTab, setActiveTab] = useState<TabType>('start');

  const tabs = [
    { id: 'start' as TabType, label: '开始练习', icon: Play },
    { id: 'scene' as TabType, label: '场景设定', icon: Settings },
    { id: 'profile' as TabType, label: '我的', icon: User },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'start':
        return <StartPage />;
      case 'scene':
        return <ScenePage />;
      case 'profile':
        return <ProfilePage />;
      default:
        return <StartPage />;
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* 顶部标题栏 */}
      <header className="bg-white border-b border-gray-100 px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-500 rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-lg">D</span>
          </div>
          <div>
            <h1 className="font-semibold text-gray-800">AI对练</h1>
            <p className="text-xs text-gray-400">提升您的专业技能</p>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="flex-1 overflow-y-auto">
        {renderContent()}
      </main>

      {/* 底部导航栏 */}
      <nav className="bg-white border-t border-gray-100 px-2 py-2">
        <div className="flex items-center justify-around">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-colors ${
                  isActive
                    ? 'text-primary-500 bg-primary-50'
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon className={`w-6 h-6 ${isActive ? 'scale-110' : ''} transition-transform`} />
                <span className={`text-xs font-medium ${isActive ? 'font-semibold' : ''}`}>
                  {tab.label}
                </span>
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}