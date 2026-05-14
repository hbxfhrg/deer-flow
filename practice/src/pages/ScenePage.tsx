import { useState } from 'react';
import { Save, Plus, X, ChevronRight } from 'lucide-react';

export function ScenePage() {
  const [scenes, setScenes] = useState([
    {
      id: '1',
      name: '汽车销售基础',
      description: '适合新手的基础汽车销售场景',
      enabled: true,
      rounds: 5,
      difficulty: 'easy',
    },
    {
      id: '2',
      name: '高端车型销售',
      description: '豪华汽车销售场景，注重高端客户沟通',
      enabled: true,
      rounds: 5,
      difficulty: 'medium',
    },
    {
      id: '3',
      name: '新能源车销售',
      description: '新能源汽车销售，关注续航和充电问题',
      enabled: false,
      rounds: 5,
      difficulty: 'hard',
    },
  ]);

  const [selectedScene, setSelectedScene] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newScene, setNewScene] = useState({
    name: '',
    description: '',
    rounds: 5,
    difficulty: 'easy' as 'easy' | 'medium' | 'hard',
  });

  const difficultyOptions = [
    { value: 'easy', label: '简单', color: 'bg-green-100 text-green-600' },
    { value: 'medium', label: '中等', color: 'bg-yellow-100 text-yellow-600' },
    { value: 'hard', label: '困难', color: 'bg-red-100 text-red-600' },
  ];

  const toggleScene = (id: string) => {
    setScenes(prev =>
      prev.map(scene =>
        scene.id === id ? { ...scene, enabled: !scene.enabled } : scene
      )
    );
  };

  const saveNewScene = () => {
    if (!newScene.name.trim()) return;
    
    setScenes(prev => [
      ...prev,
      {
        id: Date.now().toString(),
        name: newScene.name,
        description: newScene.description,
        enabled: true,
        rounds: newScene.rounds,
        difficulty: newScene.difficulty,
      },
    ]);
    setShowAddModal(false);
    setNewScene({ name: '', description: '', rounds: 5, difficulty: 'easy' });
  };

  return (
    <div className="px-4 py-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">场景设定</h2>
          <p className="text-sm text-gray-500">管理您的练习场景</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl text-sm font-medium hover:bg-primary-600 transition-colors"
        >
          <Plus className="w-4 h-4" />
          添加场景
        </button>
      </div>

      {/* 场景列表 */}
      <div className="space-y-3">
        {scenes.map((scene) => (
          <div
            key={scene.id}
            onClick={() => setSelectedScene(selectedScene === scene.id ? null : scene.id)}
            className="bg-white rounded-xl p-4 border border-gray-100 hover:border-gray-200 transition-colors cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${scene.enabled ? 'bg-success-500' : 'bg-gray-300'}`} />
                <div>
                  <h3 className="font-medium text-gray-800">{scene.name}</h3>
                  <p className="text-xs text-gray-500">{scene.description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-1 rounded-full ${
                  difficultyOptions.find(d => d.value === scene.difficulty)?.color
                }`}>
                  {difficultyOptions.find(d => d.value === scene.difficulty)?.label}
                </span>
                <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${selectedScene === scene.id ? 'rotate-90' : ''}`} />
              </div>
            </div>

            {/* 展开详情 */}
            {selectedScene === scene.id && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-xs text-gray-400 mb-1">练习轮数</p>
                    <p className="font-semibold text-gray-800">{scene.rounds} 轮</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400 mb-1">难度等级</p>
                    <p className="font-semibold text-gray-800">
                      {difficultyOptions.find(d => d.value === scene.difficulty)?.label}
                    </p>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleScene(scene.id);
                  }}
                  className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${
                    scene.enabled
                      ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      : 'bg-primary-500 text-white hover:bg-primary-600'
                  }`}
                >
                  {scene.enabled ? '禁用场景' : '启用场景'}
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 添加场景弹窗 */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50">
          <div className="bg-white w-full max-w-lg rounded-t-2xl p-6 animate-slide-up">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-800">添加新场景</h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">场景名称</label>
                <input
                  type="text"
                  value={newScene.name}
                  onChange={(e) => setNewScene(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="请输入场景名称"
                  className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">场景描述</label>
                <textarea
                  value={newScene.description}
                  onChange={(e) => setNewScene(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="请输入场景描述"
                  rows={2}
                  className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500 resize-none"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">练习轮数</label>
                  <select
                    value={newScene.rounds}
                    onChange={(e) => setNewScene(prev => ({ ...prev, rounds: Number(e.target.value) }))}
                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500"
                  >
                    {[3, 5, 10].map(num => (
                      <option key={num} value={num}>{num} 轮</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">难度等级</label>
                  <div className="flex gap-2">
                    {difficultyOptions.map(diff => (
                      <button
                        key={diff.value}
                        onClick={() => setNewScene(prev => ({ ...prev, difficulty: diff.value as 'easy' | 'medium' | 'hard' }))}
                        className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                          newScene.difficulty === diff.value
                            ? `${diff.color} ring-2 ring-offset-1 ring-current`
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        }`}
                      >
                        {diff.label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 py-2 border border-gray-200 rounded-xl text-gray-600 font-medium hover:bg-gray-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={saveNewScene}
                disabled={!newScene.name.trim()}
                className="flex-1 py-2 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" />
                保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}