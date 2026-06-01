from datetime import UTC, datetime
from sqlalchemy import JSON, DateTime, String, Integer, Text, Boolean, BigInteger, Float, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column

from deerflow.roleplay import RoleplayBase

class SceneRow(RoleplayBase):
    __tablename__ = "pract_scene_set"
    
    # 数据库中已有的字段
    scene_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scene_name: Mapped[str] = mapped_column(String(100), nullable=False)
    scene_description: Mapped[str] = mapped_column(String(500))
    scene_cover: Mapped[str] = mapped_column(String(800))
    asr_correct_lib_id: Mapped[int] = mapped_column(Integer)
    sensitive_word_lib_id: Mapped[int] = mapped_column(Integer)
    dialog_round_limit: Mapped[int] = mapped_column(Integer)
    end_speech: Mapped[str] = mapped_column(Text)
    status: Mapped[int] = mapped_column(Integer, default=1)
    create_by: Mapped[str] = mapped_column(String(50))
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    update_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    
    # 模型字段
    model_name: Mapped[str] = mapped_column(String(128), nullable=True)
    system_prompt: Mapped[str] = mapped_column(Text)
    user_prompt_template: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # 自由对练功能新增字段
    practice_mode: Mapped[str] = mapped_column(String(20), default="剧本式")
    knowledge_base: Mapped[str] = mapped_column(Text)
    summary_text: Mapped[str] = mapped_column(Text)
    exam_categories: Mapped[str] = mapped_column(String(200))
    scoring_rules: Mapped[str] = mapped_column(Text)

class CourseRow(RoleplayBase):
    __tablename__ = "pract_course"
    
    course_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_name: Mapped[str] = mapped_column(String(100), nullable=False)
    course_type: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 1: 练习，2: 考试
    scene_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 关联的剧本 ID
    simulated_role_id: Mapped[int] = mapped_column(BigInteger, nullable=True)  # 关联的模拟角色 ID
    practice_mode: Mapped[str] = mapped_column(String(20), nullable=False, default='text')  # text: 文本，voice: 语音，call: 模拟电话
    automatically: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # 是否自动播放（0: 否，1: 是）
    difficulty: Mapped[int] = mapped_column(Integer, nullable=True)  # 难度等级
    total_score: Mapped[int] = mapped_column(Integer, nullable=True, default=100)  # 课程总分
    passing_score: Mapped[int] = mapped_column(Integer, nullable=True, default=60)  # 达标分数要求
    time_limit: Mapped[int] = mapped_column(Integer, nullable=True)  # 单次练习时长限制（分钟）
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=True, default=1)  # 允许尝试次数
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)  # 开放开始时间
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)  # 开放结束时间
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)  # 0: 未发布，1: 已发布，2: 已结束
    create_by: Mapped[str] = mapped_column(String(50), default='')  # 创建人
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # 创建时间

class EvaluationRow(RoleplayBase):
    __tablename__ = "pract_evaluation"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(64), index=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    scene_id: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[str] = mapped_column(String(64))
    round_number: Mapped[int] = mapped_column(Integer)
    total_score: Mapped[int] = mapped_column(Integer)
    dimension_scores: Mapped[dict] = mapped_column(JSON)
    strengths: Mapped[dict] = mapped_column(JSON)
    improvements: Mapped[dict] = mapped_column(JSON)
    summary: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class DialogDetailRow(RoleplayBase):
    __tablename__ = "pract_dialog_detail"

    dialog_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 关联 pract_course_record.id (int)
    speaker: Mapped[int] = mapped_column(Integer, nullable=False)  # 1: 学员, 2: AI/客户
    content_type: Mapped[str] = mapped_column(String(20), nullable=False, default="1")  # 内容类型 (1:文本, 2:音频URL)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 发言内容
    content_url: Mapped[str] = mapped_column(String(1000), nullable=True)  # 录音文件地址：AI时存TTS生成的，员工时存上传的
    intent_analysis: Mapped[str] = mapped_column(JSON, nullable=True)  # AI对这句话的意图分析结果 (JSON)
    score: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)  # 该句得分（如果有考核点）
    feedback: Mapped[str] = mapped_column(Text, nullable=True)  # AI对该句的实时反馈或建议
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)  # 发言时间


class CourseRecordRow(RoleplayBase):
    __tablename__ = "pract_course_record"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(Integer)
    scene_id: Mapped[int] = mapped_column(Integer)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    total_score: Mapped[int] = mapped_column(Integer, nullable=True)
    user_name: Mapped[str] = mapped_column(String(50))
    nick_name: Mapped[str] = mapped_column(String(200), nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    conversation_id: Mapped[str] = mapped_column(String(100), nullable=True)
    scene_name: Mapped[str] = mapped_column(String(255), nullable=True)
    course_type: Mapped[int] = mapped_column(Integer, nullable=True)
    accord_finish: Mapped[int] = mapped_column(Integer, nullable=True)
    last_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    practice_mode: Mapped[str] = mapped_column(String(20), nullable=True)
    total_rounds: Mapped[int] = mapped_column(Integer, nullable=True)  # 总轮次，在对练开始时计算并存储