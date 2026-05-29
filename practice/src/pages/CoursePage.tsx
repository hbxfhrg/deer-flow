import { useState, useEffect } from 'react';
import { Save, Plus, X, ChevronRight, BookOpen, Trash2, Edit3, Clock, Target, Star, Users } from 'lucide-react';
import api from '../api';
import type { Course, Scene } from '@/types';

// 课程类型与模式选项
const COURSE_TYPES = [
  { value: 1, label: '练习' },
  { value: 2, label: '考试' },
];
const STATUS_OPTIONS = [
  { value: 0, label: '未发布' },
  { value: 1, label: '已发布' },
  { value: 2, label: '已结束' },
];

// 练习模式选项
const PRACTICE_MODES = [
  { value: 'text', label: '文本' },
  { value: 'voice', label: '语音' },
];

// 默认空表单
const emptyForm = () => ({
  course_name: '',
  courseType: 1,
  sceneId: undefined as number | undefined,
  simulatedRoleId: undefined as number | undefined,
  practiceMode: 'text',
  automatically: 0,
  difficulty: undefined as number | undefined,
  totalScore: 100,
  passingScore: 60,
  timeLimit: undefined as number | undefined,
  maxAttempts: 1,
  startTime: '',
  endTime: '',
  status: 0, // 默认未发布
});

