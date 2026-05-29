import { useState } from 'react';
import { Lightbulb, X, Sparkles, Loader2 } from 'lucide-react';
import api from '@/api';

interface InspirationPanelProps {
  recordId: number | null;
  knowledgeBase?: string;
  summaryText?: string;
  currentCategory?: string;
}

export function InspirationPanel({ recordId, knowledgeBase, summaryText, currentCategory: propCategory }: InspirationPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [inspirations, setInspirations] = useState<Array<{ category: string; content: string }>>([]);
  const [currentCategory, setCurrentCategory] = useState<string>('');
  
  // 解析摘要信息，提取分类和要点（作为备选）
  const parseSummary = () => {
    if (!summaryText) return [];
    return summaryText.split('\n')
      .map(line => line.trim())
      .filter(line => line && line.includes(':'))
      .map(line => {
        const [category, ...rest] = line.split(':');
        return {
          category: category.trim(),
          content: rest.join(':').trim()
        };
      })
      .filter(item => item.category && item.content);
  };
  
  // 调用后端API生成灵感
  const fetchInspiration = async () => {
    if (!recordId) return;
    
    setIsLoading(true);
    try {
      const result = await api.practice.getInspiration(recordId);
      // 更新当前维度
      if (result.currentCategory) {
        setCurrentCategory(result.currentCategory);
      }
      if (result.inspiration && result.inspiration.length > 0) {
        setInspirations(result.inspiration);
      } else {
        // 如果API返回空，使用备选方案
        const summaries = parseSummary();
        if (summaries.length > 0) {
          setInspirations(summaries);
        } else if (knowledgeBase) {
          setInspirations([{ category: '知识点提示', content: knowledgeBase.substring(0, 150) + (knowledgeBase.length > 150 ? '...' : '') }]);
        }
      }
    } catch (error) {
      console.error('获取灵感失败:', error);
      // 如果调用失败，使用备选方案
      const summaries = parseSummary();
      if (summaries.length > 0) {
        setInspirations(summaries.slice(0, 3).map(s => ({ ...s, content: s.content.substring(0, 150) + (s.content.length > 150 ? '...' : '') })));
      } else if (knowledgeBase) {
        setInspirations([{ category: '知识点提示', content: knowledgeBase.substring(0, 150) + (knowledgeBase.length > 150 ? '...' : '') }]);
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  // 打开面板时触发灵感获取
  const handleOpen = () => {
    setIsOpen(true);
    setInspirations([]);
    setCurrentCategory(propCategory || '');
    fetchInspiration();
  };
  
  // 获取备选灵感内容（无recordId时使用）
  const getFallbackInspirations = () => {
    const summaries = parseSummary();
    if (summaries.length > 0) {
      return summaries.slice(0, 3).map(s => ({ 
        category: s.category.substring(0, 20), 
        content: s.content.substring(0, 150) + (s.content.length > 150 ? '...' : '') 
      }));
    }
    if (knowledgeBase) {
      return [{ category: '知识点提示', content: knowledgeBase.substring(0, 150) + (knowledgeBase.length > 150 ? '...' : '') }];
    }
    return [];
  };
  
  // 判断是否可以显示灵感按钮
  const canShowInspiration = () => {
    if (recordId) return true;
    return getFallbackInspirations().length > 0;
  };
  
  if (!canShowInspiration()) {
    return null;
  }
  
  const displayInspirations = isLoading ? [] : (inspirations.length > 0 ? inspirations : getFallbackInspirations());
  
  return (
    <>
      {/* 灵感按钮 */}
      <button
        onClick={handleOpen}
        className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-amber-100 to-orange-100 hover:from-amber-200 hover:to-orange-200 rounded-full transition-all duration-200 shadow-md hover:shadow-lg"
        title="获取对话灵感"
      >
        <Lightbulb className="w-6 h-6 text-amber-600" />
      </button>
      
      {/* 灵感面板 */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[80vh] overflow-hidden animate-in fade-in zoom-in duration-200">
            {/* 头部 */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-800">对话灵感</h3>
                  {currentCategory && (
                    <span className="inline-flex items-center gap-1 mt-1 px-2 py-0.5 bg-amber-100 text-amber-700 text-xs rounded-full">
                      <Lightbulb className="w-3 h-3" />
                      当前维度：{currentCategory}
                    </span>
                  )}
                </div>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* 内容 */}
            <div className="px-6 py-4 overflow-y-auto max-h-[60vh]">
              {isLoading ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 text-primary-500 animate-spin mb-3" />
                  <p className="text-sm text-gray-400">正在为您生成灵感...</p>
                </div>
              ) : displayInspirations.length > 0 ? (
                <div className="space-y-4">
                  {displayInspirations.map((item, index) => (
                    <div
                      key={index}
                      className="bg-gradient-to-r from-amber-50 to-orange-50 rounded-xl p-4 border border-amber-100"
                    >
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 bg-amber-100 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5">
                          <Lightbulb className="w-4 h-4 text-amber-600" />
                        </div>
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-amber-700 mb-2">
                            {item.category}
                          </h4>
                          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
                            {item.content}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-12">
                  <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                    <Lightbulb className="w-8 h-8 text-gray-300" />
                  </div>
                  <p className="text-gray-400">暂无可用的灵感提示</p>
                </div>
              )}
              
              {/* 温馨提示 */}
              {!isLoading && displayInspirations.length > 0 && (
                <div className="mt-6 p-4 bg-amber-50 rounded-xl border border-amber-100">
                  <p className="text-sm text-amber-700">
                    💡 <span className="font-medium">小贴士：</span>
                    这些知识点可以帮助您更好地回应客户，试着用自己的语言表达出来，效果会更好哦！
                  </p>
                </div>
              )}
            </div>
            
            {/* 底部 */}
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
              <button
                onClick={() => setIsOpen(false)}
                className="w-full py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-medium hover:from-amber-600 hover:to-orange-600 transition-colors"
              >
                我知道了
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
