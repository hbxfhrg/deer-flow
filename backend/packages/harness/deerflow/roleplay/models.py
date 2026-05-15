from datetime import UTC, datetime
from sqlalchemy import JSON, DateTime, String, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from deerflow.roleplay import RoleplayBase

class SceneRow(RoleplayBase):
    __tablename__ = "scenes"
    
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium")
    rounds: Mapped[int] = mapped_column(Integer, default=5)
    time_per_round: Mapped[int] = mapped_column(Integer, default=120)
    total_time_limit: Mapped[int] = mapped_column(Integer, default=600)
    model_name: Mapped[str] = mapped_column(String(128), default="gpt-4o-mini")
    system_prompt: Mapped[str] = mapped_column(Text)
    user_prompt_template: Mapped[str] = mapped_column(Text)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class EvaluationRow(RoleplayBase):
    __tablename__ = "evaluations"
    
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
    __tablename__ = "practice_records"
    
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