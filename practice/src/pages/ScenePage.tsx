import { useState, useEffect } from 'react';
import { Save, Plus, X, ChevronRight, Sparkles, Check, Settings } from 'lucide-react';
import api from '../api';

interface Scene {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  rounds: number;
  difficulty: '简单' | '中等' | '困难';
  timePerRound?: number; // 每轮时间限制（秒）
  totalTimeLimit?: number; // 总时长限制（秒）
  knowledgeBase?: string; // 知识库内容
  practiceMode?: string; // 练习模式：剧本式/自由式
  summaryText?: string; // 摘要信息（格式：分类:要点，每行一个）
  examCategories?: string; // 考核范围（逗号分隔）
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
      difficulty: '简单',
      practiceMode: '自由式',
      knowledgeBase: '汽车销售基础知识包括产品知识、客户需求分析、销售技巧等方面。产品知识涵盖车型特点、配置参数、竞品对比等。客户需求分析需要了解客户的预算、用途、偏好等。销售技巧包括沟通技巧、谈判技巧、跟进技巧等。',
      summaryText: '产品知识:了解客户需求是销售的第一步\n客户需求分析:产品优势需要与客户痛点相结合\n销售技巧:建立信任关系至关重要',
      examCategories: '产品知识,客户需求分析,销售技巧',
      scoringRules: '产品知识准确性：30分\n沟通技巧：25分\n需求理解：25分\n销售策略：20分',
    },
    {
      id: '2',
      name: '高端车型销售',
      description: '豪华汽车销售场景，注重高端客户沟通',
      enabled: true,
      rounds: 5,
      difficulty: '中等',
      practiceMode: '剧本式',
    },
    {
      id: '3',
      name: '新能源车销售',
      description: '新能源汽车销售，关注续航和充电问题',
      enabled: false,
      rounds: 5,
      difficulty: '困难',
      practiceMode: '自由式',
    },
  ]);

  // 页面加载时从后端获取场景列表
  useEffect(() => {
    const loadScenes = async () => {
      try {
        const scenesData = await api.scenes.list();
        if (scenesData && scenesData.length > 0) {
          setScenes(scenesData);
        }
      } catch (error) {
        console.error('加载场景列表失败:', error);
        // 如果后端不可用，使用默认数据
      }
    };
    loadScenes();
  }, []);

  const [selectedScene, setSelectedScene] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [summaryPrompt, setSummaryPrompt] = useState(defaultPrompt);
  const [editingScene, setEditingScene] = useState<Scene | null>(null);
  // 示例文本
  const defaultKnowledgeBase = `汽车销售基础知识包括以下几个方面：

产品知识：
- 了解车型特点和配置参数
- 掌握竞品对比信息
- 熟悉车辆性能数据

客户需求分析：
- 了解客户的预算范围
- 分析客户的使用用途
- 识别客户的偏好需求

销售技巧：
- 有效的沟通技巧
- 专业的谈判技巧
- 及时的跟进技巧

售后服务：
- 提供优质的售后服务
- 建立长期客户关系
- 处理客户投诉和反馈`;

  const [newScene, setNewScene] = useState({
    scene_name: '',
    scene_description: '',
    rounds: 5,
    difficulty: '简单' as '简单' | '中等' | '困难',
    practiceMode: '自由式',
    timePerRound: 120, // 默认每轮2分钟
    totalTimeLimit: 600, // 默认总时长10分钟
    knowledgeBase: '', // 新增时清空，用户自行输入
    summaryText: '',
    examCategories: '',
    scoringRules: '',
  });

  const difficultyOptions = [
    { value: '简单', label: '简单', color: 'bg-green-100 text-green-600' },
    { value: '中等', label: '中等', color: 'bg-yellow-100 text-yellow-600' },
    { value: '困难', label: '困难', color: 'bg-red-100 text-red-600' },
  ];

  const practiceModeOptions = [
    { value: '剧本式', label: '剧本式' },
    { value: '自由式', label: '自由式' },
  ];

  const toggleScene = async (id: string) => {
    try {
      const scene = scenes.find(s => s.scene_id === id);
      if (!scene) return;
      
      await api.scenes.update(id, { enabled: !scene.enabled });
      // 重新加载场景列表
      const updatedScenes = await api.scenes.list();
      setScenes(updatedScenes);
    } catch (error) {
      console.error('更新场景状态失败:', error);
      alert('更新场景状态失败，请稍后重试');
    }
  };

  const deleteScene = async (id: string) => {
    if (confirm('确定要删除这个场景吗？')) {
      try {
        await api.scenes.delete(id);
        // 重新加载场景列表
        const updatedScenes = await api.scenes.list();
        setScenes(updatedScenes);
        if (selectedScene === id) {
          setSelectedScene(null);
        }
      } catch (error) {
        console.error('删除场景失败:', error);
        alert('删除场景失败，请稍后重试');
      }
    }
  };

  // 编辑场景
  const openEditModal = (scene: Scene) => {
    setEditingScene(scene);
    setShowEditModal(true);
  };

  // 编辑场景时提取摘要
  const extractSummaryForEdit = async () => {
    if (!editingScene || !editingScene.knowledgeBase.trim()) return;
    
    setIsExtracting(true);
    
    try {
      const response = await api.scenes.extractSummary({
        knowledgeBase: editingScene.knowledgeBase,
        promptTemplate: summaryPrompt,
      });
      
      if (response.success && response.summaryText) {
        setEditingScene(prev => prev ? {
          ...prev,
          summaryText: response.summaryText,
          examCategories: '', // 清空之前选择的考核分类
        } : null);
      } else {
        alert('提取摘要失败：' + (response.message || '未知错误'));
      }
    } catch (error) {
      console.error('提取摘要失败:', error);
      alert('提取摘要失败，请稍后重试');
    } finally {
      setIsExtracting(false);
    }
  };

  // 保存编辑后的场景
  const saveEditedScene = async () => {
    if (!editingScene || !editingScene.scene_name.trim()) {
      alert('请输入场景名称');
      return;
    }
    
    try {
      await api.scenes.update(editingScene.scene_id, {
        scene_name: editingScene.scene_name,
        scene_description: editingScene.scene_description,
        rounds: editingScene.rounds,
        difficulty: editingScene.difficulty,
        practiceMode: editingScene.practiceMode,
        timePerRound: editingScene.timePerRound,
        totalTimeLimit: editingScene.totalTimeLimit,
        knowledgeBase: editingScene.knowledgeBase,
        summaryText: editingScene.summaryText?.trim() || undefined,
        examCategories: editingScene.examCategories?.trim() || undefined,
        scoringRules: editingScene.scoringRules?.trim() || undefined,
      });
      
      // 重新加载场景列表
      const updatedScenes = await api.scenes.list();
      setScenes(updatedScenes);
      
      alert('场景修改成功！');
      setShowEditModal(false);
      setEditingScene(null);
    } catch (error) {
      console.error('修改场景失败:', error);
      alert('修改场景失败，请稍后重试');
    }
  };

  // 解析 summaryText 为分类和要点
  const parseSummaryText = (text: string) => {
    const lines = text.split('\n').filter(line => line.trim());
    const categories: string[] = [];
    const keyPoints: string[] = [];
    
    lines.forEach(line => {
      const parts = line.split(':');
      if (parts.length >= 2) {
        categories.push(parts[0].trim());
        keyPoints.push(parts.slice(1).join(':').trim());
      }
    });
    
    return { categories, keyPoints };
  };

  // 调用后端API提取摘要
  const extractSummary = async () => {
    if (!newScene.knowledgeBase.trim()) return;
    
    setIsExtracting(true);
    
    try {
      const response = await api.scenes.extractSummary({
        knowledgeBase: newScene.knowledgeBase,
        promptTemplate: summaryPrompt,
      });
      
      if (response.success && response.summaryText) {
        setNewScene(prev => ({
          ...prev,
          summaryText: response.summaryText,
          examCategories: '', // 清空之前选择的考核分类
        }));
      } else {
        alert('提取摘要失败：' + (response.message || '未知错误'));
      }
    } catch (error) {
      console.error('提取摘要失败:', error);
      alert('提取摘要失败，请稍后重试');
    } finally {
      setIsExtracting(false);
    }
  };

  // 添加考核分类
  const addExamCategory = (category: string) => {
    if (!newScene.examCategories.includes(category)) {
      setNewScene(prev => ({
        ...prev,
        examCategories: prev.examCategories 
          ? prev.examCategories + ',' + category 
          : category,
      }));
    }
  };

  // 移除考核分类
  const removeExamCategory = (category: string) => {
    setNewScene(prev => ({
      ...prev,
      examCategories: prev.examCategories
        .split(',')
        .filter(cat => cat.trim() !== category)
        .join(','),
    }));
  };

  // 全选/取消全选考核分类
  const toggleAllExamCategories = () => {
    const { categories } = parseSummaryText(newScene.summaryText);
    if (newScene.examCategories.split(',').filter(c => c.trim()).length === categories.length) {
      setNewScene(prev => ({ ...prev, examCategories: '' }));
    } else {
      setNewScene(prev => ({ ...prev, examCategories: categories.join(',') }));
    }
  };

  const saveNewScene = async () => {
    // 表单验证
    const errors: string[] = [];
    
    if (!newScene.scene_name.trim()) {
      errors.push('请输入场景名称');
    }
    
    if (newScene.practiceMode === '自由式' && !newScene.knowledgeBase.trim()) {
      errors.push('自由式练习模式需要填写知识库内容');
    }
    
    if (newScene.practiceMode === '自由式' && !newScene.scoringRules.trim()) {
      errors.push('自由式练习模式需要填写评分规则');
    }
    
    if (errors.length > 0) {
      alert(errors.join('\n'));
      return;
    }
    
    try {
      const response = await api.scenes.create({
        scene_name: newScene.scene_name,
        scene_description: newScene.scene_description,
        enabled: true,
        rounds: newScene.rounds,
        difficulty: newScene.difficulty,
        practiceMode: newScene.practiceMode,
        timePerRound: newScene.timePerRound,
        totalTimeLimit: newScene.totalTimeLimit,
        knowledgeBase: newScene.knowledgeBase,
        summaryText: newScene.summaryText.trim() || undefined,
        examCategories: newScene.examCategories.trim() || undefined,
        scoringRules: newScene.scoringRules.trim() || undefined,
      });
      
      // 重新加载场景列表
      const updatedScenes = await api.scenes.list();
      setScenes(updatedScenes);
      
      alert('场景保存成功！');
      setShowAddModal(false);
      setNewScene({
        name: '',
        description: '',
        rounds: 5,
        difficulty: '简单',
        practiceMode: '自由式',
        timePerRound: 120,
        totalTimeLimit: 600,
        knowledgeBase: '', // 新增时清空
        summaryText: '',
        examCategories: '',
        scoringRules: '',
      });
    } catch (error) {
      console.error('保存场景失败:', error);
      alert('保存场景失败，请稍后重试');
    }
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
            key={scene.scene_id}
            onClick={() => setSelectedScene(selectedScene === scene.scene_id ? null : scene.scene_id)}
            className="bg-white rounded-xl p-4 border border-gray-100 hover:border-gray-200 transition-colors cursor-pointer"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${scene.enabled ? 'bg-success-500' : 'bg-gray-300'}`} />
                <div>
                  <h3 className="font-medium text-gray-800">{scene.scene_name}</h3>
                  <p className="text-xs text-gray-500">{scene.scene_description}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-xs px-2 py-1 rounded-full ${
                  difficultyOptions.find(d => d.value === scene.difficulty)?.color
                }`}>
                  {difficultyOptions.find(d => d.value === scene.difficulty)?.label}
                </span>
                <ChevronRight className={`w-5 h-5 text-gray-400 transition-transform ${selectedScene === scene.scene_id ? 'rotate-90' : ''}`} />
              </div>
            </div>

            {/* 展开详情 */}
            {selectedScene === scene.scene_id && (
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
                
                {/* 显示练习模式 */}
                {scene.practiceMode && (
                  <div className="mb-4">
                    <p className="text-xs text-gray-400 mb-1">🎮 练习模式</p>
                    <span className={`inline-block text-xs px-3 py-1 rounded-full ${
                      scene.practiceMode === '自由式' 
                        ? 'bg-amber-100 text-amber-600' 
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {scene.practiceMode}
                    </span>
                  </div>
                )}
                
                {/* 显示时间设置 */}
                {(scene.timePerRound || scene.totalTimeLimit) && (
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    {scene.timePerRound && (
                      <div>
                        <p className="text-xs text-gray-400 mb-1">⏱️ 每轮时间</p>
                        <p className="font-semibold text-gray-800">{scene.timePerRound} 秒</p>
                      </div>
                    )}
                    {scene.totalTimeLimit && (
                      <div>
                        <p className="text-xs text-gray-400 mb-1">⏰ 总时长</p>
                        <p className="font-semibold text-gray-800">{scene.totalTimeLimit} 秒</p>
                      </div>
                    )}
                  </div>
                )}
                
                {/* 显示考核范围 */}
                {scene.examCategories && scene.examCategories.trim() && (
                  <div className="mb-4 p-3 bg-purple-50 rounded-xl">
                    <p className="text-xs text-purple-600 font-medium mb-2">📝 考核范围</p>
                    <div className="flex flex-wrap gap-1">
                      {scene.examCategories.split(',').map((cat, idx) => (
                        <span key={idx} className="text-xs px-2 py-0.5 bg-purple-100 text-purple-600 rounded-full">
                          {cat.trim()}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* 显示知识库摘要 */}
                {scene.summaryText && scene.summaryText.trim() && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-xl">
                    <p className="text-xs text-blue-600 font-medium mb-2">📚 知识要点</p>
                    <ul className="text-xs text-gray-600 space-y-1">
                      {scene.summaryText.split('\n').slice(0, 3).map((line, idx) => {
                        const parts = line.split(':');
                        return (
                          <li key={idx} className="flex items-start gap-1">
                            <span className="text-blue-500 font-medium">{parts[0].trim()}:</span>
                            {parts.slice(1).join(':').trim()}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
                
                <div className="flex gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      openEditModal(scene);
                    }}
                    className="flex-1 py-2 rounded-lg text-sm font-medium bg-blue-500 text-white hover:bg-blue-600 transition-colors"
                  >
                    修改场景
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleScene(scene.scene_id);
                    }}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                      scene.enabled
                        ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        : 'bg-primary-500 text-white hover:bg-primary-600'
                    }`}
                  >
                    {scene.enabled ? '禁用场景' : '启用场景'}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteScene(scene.scene_id);
                    }}
                    className="flex-1 py-2 rounded-lg text-sm font-medium bg-red-500 text-white hover:bg-red-600 transition-colors"
                  >
                    删除场景
                  </button>
                </div>
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
                <label className="block text-sm font-medium text-gray-700 mb-1">场景名称<span className="text-red-500 ml-1">*</span></label>
                <input
                  type="text"
                  value={newScene.scene_name}
                  onChange={(e) => setNewScene(prev => ({ ...prev, scene_name: e.target.value }))}
                  placeholder="请输入场景名称"
                  className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">场景描述</label>
                <textarea
                  value={newScene.scene_description}
                  onChange={(e) => setNewScene(prev => ({ ...prev, scene_description: e.target.value }))}
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
                        onClick={() => setNewScene(prev => ({ ...prev, difficulty: diff.value as '简单' | '中等' | '困难' }))}
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
              
              {/* 练习模式选择 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">🎮 练习模式</label>
                <div className="flex gap-2">
                  {practiceModeOptions.map(mode => (
                    <button
                      key={mode.value}
                      onClick={() => setNewScene(prev => ({ ...prev, practiceMode: mode.value }))}
                      className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                        newScene.practiceMode === mode.value
                          ? 'bg-amber-500 text-white ring-2 ring-offset-1 ring-amber-500'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {mode.label}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* 时间设置 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">⏱️ 每轮时间限制（秒）</label>
                  <input
                    type="number"
                    min="30"
                    max="600"
                    step="30"
                    value={newScene.timePerRound}
                    onChange={(e) => setNewScene(prev => ({ ...prev, timePerRound: Number(e.target.value) }))}
                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500"
                  />
                  <p className="text-xs text-gray-400 mt-1">默认 120 秒（2分钟）</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">⏰ 总时长限制（秒）</label>
                  <input
                    type="number"
                    min="60"
                    max="1800"
                    step="60"
                    value={newScene.totalTimeLimit}
                    onChange={(e) => setNewScene(prev => ({ ...prev, totalTimeLimit: Number(e.target.value) }))}
                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500"
                  />
                  <p className="text-xs text-gray-400 mt-1">默认 600 秒（10分钟）</p>
                </div>
              </div>
              
              {/* 知识库文本输入 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">标准文本（用于生成知识库）{newScene.practiceMode === '自由式' && <span className="text-red-500 ml-1">*</span>}</label>
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
                  <p className="text-xs text-blue-600 font-medium mb-2">✨ 提取结果（知识要点）</p>
                  {newScene.summaryText.trim() ? (
                    <div className="space-y-2">
                      <div>
                        <p className="text-xs text-gray-500 mb-1">分类与要点</p>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {newScene.summaryText.split('\n').map((line, idx) => {
                            const parts = line.split(':');
                            return (
                              <li key={idx} className="flex items-start gap-1">
                                <span className="text-blue-500 font-medium">{parts[0].trim()}:</span>
                                {parts.slice(1).join(':').trim()}
                              </li>
                            );
                          })}
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
                    {parseSummaryText(newScene.summaryText).categories.length > 0 && (
                      <button
                        onClick={toggleAllExamCategories}
                        className="text-xs text-purple-500 hover:text-purple-600"
                      >
                        {newScene.examCategories.split(',').filter(c => c.trim()).length === parseSummaryText(newScene.summaryText).categories.length ? '取消全选' : '全选'}
                      </button>
                    )}
                  </div>
                  {parseSummaryText(newScene.summaryText).categories.length > 0 ? (
                    <>
                      <div className="flex flex-wrap gap-2">
                        {parseSummaryText(newScene.summaryText).categories.map((cat, idx) => (
                          <button
                            key={idx}
                            onClick={() => newScene.examCategories.includes(cat) ? removeExamCategory(cat) : addExamCategory(cat)}
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
                      {newScene.examCategories.split(',').filter(c => c.trim()).length > 0 && (
                        <p className="text-xs text-purple-500 mt-2">
                          已选择 {newScene.examCategories.split(',').filter(c => c.trim()).length} 个考核项
                        </p>
                      )}
                    </>
                  ) : (
                    <p className="text-xs text-gray-400">请先提取摘要以获取可选择的分类</p>
                  )}
                </div>
                
                {/* 评分规则设定 */}
                <div className="p-4 bg-green-50 rounded-xl">
                  <p className="text-xs text-green-600 font-medium mb-2">📊 评分规则设定{newScene.practiceMode === '自由式' && <span className="text-red-500 ml-1">*</span>}</p>
                  <textarea
                    value={newScene.scoringRules}
                    onChange={(e) => setNewScene(prev => ({ ...prev, scoringRules: e.target.value }))}
                    placeholder="请输入评分规则，例如：\n产品知识准确性：30分\n沟通技巧：25分\n需求理解：25分\n销售策略：20分"
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
                disabled={!newScene.scene_name.trim()}
                className="flex-1 py-2 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" />
                保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑场景弹窗 */}
      {showEditModal && editingScene && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
          <div className="bg-white w-full max-w-2xl rounded-2xl p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-800">修改场景</h3>
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingScene(null);
                }}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">场景名称<span className="text-red-500 ml-1">*</span></label>
                <input
                  type="text"
                  value={editingScene.scene_name}
                  onChange={(e) => setEditingScene(prev => prev ? { ...prev, scene_name: e.target.value } : null)}
                  placeholder="请输入场景名称"
                  className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">场景描述</label>
                <textarea
                  value={editingScene.scene_description}
                  onChange={(e) => setEditingScene(prev => prev ? { ...prev, scene_description: e.target.value } : null)}
                  placeholder="请输入场景描述"
                  rows={2}
                  className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500 resize-none"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">练习轮数</label>
                  <select
                    value={editingScene.rounds}
                    onChange={(e) => setEditingScene(prev => prev ? { ...prev, rounds: Number(e.target.value) } : null)}
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
                        onClick={() => setEditingScene(prev => prev ? { ...prev, difficulty: diff.value as '简单' | '中等' | '困难' } : null)}
                        className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                          editingScene.difficulty === diff.value
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
              
              {/* 练习模式选择 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">🎮 练习模式</label>
                <div className="flex gap-2">
                  {practiceModeOptions.map(mode => (
                    <button
                      key={mode.value}
                      onClick={() => setEditingScene(prev => prev ? { ...prev, practiceMode: mode.value } : null)}
                      className={`flex-1 py-2 rounded-xl text-sm font-medium transition-colors ${
                        editingScene.practiceMode === mode.value
                          ? mode.value === '自由式'
                            ? 'bg-amber-500 text-white'
                            : 'bg-gray-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {mode.label}
                    </button>
                  ))}
                </div>
              </div>
              
              {/* 时间设置 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">⏱️ 每轮时间限制（秒）</label>
                  <input
                    type="number"
                    min="30"
                    max="600"
                    step="30"
                    value={editingScene.timePerRound}
                    onChange={(e) => setEditingScene(prev => prev ? { ...prev, timePerRound: Number(e.target.value) } : null)}
                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500"
                  />
                  <p className="text-xs text-gray-400 mt-1">默认 120 秒（2分钟）</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">⏰ 总时长限制（秒）</label>
                  <input
                    type="number"
                    min="60"
                    max="1800"
                    step="60"
                    value={editingScene.totalTimeLimit}
                    onChange={(e) => setEditingScene(prev => prev ? { ...prev, totalTimeLimit: Number(e.target.value) } : null)}
                    className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500"
                  />
                  <p className="text-xs text-gray-400 mt-1">默认 600 秒（10分钟）</p>
                </div>
              </div>
              
              {/* 知识库文本输入 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">标准文本（用于生成知识库）{editingScene.practiceMode === '自由式' && <span className="text-red-500 ml-1">*</span>}</label>
                <textarea
                  value={editingScene.knowledgeBase}
                  onChange={(e) => setEditingScene(prev => prev ? { ...prev, knowledgeBase: e.target.value } : null)}
                  placeholder="请输入相关产品知识、销售话术等标准文本，系统将自动提取摘要..."
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500 resize-none"
                />
                
                {/* 提取摘要按钮和设置按钮 */}
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={extractSummaryForEdit}
                    disabled={!editingScene.knowledgeBase.trim() || isExtracting}
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
                  <p className="text-xs text-blue-600 font-medium mb-2">✨ 提取结果（知识要点）</p>
                  {editingScene.summaryText?.trim() ? (
                    <div className="space-y-2">
                      <div>
                        <p className="text-xs text-gray-500 mb-1">分类与要点</p>
                        <ul className="text-xs text-gray-600 space-y-1">
                          {editingScene.summaryText.split('\n').map((line, idx) => {
                            const parts = line.split(':');
                            return (
                              <li key={idx} className="flex items-start gap-1">
                                <span className="text-blue-500 font-medium">{parts[0].trim()}:</span>
                                {parts.slice(1).join(':').trim()}
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400">请先输入标准文本并点击"提取摘要"按钮</p>
                  )}
                </div>
                
                {/* 考核范围选择 */}
                <div className="p-4 bg-purple-50 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs text-purple-600 font-medium">🎯 考核范围（可多选）</p>
                    <button
                      onClick={() => {
                        const { categories } = parseSummaryText(editingScene.summaryText || '');
                        if (editingScene.examCategories?.split(',').filter(c => c.trim()).length === categories.length) {
                          setEditingScene(prev => prev ? { ...prev, examCategories: '' } : null);
                        } else {
                          setEditingScene(prev => prev ? { ...prev, examCategories: categories.join(',') } : null);
                        }
                      }}
                      className="text-xs text-purple-600 hover:text-purple-700"
                    >
                      {editingScene.examCategories?.split(',').filter(c => c.trim()).length === parseSummaryText(editingScene.summaryText || '').categories.length ? '取消全选' : '全选'}
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {parseSummaryText(editingScene.summaryText || '').categories.map((category, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          const currentCategories = editingScene.examCategories?.split(',').filter(c => c.trim()) || [];
                          if (currentCategories.includes(category)) {
                            setEditingScene(prev => prev ? {
                              ...prev,
                              examCategories: currentCategories.filter(c => c !== category).join(',')
                            } : null);
                          } else {
                            setEditingScene(prev => prev ? {
                              ...prev,
                              examCategories: [...currentCategories, category].join(',')
                            } : null);
                          }
                        }}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                          (editingScene.examCategories?.split(',').filter(c => c.trim()) || []).includes(category)
                            ? 'bg-purple-500 text-white'
                            : 'bg-white text-purple-600 border border-purple-200 hover:border-purple-300'
                        }`}
                      >
                        {category}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
              
              {/* 评分规则设定 */}
              <div className="p-4 bg-green-50 rounded-xl">
                <p className="text-xs text-green-600 font-medium mb-2">📊 评分规则设定{editingScene.practiceMode === '自由式' && <span className="text-red-500 ml-1">*</span>}</p>
                <textarea
                  value={editingScene.scoringRules}
                  onChange={(e) => setEditingScene(prev => prev ? { ...prev, scoringRules: e.target.value } : null)}
                  placeholder="请输入评分规则，例如：\n产品知识准确性：30分\n沟通技巧：25分\n需求理解：25分\n销售策略：20分"
                  rows={4}
                  className="w-full px-3 py-2 border border-green-200 rounded-lg text-xs focus:outline-none focus:border-green-500 resize-none"
                />
              </div>
            </div>
            
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowEditModal(false);
                  setEditingScene(null);
                }}
                className="flex-1 py-2 border border-gray-200 rounded-xl text-gray-600 font-medium hover:bg-gray-50 transition-colors"
              >
                取消
              </button>
              <button
                onClick={saveEditedScene}
                disabled={!editingScene.scene_name.trim()}
                className="flex-1 py-2 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <Save className="w-4 h-4" />
                保存修改
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