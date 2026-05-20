from datetime import UTC, datetime
from sqlalchemy import JSON, DateTime, String, Integer, Text, Boolean
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
    
    # 模型中新增的字段（需要添加到数据库）
    difficulty: Mapped[str] = mapped_column(String(20), default="简单")
    rounds: Mapped[int] = mapped_column(Integer, default=5)
    time_per_round: Mapped[int] = mapped_column(Integer, default=120)
    total_time_limit: Mapped[int] = mapped_column(Integer, default=600)
    model_name: Mapped[str] = mapped_column(String(128), default="gpt-4o-mini")
    system_prompt: Mapped[str] = mapped_column(Text)
    user_prompt_template: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    
    # 自由对练功能新增字段
    practice_mode: Mapped[str] = mapped_column(String(20), default="剧本式")
    knowledge_base: Mapped[str] = mapped_column(Text)
    summary_text: Mapped[str] = mapped_column(Text)
    exam_categories: Mapped[str] = mapped_column(String(200))
    scoring_rules: Mapped[str] = mapped_column(Text)

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