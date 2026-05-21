from datetime import UTC, datetime
from sqlalchemy import JSON, DateTime, String, Integer, Text, Boolean, BigInteger
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
    practice_mode: Mapped[str] = mapped_column(String(20), nullable=False)  # text: 文本，voice: 语音，call: 模拟电话
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

class PracticeRecordRow(RoleplayBase):
    __tablename__ = "pract_record"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(64), index=True)
    scene_id: Mapped[str] = mapped_column(String(64))
    user_id: Mapped[str] = mapped_column(String(64))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total_rounds: Mapped[int] = mapped_column(Integer)
    completed_rounds: Mapped[int] = mapped_column(Integer)
    avg_score: Mapped[float] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="completed")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)