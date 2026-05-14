import { useState } from 'react';
import { Save, Plus, X, ChevronRight, Sparkles, Check, Settings } from 'lucide-react';

interface Scene {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  rounds: number;
  difficulty: 'easy' | 'medium' | 'hard';
  knowledgeBase?: string; // 知识库内容
  summary?: {
    title: string;
    categories: string[];
    keyPoints: string[];
  };
  examCategories?: string[]; // 考核范围
  scoringRules?: string; // 评分规则
}

// 默认提示词
const defaultPrompt = `请对以下文本进行分析，提取关键信息：

1. 识别文本中的主要分类（如产品介绍、客户需求、销售策略等）
2. 提取每个分类下的关键要点
3. 生成一个简洁的标题

请以JSON格式输出，包含以下字段：
- title: 摘要标题
- categories: 分类标签数组
- keyPoints: 关键要点数组

文本内容：
{{TEXT}}`;

export function ScenePage() {
  const [scenes, setScenes] = useState<Scene[]>([
    {
      id: '1',
      name: '汽车销售基础',
      description: '适合新手的基础汽车销售场景',
      enabled: true,
      rounds: 5,
      difficulty: 'easy',
      knowledgeBase: '汽车销售基础知识包括产品知识、客户需求分析、销售技巧等方面。产品知识涵盖车型特点、配置参数、竞品对比等。客户需求分析需要了解客户的预算、用途、偏好等。销售技巧包括沟通技巧、谈判技巧、跟进技巧等。',
      summary: {
        title: '汽车销售基础知识',
        categories: ['产品知识', '客户需求分析', '销售技巧'],
        keyPoints: ['车型特点', '配置参数', '竞品对比', '客户预算', '客户用途', '沟通技巧', '谈判技巧'],
      },
      examCategories: ['产品知识', '销售技巧'],
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
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [summaryPrompt, setSummaryPrompt] = useState(defaultPrompt);
  const [newScene, setNewScene] = useState({
    name: '',
    description: '',
    rounds: 5,
    difficulty: 'easy' as 'easy' | 'medium' | 'hard',
    knowledgeBase: '',
    summary: {
      title: '',
      categories: [] as string[],
      keyPoints: [] as string[],
    },
    examCategories: [] as string[],
    scoringRules: '',
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

  // 模拟调用大模型提取摘要
  const extractSummary = async () => {
    if (!newScene.knowledgeBase.trim()) return;
    
    setIsExtracting(true);
    
    // 模拟API延迟
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // 模拟大模型返回的摘要结果
    const mockSummary = {
      title: '知识摘要',
      categories: ['产品介绍', '客户需求', '销售策略', '常见问题', '竞品分析'],
      keyPoints: [
        '了解客户需求是销售的第一步',
        '产品优势需要与客户痛点相结合',
        '建立信任关系至关重要',
        '处理客户异议需要耐心和技巧',
        '跟进客户可以提高成交率',
      ],
    };
    
    setNewScene(prev => ({
      ...prev,
      summary: mockSummary,
      examCategories: [], // 清空之前选择的考核分类
    }));
    
    setIsExtracting(false);
  };

  // 切换考核分类选择
  const toggleExamCategory = (category: string) => {
    setNewScene(prev => ({
      ...prev,
      examCategories: prev.examCategories.includes(category)
        ? prev.examCategories.filter(cat => cat !== category)
        : [...prev.examCategories, category],
    }));
  };

  // 全选/取消全选考核分类
  const toggleAllExamCategories = () => {
    if (newScene.examCategories.length === newScene.summary.categories.length) {
      setNewScene(prev => ({ ...prev, examCategories: [] }));
    } else {
      setNewScene(prev => ({ ...prev, examCategories: [...prev.summary.categories] }));
    }
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
        knowledgeBase: newScene.knowledgeBase,
        summary: newScene.summary.title ? newScene.summary : undefined,
        examCategories: newScene.examCategories.length > 0 ? newScene.examCategories : undefined,
        scoringRules: newScene.scoringRules.trim() ? newScene.scoringRules : undefined,
      },
    ]);
    setShowAddModal(false);
    setNewScene({
      name: '',
      description: '',
      rounds: 5,
      difficulty: 'easy',
      knowledgeBase: '',
      summary: { title: '', categories: [], keyPoints: [] },
      examCategories: [],
      scoringRules: '',
    });
  };

  const savePromptSettings = () => {
    setShowSettingsModal(false);
    // 可以在这里保存到 localStorage 或后端
    localStorage.setItem('summary_prompt', summaryPrompt);
  };

  const resetPrompt = () => {
    setSummaryPrompt(defaultPrompt);
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
                
                {/* 显示考核范围 */}
                {scene.examCategories && scene.examCategories.length > 0 && (
                  <div className="mb-4 p-3 bg-purple-50 rounded-xl">
                    <p className="text-xs text-purple-600 font-medium mb-2">📝 考核范围</p>
                    <div className="flex flex-wrap gap-1">
                      {scene.examCategories.map((cat, idx) => (
                        <span key={idx} className="text-xs px-2 py-0.5 bg-purple-100 text-purple-600 rounded-full">
                          {cat}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* 显示知识库摘要 */}
                {scene.summary && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-xl">
                    <p className="text-xs text-blue-600 font-medium mb-2">📚 知识摘要</p>
                    <p className="text-sm font-semibold text-gray-800 mb-2">{scene.summary.title}</p>
                    <div className="flex flex-wrap gap-1 mb-2">
                      {scene.summary.categories.map((cat, idx) => (
                        <span key={idx} className="text-xs px-2 py-0.5 bg-blue-100 text-blue-600 rounded-full">
                          {cat}
                        </span>
                      ))}
                    </div>
                    <ul className="text-xs text-gray-600 space-y-1">
                      {scene.summary.keyPoints.slice(0, 3).map((point, idx) => (
                        <li key={idx} className="flex items-start gap-1">
                          <span className="text-blue-500">•</span>
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
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
          <div className="bg-white w-full max-w-lg rounded-t-2xl p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
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
              
              {/* 知识库文本输入 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">标准文本（用于生成知识库）</label>
                <textarea
                  value={newScene.knowledgeBase}
                  onChange={(e) => setNewScene(prev => ({ ...prev, knowledgeBase: e.target.value }))}
                  placeholder="请输入相关产品知识、销售话术等标准文本，系统将自动提取摘要..."
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500 resize-none"
                />
                
                {/* 提取摘要按钮和设置按钮 */}
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={extractSummary}
                    disabled={!newScene.knowledgeBase.trim() || isExtracting}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg text-sm font-medium hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Sparkles className={`w-4 h-4 ${isExtracting ? 'animate-spin' : ''}`} />
                    {isExtracting ? '提取中...' : '提取摘要'}
                  </button>
                  <button
                    onClick={() => setShowSettingsModal(true)}
                    className="flex items-center justify-center gap-1 px-4 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                  >
                    <Settings className="w-4 h-4" />
                    设置
                  </button>
                </div>
              </div>
              
              {/* 提取结果展示 */}
              <div className="space-y-4">
                <div className="p-4 bg-blue-50 rounded-xl">
                  <p className="text-xs text-blue-600 font-medium mb-2">✨ 提取结果</p>
                  {newScene.summary.title ? (
                    <div className="space-y-2">
                      <div>
                        <p className="text-sm font-semibold text-gray-800">{newScene.summary.title}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">分类标签</p>
                        <div className="flex flex-wrap gap-1">
                          {newScene.summary.categories.map((cat, idx) => (
                            <span key={idx} className="text-xs px-2 py-0.5 bg-blue-100 text-blue-600 rounded-full">
                              {cat}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">关键要点</p>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {newScene.summary.keyPoints.map((point, idx) => (
                            <li key={idx} className="flex items-start gap-1">
                              <span className="text-blue-500">•</span>
                              {point}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400">请先输入标准文本并点击"提取摘要"按钮</p>
                  )}
                </div>
                
                {/* 考核范围选择 */}
                <div className="p-4 bg-purple-50 rounded-xl">
                  <div className="flex items-center justify-between mb-3">
                    <p className="text-xs text-purple-600 font-medium">📝 选择考核范围</p>
                    {newScene.summary.categories.length > 0 && (
                      <button
                        onClick={toggleAllExamCategories}
                        className="text-xs text-purple-500 hover:text-purple-600"
                      >
                        {newScene.examCategories.length === newScene.summary.categories.length ? '取消全选' : '全选'}
                      </button>
                    )}
                  </div>
                  {newScene.summary.categories.length > 0 ? (
                    <>
                      <div className="flex flex-wrap gap-2">
                        {newScene.summary.categories.map((cat, idx) => (
                          <button
                            key={idx}
                            onClick={() => toggleExamCategory(cat)}
                            className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                              newScene.examCategories.includes(cat)
                                ? 'bg-purple-500 text-white'
                                : 'bg-purple-100 text-purple-600 hover:bg-purple-200'
                            }`}
                          >
                            {newScene.examCategories.includes(cat) && (
                              <Check className="w-3 h-3" />
                            )}
                            {cat}
                          </button>
                        ))}
                      </div>
                      {newScene.examCategories.length > 0 && (
                        <p className="text-xs text-purple-500 mt-2">
                          已选择 {newScene.examCategories.length} 个考核项
                        </p>
                      )}
                    </>
                  ) : (
                    <p className="text-xs text-gray-400">请先提取摘要以获取可选择的分类</p>
                  )}
                </div>
                
                {/* 评分规则设定 */}
                <div className="p-4 bg-green-50 rounded-xl">
                  <p className="text-xs text-green-600 font-medium mb-2">📊 评分规则设定</p>
                  <textarea
                    value={newScene.scoringRules}
                    onChange={(e) => setNewScene(prev => ({ ...prev, scoringRules: e.target.value }))}
                    placeholder="请输入评分规则，例如：\n- 产品知识准确性：30分\n- 沟通技巧：25分\n- 需求理解：25分\n- 销售策略：20分"
                    rows={4}
                    className="w-full px-3 py-2 border border-green-200 rounded-lg text-xs focus:outline-none focus:border-green-500 resize-none"
                  />
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

      {/* 摘要提取设置弹窗 */}
      {showSettingsModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
          <div className="bg-white w-full max-w-md rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-800">摘要提取设置</h3>
              <button
                onClick={() => setShowSettingsModal(false)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  提取提示词
                  <span className="text-gray-400 font-normal ml-1">(使用 {'{'}{'{'}TEXT{'}'}{'}'} 作为文本占位符)</span>
                </label>
                <textarea
                  value={summaryPrompt}
                  onChange={(e) => setSummaryPrompt(e.target.value)}
                  placeholder="请输入提示词..."
                  rows={8}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500 resize-none font-mono text-sm"
                />
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={resetPrompt}
                  className="flex-1 py-2 border border-gray-200 rounded-xl text-gray-600 font-medium hover:bg-gray-50 transition-colors"
                >
                  恢复默认
                </button>
                <button
                  onClick={savePromptSettings}
                  className="flex-1 py-2 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors"
                >
                  保存设置
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}