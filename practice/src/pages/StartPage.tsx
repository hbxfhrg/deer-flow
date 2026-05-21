import { Play, Target, Trophy, TrendingUp, BookOpen } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';
import type { Course } from '@/types';

const COURSE_ICONS = [
  { icon: Target, color: 'bg-blue-100 text-blue-600' },
  { icon: Trophy, color: 'bg-green-100 text-green-600' },
  { icon: TrendingUp, color: 'bg-purple-100 text-purple-600' },
  { icon: BookOpen, color: 'bg-orange-100 text-orange-600' },
];

export function StartPage() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [courses, setCourses] = useState<Course[]>([]);

  // 加载已发布的课程
  useEffect(() => {
    const loadCourses = async () => {
      try {
        const data = await api.courses.list();
        if (data) setCourses(data.filter(c => c.status === 1)); // 只显示已发布的
      } catch (error) {
        console.error('加载课程失败:', error);
      }
    };
    loadCourses();
  }, []);

  const handleStartPractice = async (courseId: number) => {
    setIsLoading(true);
    navigate(`/chat?courseId=${courseId}`);
  };

  return (
    <div className="px-4 py-6">
      {/* 欢迎区域 */}
      <div className="bg-gradient-to-br from-primary-500 to-primary-600 rounded-2xl p-6 text-white mb-6">
        <h2 className="text-xl font-bold mb-2">欢迎回来！</h2>
        <p className="text-primary-100 text-sm">今天也要努力提升对练技巧哦</p>
      </div>

      {/* 课程列表 */}
      <div className="mb-6">
        <h3 className="font-semibold text-gray-800 mb-3">练习课程</h3>
        {courses.length === 0 ? (
          <div className="bg-white rounded-xl p-8 text-center">
            <p className="text-gray-400 text-sm">暂无已发布的课程</p>
          </div>
        ) : (
          <div className="space-y-3">
            {courses.map((course, index) => {
              const iconConfig = COURSE_ICONS[index % COURSE_ICONS.length];
              const Icon = iconConfig.icon;
              return (
                <div
                  key={course.courseId}
                  className="w-full bg-white rounded-xl p-4 border border-gray-100 hover:border-gray-200 transition-all"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${iconConfig.color}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-gray-800 truncate">{course.course_name}</h4>
                      <p className="text-xs text-gray-400 truncate">{course.sceneName || '未关联场景'}</p>
                    </div>
                    <button
                      onClick={() => handleStartPractice(course.courseId)}
                      disabled={isLoading}
                      className="shrink-0 px-4 py-2 bg-primary-500 text-white text-sm font-medium rounded-lg hover:bg-primary-600 transition-colors disabled:opacity-50 flex items-center gap-1"
                    >
                      <Play className="w-3.5 h-3.5" />
                      开始练习
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* 今日建议 */}
      <div className="bg-amber-50 rounded-xl p-4">
        <h3 className="font-semibold text-amber-800 mb-2">💡 今日建议</h3>
        <p className="text-sm text-amber-700">
          今天可以尝试新场景，重点练习沟通与应变能力。记住要多使用具体数据来说服对方！
        </p>
      </div>
    </div>
  );
}