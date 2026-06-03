"""ORM 模型 — 从 deerflow/roleplay/models.py 迁移，移除 deerflow 依赖"""

from datetime import datetime
from sqlalchemy import JSON, DateTime, String, Integer, Text, BigInteger, Float, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SceneRow(Base):
    __tablename__ = "pract_scene_set"

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


class CourseRow(Base):
    __tablename__ = "pract_course"

    course_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_name: Mapped[str] = mapped_column(String(100), nullable=False)
    course_type: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    scene_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    simulated_role_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    practice_mode: Mapped[str] = mapped_column(String(20), nullable=False, default='text')
    automatically: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=True)
    total_score: Mapped[int] = mapped_column(Integer, nullable=True, default=100)
    passing_score: Mapped[int] = mapped_column(Integer, nullable=True, default=60)
    time_limit: Mapped[int] = mapped_column(Integer, nullable=True)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=True, default=1)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    create_by: Mapped[str] = mapped_column(String(50), default='')
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class EvaluationRow(Base):
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


class DialogDetailRow(Base):
    __tablename__ = "pract_dialog_detail"

    dialog_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    record_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    speaker: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False, default="1")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    intent_analysis: Mapped[str] = mapped_column(JSON, nullable=True)
    score: Mapped[float] = mapped_column(DECIMAL(5, 2), nullable=True)
    feedback: Mapped[str] = mapped_column(Text, nullable=True)
    create_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CourseRecordRow(Base):
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
    total_rounds: Mapped[int] = mapped_column(Integer, nullable=True)
