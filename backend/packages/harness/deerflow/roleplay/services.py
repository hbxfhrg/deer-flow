from datetime import datetime, UTC
from uuid import uuid4
from sqlalchemy import select, desc, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from deerflow.roleplay import get_db, get_session_factory
from deerflow.roleplay.models import SceneRow, EvaluationRow, PracticeRecordRow

class SceneService:
    @staticmethod
    async def get_scenes():
        async with get_db() as session:
            result = await session.execute(
                select(SceneRow).where(SceneRow.enabled == True).order_by(SceneRow.name)
            )
            return result.scalars().all()

    @staticmethod
    async def get_scene(scene_id: str):
        async with get_db() as session:
            result = await session.execute(
                select(SceneRow).where(SceneRow.id == scene_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def create_scene(data: dict):
        async with get_db() as session:
            scene = SceneRow(
                id=data.get("id") or str(uuid4()),
                name=data["name"],
                description=data.get("description", ""),
                difficulty=data.get("difficulty", "medium"),
                rounds=data.get("rounds", 5),
                time_per_round=data.get("time_per_round", 120),
                total_time_limit=data.get("total_time_limit", 600),
                model_name=data.get("model_name", "gpt-4o-mini"),
                system_prompt=data.get("system_prompt", ""),
                user_prompt_template=data.get("user_prompt_template", ""),
                enabled=data.get("enabled", True),
                metadata_json=data.get("metadata_json", {}),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            session.add(scene)
            await session.commit()
            await session.refresh(scene)
            return scene

    @staticmethod
    async def update_scene(scene_id: str, data: dict):
        async with get_db() as session:
            result = await session.execute(
                select(SceneRow).where(SceneRow.id == scene_id)
            )
            scene = result.scalar_one_or_none()
            if scene:
                for key, value in data.items():
                    if hasattr(scene, key) and value is not None:
                        setattr(scene, key, value)
                scene.updated_at = datetime.now(UTC)
                await session.commit()
                await session.refresh(scene)
            return scene

    @staticmethod
    async def delete_scene(scene_id: str):
        async with get_db() as session:
            result = await session.execute(
                select(SceneRow).where(SceneRow.id == scene_id)
            )
            scene = result.scalar_one_or_none()
            if scene:
                scene.enabled = False
                scene.updated_at = datetime.now(UTC)
                await session.commit()
                return True
            return False

class EvaluationService:
    @staticmethod
    async def get_evaluations(thread_id: str = None, user_id: str = None):
        async with get_db() as session:
            query = select(EvaluationRow)
            if thread_id:
                query = query.where(EvaluationRow.thread_id == thread_id)
            if user_id:
                query = query.where(EvaluationRow.user_id == user_id)
            query = query.order_by(desc(EvaluationRow.created_at))
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_evaluation(eval_id: str):
        async with get_db() as session:
            result = await session.execute(
                select(EvaluationRow).where(EvaluationRow.id == eval_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def create_evaluation(data: dict):
        async with get_db() as session:
            eval_row = EvaluationRow(
                id=data.get("id") or str(uuid4()),
                thread_id=data["thread_id"],
                run_id=data["run_id"],
                scene_id=data["scene_id"],
                user_id=data["user_id"],
                round_number=data.get("round_number", 1),
                total_score=data.get("total_score", 0),
                dimension_scores=data.get("dimension_scores", {}),
                strengths=data.get("strengths", {}),
                improvements=data.get("improvements", {}),
                summary=data.get("summary", ""),
                status=data.get("status", "pending"),
                created_at=datetime.now(UTC)
            )
            session.add(eval_row)
            await session.commit()
            await session.refresh(eval_row)
            return eval_row

    @staticmethod
    async def update_evaluation(eval_id: str, data: dict):
        async with get_db() as session:
            result = await session.execute(
                select(EvaluationRow).where(EvaluationRow.id == eval_id)
            )
            eval_row = result.scalar_one_or_none()
            if eval_row:
                for key, value in data.items():
                    if hasattr(eval_row, key) and value is not None:
                        setattr(eval_row, key, value)
                await session.commit()
                await session.refresh(eval_row)
            return eval_row

class PracticeRecordService:
    @staticmethod
    async def get_practice_records(user_id: str = None, scene_id: str = None):
        async with get_db() as session:
            query = select(PracticeRecordRow)
            if user_id:
                query = query.where(PracticeRecordRow.user_id == user_id)
            if scene_id:
                query = query.where(PracticeRecordRow.scene_id == scene_id)
            query = query.order_by(desc(PracticeRecordRow.start_time))
            result = await session.execute(query)
            return result.scalars().all()

    @staticmethod
    async def get_practice_record(record_id: str):
        async with get_db() as session:
            result = await session.execute(
                select(PracticeRecordRow).where(PracticeRecordRow.id == record_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def create_practice_record(data: dict):
        async with get_db() as session:
            record = PracticeRecordRow(
                id=data.get("id") or str(uuid4()),
                thread_id=data["thread_id"],
                scene_id=data["scene_id"],
                user_id=data["user_id"],
                start_time=datetime.now(UTC),
                total_rounds=data.get("total_rounds", 5),
                completed_rounds=0,
                status="in_progress"
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    @staticmethod
    async def complete_practice_record(record_id: str, data: dict):
        async with get_db() as session:
            result = await session.execute(
                select(PracticeRecordRow).where(PracticeRecordRow.id == record_id)
            )
            record = result.scalar_one_or_none()
            if record:
                record.end_time = datetime.now(UTC)
                record.completed_rounds = data.get("completed_rounds", record.completed_rounds)
                record.avg_score = data.get("avg_score", 0)
                record.status = "completed"
                record.metadata_json = data.get("metadata_json", {})
                await session.commit()
                await session.refresh(record)
            return record

class StatisticsService:
    @staticmethod
    async def get_user_stats(user_id: str):
        sf = get_session_factory()
        async with sf() as session:
            record_result = await session.execute(
                select(
                    func.count(PracticeRecordRow.id).label("total_practices"),
                    func.sum(func.julianday(PracticeRecordRow.end_time) - func.julianday(PracticeRecordRow.start_time)).label("total_duration"),
                    func.avg(PracticeRecordRow.avg_score).label("avg_score")
                ).where(PracticeRecordRow.user_id == user_id)
            )
            return record_result.first()

    @staticmethod
    async def get_scene_stats(scene_id: str = None):
        sf = get_session_factory()
        async with sf() as session:
            query = select(
                PracticeRecordRow.scene_id,
                func.count(PracticeRecordRow.id).label("practice_count"),
                func.avg(PracticeRecordRow.avg_score).label("avg_score")
            ).group_by(PracticeRecordRow.scene_id)
            if scene_id:
                query = query.where(PracticeRecordRow.scene_id == scene_id)
            result = await session.execute(query)
            return result.all()

    @staticmethod
    async def get_leaderboard(limit: int = 10):
        sf = get_session_factory()
        async with sf() as session:
            query = select(
                PracticeRecordRow.user_id,
                func.count(PracticeRecordRow.id).label("practice_count"),
                func.avg(PracticeRecordRow.avg_score).label("avg_score")
            ).group_by(PracticeRecordRow.user_id)\
             .order_by(desc(func.avg(PracticeRecordRow.avg_score)))\
             .limit(limit)
            result = await session.execute(query)
            return result.all()