export function CoursePage() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [scenes, setScenes] = useState<Scene[]>([]);

  // 弹窗状态
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null);

  // 表单数据
  const [form, setForm] = useState(emptyForm());

  // 编辑表单独立状态
  const [editForm, setEditForm] = useState(emptyForm());

  // 加载场景列表
  const loadScenes = async () => {
    try {
      const data = await api.scenes.list();
      if (data) setScenes(data);
    } catch (error) {
      console.error('加载场景失败:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        const [coursesData, scenesData] = await Promise.all([
          api.courses.list(),
          api.scenes.list(),
        ]);
        if (coursesData) setCourses(coursesData);
        if (scenesData) setScenes(scenesData);
      } catch (error) {
        console.error('加载数据失败:', error);
      }
    };
    loadData();
  }, []);

  // 切换状态
  const changeStatus = async (courseId: number, newStatus: number) => {
    try {
      await api.courses.update(courseId, { status: newStatus });
      const updated = await api.courses.list();
      if (updated) setCourses(updated);
    } catch (error) {
      console.error('操作失败:', error);
      alert('操作失败，请稍后重试');
    }
  };

  // 删除课程
  const deleteCourse = async (courseId: number) => {
    if (!confirm('确定要删除这个课程吗？')) return;
    try {
      await api.courses.delete(courseId);
      const updated = await api.courses.list();
      if (updated) setCourses(updated);
      setSelectedCourseId(null);
    } catch (error) {
      console.error('删除课程失败:', error);
      alert('删除失败，请稍后重试');
    }
  };

  // 打开编辑弹窗
  const openEditModal = async (course: Course) => {
    await loadScenes();
    setEditingCourse(course);
    setEditForm({
      course_name: course.course_name || '',
      courseType: course.courseType ?? 1,
      sceneId: course.sceneId ?? undefined,
      simulatedRoleId: course.simulatedRoleId ?? undefined,
      practiceMode: course.practiceMode || 'text',
      automatically: course.automatically ?? 0,
      difficulty: course.difficulty ?? undefined,
      totalScore: course.totalScore ?? 100,
      passingScore: course.passingScore ?? 60,
      timeLimit: course.timeLimit ?? undefined,
      maxAttempts: course.maxAttempts ?? 1,
      startTime: course.startTime ? course.startTime.slice(0, 10) : '',
      endTime: course.endTime ? course.endTime.slice(0, 10) : '',
      status: course.status ?? 0,
    });
    setShowEditModal(true);
  };

  // 保存新课程
  const saveNewCourse = async () => {
    if (!form.course_name.trim()) { alert('请输入课程名称'); return; }
    if (!form.sceneId) { alert('请选择关联场景'); return; }
    if (!form.startTime) { alert('请选择开始日期'); return; }
    if (!form.endTime) { alert('请选择结束日期'); return; }

    try {
      const currentUser = api.auth.getCurrentUser();
      await api.courses.create({
        course_name: form.course_name.trim(),
        courseType: form.courseType,
        sceneId: form.sceneId,
        simulatedRoleId: form.simulatedRoleId,
        practiceMode: form.practiceMode,
        automatically: form.automatically,
        difficulty: form.difficulty,
        totalScore: form.totalScore,
        passingScore: form.passingScore,
        timeLimit: form.timeLimit,
        maxAttempts: form.maxAttempts,
        startTime: form.startTime || undefined,
        endTime: form.endTime || undefined,
        status: form.status,
        create_by: currentUser ? currentUser.user_name : '',
      } as any);

      const updated = await api.courses.list();
      if (updated) setCourses(updated);
      alert('课程创建成功！');
      setShowAddModal(false);
      setForm(emptyForm());
    } catch (error) {
      console.error('创建课程失败:', error);
      alert('创建失败，请稍后重试');
    }
  };

  // 保存编辑
  const saveEditedCourse = async () => {
    if (!editingCourse) return;
    const ef = editForm;
    if (!ef.course_name.trim()) { alert('请输入课程名称'); return; }
    if (!ef.startTime) { alert('请选择开始日期'); return; }
    if (!ef.endTime) { alert('请选择结束日期'); return; }

    try {
      const payload: any = {};
      if (ef.course_name !== editingCourse.course_name) payload.course_name = ef.course_name.trim();
      if (ef.courseType !== editingCourse.courseType) payload.courseType = ef.courseType;
      if (ef.sceneId !== editingCourse.sceneId) payload.sceneId = ef.sceneId;
      if (ef.simulatedRoleId !== editingCourse.simulatedRoleId) payload.simulatedRoleId = ef.simulatedRoleId;
      if (ef.practiceMode !== (editingCourse.practiceMode || 'text')) payload.practiceMode = ef.practiceMode;
      if (ef.automatically !== (editingCourse.automatically ?? 0)) payload.automatically = ef.automatically;
      if (ef.difficulty !== editingCourse.difficulty) payload.difficulty = ef.difficulty;
      if (ef.totalScore !== (editingCourse.totalScore ?? 100)) payload.totalScore = ef.totalScore;
      if (ef.passingScore !== (editingCourse.passingScore ?? 60)) payload.passingScore = ef.passingScore;
      if ((ef.timeLimit ?? undefined) !== (editingCourse.timeLimit ?? undefined)) payload.timeLimit = ef.timeLimit || undefined;
      if (ef.maxAttempts !== (editingCourse.maxAttempts ?? 1)) payload.maxAttempts = ef.maxAttempts;
      if (ef.startTime !== (editingCourse.startTime ? editingCourse.startTime.slice(0, 10) : '')) payload.startTime = ef.startTime || undefined;
      if (ef.endTime !== (editingCourse.endTime ? editingCourse.endTime.slice(0, 10) : '')) payload.endTime = ef.endTime || undefined;
      if (ef.status !== editingCourse.status) payload.status = ef.status;

      if (Object.keys(payload).length === 0) {
        alert('没有需要修改的内容');
        return;
      }

      await api.courses.update(editingCourse.courseId, payload);
      const updated = await api.courses.list();
      if (updated) setCourses(updated);
      alert('课程修改成功！');
      setShowEditModal(false);
      setEditingCourse(null);
    } catch (error) {
      console.error('修改课程失败:', error);
      alert('修改失败，请稍后重试');
    }
  };

  // 表单控件工厂
  const renderFormFields = (
    f: ReturnType<typeof emptyForm>,
    setter: (updater: (prev: any) => any) => void,
  ) => (
    <div className="space-y-4">

      {/* ========== 基本信息 ========== */}
      <div className="p-4 bg-blue-50 rounded-xl space-y-4">
        <p className="text-xs text-blue-600 font-medium">📋 基本信息</p>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">课程名称<span className="text-red-500 ml-1">*</span></label>
          <input type="text" value={f.course_name} onChange={e => setter(prev => ({ ...prev, course_name: e.target.value }))}
            placeholder="请输入课程名称"
            className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">课程类型</label>
            <select value={f.courseType} onChange={e => setter(prev => ({ ...prev, courseType: Number(e.target.value) }))}
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500">
              {COURSE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">发布状态</label>
            <select value={f.status} onChange={e => setter(prev => ({ ...prev, status: Number(e.target.value) }))}
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500">
              {STATUS_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">关联场景<span className="text-red-500 ml-1">*</span></label>
          <select value={f.sceneId ?? ''} onChange={e => setter(prev => ({ ...prev, sceneId: e.target.value ? Number(e.target.value) : undefined }))}
            className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500">
            <option value="">请选择场景</option>
            {scenes.map(s => <option key={s.scene_id} value={s.scene_id}>{s.scene_name}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">难度等级</label>
            <select value={f.difficulty ?? ''} onChange={e => setter(prev => ({ ...prev, difficulty: e.target.value ? Number(e.target.value) : undefined }))}
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500">
              <option value="">不设置</option>
              <option value="1">低</option>
              <option value="2">中</option>
              <option value="3">高</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">模拟角色ID</label>
            <input type="number" value={f.simulatedRoleId ?? ''} onChange={e => setter(prev => ({ ...prev, simulatedRoleId: e.target.value ? Number(e.target.value) : undefined }))}
              placeholder="暂不设置"
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">练习模式</label>
            <select value={f.practiceMode} onChange={e => setter(prev => ({ ...prev, practiceMode: e.target.value }))}
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500">
              {PRACTICE_MODES.map(m => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">是否自动播放</label>
            <select value={f.automatically} onChange={e => setter(prev => ({ ...prev, automatically: Number(e.target.value) }))}
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500">
              <option value={0}>否</option>
              <option value={1}>是</option>
            </select>
          </div>
        </div>
      </div>

      {/* ========== 评分与规则 ========== */}
      <div className="p-4 bg-amber-50 rounded-xl space-y-4">
        <p className="text-xs text-amber-600 font-medium">📊 评分与规则</p>
        
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">课程总分</label>
            <input type="number" min={0} value={f.totalScore} onChange={e => setter(prev => ({ ...prev, totalScore: Number(e.target.value) || 0 }))}
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">达标分数</label>
            <input type="number" min={0} value={f.passingScore} onChange={e => setter(prev => ({ ...prev, passingScore: Number(e.target.value) || 0 }))}
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">时长限制（分钟）</label>
            <input type="number" min={0} value={f.timeLimit ?? ''} onChange={e => setter(prev => ({ ...prev, timeLimit: e.target.value ? Number(e.target.value) : undefined }))}
              placeholder="不限制"
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">允许尝试次数</label>
            <input type="number" min={1} value={f.maxAttempts} onChange={e => setter(prev => ({ ...prev, maxAttempts: Number(e.target.value) || 1 }))}
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500" />
          </div>
        </div>
      </div>

      {/* ========== 开放时间 ========== */}
      <div className="p-4 bg-green-50 rounded-xl space-y-3">
        <p className="text-xs text-green-600 font-medium">📅 开放时间</p>
        <div className="flex items-center gap-3">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">开始日期<span className="text-red-500 ml-1">*</span></label>
            <input type="date" value={f.startTime}
              onChange={e => setter(prev => ({ ...prev, startTime: e.target.value }))}
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500" />
          </div>
          <span className="text-gray-400 text-sm pt-6 shrink-0">至</span>
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">结束日期<span className="text-red-500 ml-1">*</span></label>
            <input type="date" value={f.endTime}
              onChange={e => setter(prev => ({ ...prev, endTime: e.target.value }))}
              className="w-full px-4 py-2 border border-gray-200 rounded-xl focus:outline-none focus:border-primary-500" />
          </div>
        </div>
      </div>

    </div>
  );

  // 状态标签
  const statusBadge = (s: number) => {
    const map: Record<number, { label: string; cls: string }> = {
      0: { label: '未发布', cls: 'bg-gray-100 text-gray-600' },
      1: { label: '已发布', cls: 'bg-green-100 text-green-700' },
      2: { label: '已结束', cls: 'bg-red-100 text-red-600' },
    };
    const info = map[s] || map[0];
    return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${info.cls}`}>{info.label}</span>;
  };

  // 类型标签
  const typeLabel = (t: number) => {
    const m = COURSE_TYPES.find(x => x.value === t);
    return m?.label || '练习';
  };

  // 难度标签
  const difficultyLabel = (d: number) => {
    const map: Record<number, string> = { 1: '低', 2: '中', 3: '高' };
    return map[d] || `${d}`;
  };

  return (
    <div className="px-4 py-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-gray-800">练习课程</h2>
          <p className="text-sm text-gray-500">管理您的练习与考试课程</p>
        </div>
        <button
          onClick={async () => { await loadScenes(); setForm(emptyForm()); setShowAddModal(true); }}
          className="flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-xl text-sm font-medium hover:bg-primary-600 transition-colors"
        >
          <Plus className="w-4 h-4" />
          添加课程
        </button>
      </div>

      {/* 课程列表 */}
      <div className="space-y-3">
        {courses.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <BookOpen className="w-16 h-16 mb-4 opacity-40" />
            <p className="text-sm">暂无课程数据</p>
            <p className="text-xs mt-1">点击上方"添加课程"创建第一个课程</p>
          </div>
        ) : (
          courses.map((course) => (
            <div key={course.courseId}
              onClick={() => setSelectedCourseId(selectedCourseId === course.courseId ? null : course.courseId)}
              className="bg-white rounded-xl p-4 border border-gray-100 hover:border-gray-200 transition-colors cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${course.courseType === 2 ? 'bg-orange-50 text-orange-500' : 'bg-blue-50 text-blue-500'}`}>
                    {course.courseType === 2 ? <Target className="w-5 h-5" /> : <BookOpen className="w-5 h-5" />}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h3 className="font-medium text-gray-800 truncate">{course.course_name}</h3>
                      {statusBadge(course.status)}
                    </div>
                    <div className="flex items-center gap-2 mt-1 flex-wrap text-xs text-gray-400">
                      <span className="px-1.5 py-0.5 bg-gray-100 rounded">{typeLabel(course.courseType)}</span>
                      {course.sceneName && <span className="text-blue-500">{course.sceneName}</span>}
                      {course.difficulty && <span>{difficultyLabel(course.difficulty)}</span>}
                    </div>
                  </div>
                </div>
                <ChevronRight className={`w-5 h-5 text-gray-400 shrink-0 transition-transform ${selectedCourseId === course.courseId ? 'rotate-90' : ''}`} />
              </div>

              {/* 展开详情 */}
              {selectedCourseId === course.courseId && (
                <div className="mt-4 pt-4 border-t border-gray-100 space-y-3" onClick={e => e.stopPropagation()}>
                  {/* 基本信息 */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <InfoItem icon={<BookOpen className="w-4 h-4" />} label="课程类型" value={typeLabel(course.courseType)} />
                    {course.difficulty && <InfoItem icon={<Target className="w-4 h-4" />} label="难度" value={difficultyLabel(course.difficulty)} />}
                    {course.simulatedRoleId && <InfoItem icon={<Users className="w-4 h-4" />} label="模拟角色" value={String(course.simulatedRoleId)} />}
                    {course.sceneName && <InfoItem label="关联场景" value={course.sceneName} />}
                  </div>

                  {/* 分数信息 */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <InfoItem icon={<Target className="w-4 h-4" />} label="总分" value={String(course.totalScore ?? 100)} />
                    <InfoItem icon={<Star className="w-4 h-4" />} label="达标分数" value={String(course.passingScore ?? 60)} />
                    {course.timeLimit != null && <InfoItem icon={<Clock className="w-4 h-4" />} label="时长限制" value={`${course.timeLimit} 分钟`} />}
                    <InfoItem icon={<Users className="w-4 h-4" />} label="尝试次数" value={String(course.maxAttempts ?? 1)} />
                  </div>

                  {/* 时间范围 */}
                  {(course.startTime || course.endTime) && (
                    <div className="p-3 bg-gray-50 rounded-lg text-sm">
                      <p className="text-xs text-gray-400 mb-1">开放时间</p>
                      <p className="text-gray-600">
                        {course.startTime ? course.startTime.slice(0, 10) : '不限'} ~ {course.endTime ? course.endTime.slice(0, 10) : '不限'}
                      </p>
                    </div>
                  )}

                  {/* 元信息 */}
                  {course.createdAt && (
                    <div className="text-xs text-gray-400">
                      创建时间：{course.createdAt.slice(0, 16).replace('T', ' ')}
                      {course.create_by && ` | 创建人：${course.create_by}`}
                    </div>
                  )}

                  {/* 操作按钮 */}
                  <div className="flex gap-2">
                    <button onClick={() => openEditModal(course)}
                      className="flex-1 py-2 rounded-lg text-sm font-medium bg-blue-500 text-white hover:bg-blue-600 transition-colors">
                      <Edit3 className="w-4 h-4 inline mr-1 -mt-0.5" />修改
                    </button>
                    {course.status === 1 ? (
                      <button onClick={() => changeStatus(course.courseId, 0)}
                        className="flex-1 py-2 rounded-lg text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors">
                        下架
                      </button>
                    ) : course.status === 0 ? (
                      <button onClick={() => changeStatus(course.courseId, 1)}
                        className="flex-1 py-2 rounded-lg text-sm font-medium bg-green-500 text-white hover:bg-green-600 transition-colors">
                        发布
                      </button>
                    ) : (
                      <button onClick={() => changeStatus(course.courseId, 1)}
                        className="flex-1 py-2 rounded-lg text-sm font-medium bg-gray-100 text-gray-600 hover:bg-gray-200 transition-colors">
                        重新发布
                      </button>
                    )}
                    <button onClick={() => deleteCourse(course.courseId)}
                      className="flex-1 py-2 rounded-lg text-sm font-medium bg-red-500 text-white hover:bg-red-600 transition-colors">
                      <Trash2 className="w-4 h-4 inline mr-1 -mt-0.5" />删除
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* 添加课程弹窗（底部滑出） */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50">
          <div className="bg-white w-full max-w-lg rounded-t-2xl p-6 animate-slide-up max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-800">添加新课程</h3>
              <button onClick={() => setShowAddModal(false)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            {renderFormFields(form, setForm)}
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowAddModal(false)}
                className="flex-1 py-2 border border-gray-200 rounded-xl text-gray-600 font-medium hover:bg-gray-50 transition-colors">
                取消
              </button>
              <button onClick={saveNewCourse}
                disabled={!form.course_name.trim() || !form.sceneId || !form.startTime || !form.endTime}
                className="flex-1 py-2 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                <Save className="w-4 h-4" />保存
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 编辑课程弹窗（居中） */}
      {showEditModal && editingCourse && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
          <div className="bg-white w-full max-w-lg rounded-2xl p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-800">修改课程</h3>
              <button onClick={() => { setShowEditModal(false); setEditingCourse(null); }}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            {renderFormFields(
              editForm,
              (updater) => setEditForm(prev => updater(prev)),
            )}
            <div className="flex gap-3 mt-6">
              <button onClick={() => { setShowEditModal(false); setEditingCourse(null); }}
                className="flex-1 py-2 border border-gray-200 rounded-xl text-gray-600 font-medium hover:bg-gray-50 transition-colors">
                取消
              </button>
              <button onClick={saveEditedCourse}
                className="flex-1 py-2 bg-primary-500 text-white rounded-xl font-medium hover:bg-primary-600 transition-colors flex items-center justify-center gap-2">
                <Save className="w-4 h-4" />保存修改
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ---- 复用小部件 ----

// 详情信息项
const InfoItem = ({ icon, label, value }: { icon?: React.ReactNode; label: string; value: string }) => (
  <div className="flex items-center gap-2">
    {icon && <span className="text-gray-400">{icon}</span>}
    <span className="text-gray-400">{label}：</span>
    <span className="text-gray-700 font-medium">{value}</span>
  </div>
);

