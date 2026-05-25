import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, Star, ChevronRight, Filter, Calendar, CheckCircle, Loader } from 'lucide-react';
import { api } from '@/api';

interface PracticeHistoryRecord {
  id: number;
  courseId: number;
  courseName: string;
  sceneName: string;
  startTime: string;
  endTime?: string;
  totalScore?: number;
  summary?: string;
  status: 'completed' | 'in_progress';
}

type StatusType = 'all' | 'completed' | 'in_progress';

export function HistoryPage() {
  const navigate = useNavigate();
  const [records, setRecords] = useState<PracticeHistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<StatusType>('all');
  const [dateRange, setDateRange] = useState<{ start: string; end: string }>(getDefaultDateRange());

  function getDefaultDateRange() {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 3);
    return {
      start: start.toISOString().split('T')[0],
      end: end.toISOString().split('T')[0],
    };
  }

  useEffect(() => {
    const startTime = `${dateRange.start}T00:00:00Z`;
    const endTime = `${dateRange.end}T23:59:59Z`;
    fetchHistory(undefined, startTime, endTime);
  }, []);

  const fetchHistory = async (status?: string, startTime?: string, endTime?: string) => {
    setLoading(true);
    try {
      const user = api.auth.getCurrentUser();
      const data = await api.practiceRecords.list(
        undefined,
        user?.user_name,
        startTime,
        endTime,
        status === 'all' ? undefined : status
      );
      if (data) {
        setRecords(data.map((item: any) => ({
          id: item.recordId,
          courseId: item.courseId,
          courseName: item.courseName || '未知课程',
          sceneName: item.sceneName || '未知场景',
          startTime: item.startTime,
          endTime: item.endTime,
          totalScore: item.totalScore,
          summary: item.summary,
          status: item.endTime ? 'completed' : 'in_progress',
        })));
      }
    } catch (error) {
      console.error('获取练习历史失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRecordClick = (record: PracticeHistoryRecord) => {
    if (record.status === 'in_progress') {
      // 继续未完成的对话
      navigate(`/chat?recordId=${record.id}`);
    }
  };

  const handleFilter = () => {
    const status = statusFilter === 'all' ? undefined : statusFilter;
    const startTime = dateRange.start ? `${dateRange.start}T00:00:00Z` : undefined;
    const endTime = dateRange.end ? `${dateRange.end}T23:59:59Z` : undefined;
    fetchHistory(status, startTime, endTime);
  };

  const handleReset = () => {
    setStatusFilter('all');
    setDateRange(getDefaultDateRange());
    fetchHistory(undefined, undefined, undefined);
  };

  const formatDateTime = (dateStr?: string) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="w-8 h-8 border-4 border-primary-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">练习历史</h2>
        <span className="text-sm text-gray-400">{records.length} 条记录</span>
      </div>

      {/* 筛选区域 */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 mb-4">
        <div className="flex items-center gap-2 mb-3">
          <Filter className="w-4 h-4 text-gray-400" />
          <span className="text-sm font-medium text-gray-700">筛选条件</span>
        </div>
        
        {/* 状态筛选 */}
        <div className="flex gap-2 mb-3">
          {[
            { value: 'all', label: '全部', icon: Loader },
            { value: 'completed', label: '已完成', icon: CheckCircle },
            { value: 'in_progress', label: '进行中', icon: Clock },
          ].map((item) => {
            const Icon = item.icon;
            const isActive = statusFilter === item.value;
            return (
              <button
                key={item.value}
                onClick={() => setStatusFilter(item.value as StatusType)}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-500 text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <Icon className="w-3 h-3" />
                {item.label}
              </button>
            );
          })}
        </div>

        {/* 时间范围 */}
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-400" />
          <input
            type="date"
            value={dateRange.start}
            onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
            className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-primary-500"
          />
          <span className="text-gray-400">~</span>
          <input
            type="date"
            value={dateRange.end}
            onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
            className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-primary-500"
          />
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={handleFilter}
            className="flex-1 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium hover:bg-primary-600 transition-colors"
          >
            筛选
          </button>
          <button
            onClick={handleReset}
            className="flex-1 py-2 bg-gray-100 text-gray-600 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
          >
            重置
          </button>
        </div>
      </div>

      {/* 记录列表 */}
      {records.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-gray-400">
          <Star className="w-16 h-16 mb-4 opacity-50" />
          <p className="text-lg">暂无练习记录</p>
          <p className="text-sm mt-2">完成首次练习后，记录将显示在这里</p>
        </div>
      ) : (
        <div className="space-y-3">
          {records.map((record) => (
            <div
              key={record.id}
              onClick={() => handleRecordClick(record)}
              className={`bg-white rounded-xl p-4 shadow-sm border border-gray-100 transition-shadow cursor-pointer ${
                record.status === 'in_progress' ? 'hover:shadow-lg hover:border-primary-200' : 'hover:shadow-md'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-medium text-gray-800">{record.courseName}</h3>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full ${
                        record.status === 'completed'
                          ? 'bg-green-100 text-green-600'
                          : 'bg-yellow-100 text-yellow-600'
                      }`}
                    >
                      {record.status === 'completed' ? '已完成' : '进行中'}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mb-3">{record.sceneName}</p>
                  <div className="flex items-center gap-4 text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDateTime(record.startTime)}
                      {record.endTime && (
                        <span className="mx-1">~</span>
                      )}
                      {record.endTime && formatDateTime(record.endTime)}
                    </span>
                    {record.totalScore !== undefined && (
                      <span className="flex items-center gap-1">
                        <Star className="w-3 h-3" />
                        {record.totalScore}分
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex flex-col items-end">
                  {record.status === 'completed' && record.totalScore !== undefined && (
                    <div className="flex items-center gap-1 bg-primary-50 px-3 py-1 rounded-lg">
                      <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                      <span className="font-semibold text-primary-600">{record.totalScore}</span>
                    </div>
                  )}
                  <ChevronRight className="w-5 h-5 text-gray-300 mt-2" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}