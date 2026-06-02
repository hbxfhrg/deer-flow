from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import select, desc, func, update
from sqlalchemy.ext.asyncio import AsyncSession
import re

# 导入时区工具（从配置读取时区）
from deerflow.roleplay.timezone_utils import now_local

from deerflow.roleplay import get_db, get_session_factory
from deerflow.roleplay.models import SceneRow, EvaluationRow, CourseRow, CourseRecordRow

# 驼峰命名转下划线命名（通用函数）
def camel_to_snake(name: str) -> str:
    """
    将驼峰命名转换为下划线命名
    例如: practiceMode -> practice_mode, timePerRound -> time_per_round
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

class SceneService:
    @staticmethod
    async def get_scenes():
        async with get_db() as session:
            result = await session.execute(
                select(SceneRow).where(SceneRow.status == 1).order_by(SceneRow.scene_name)
            )
            return result.scalars().all()

    @staticmethod
    async def get_scene(scene_id: int):
        async with get_db() as session:
            result = await session.execute(
                select(SceneRow).where(SceneRow.scene_id == scene_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def create_scene(data: dict):
        async with get_db() as session:
            # 将驼峰命名转换为下划线命名
            snake_case_data = {camel_to_snake(k): v for k, v in data.items()}
            
            scene = SceneRow(
                # 数据库已有的字段（特殊处理 name -> scene_name, description -> scene_description）
                scene_name=data.get("name") or snake_case_data.get("scene_name"),
                scene_description=data.get("description") or snake_case_data.get("scene_description", ""),
                scene_cover=snake_case_data.get("scene_cover"),
                asr_correct_lib_id=snake_case_data.get("asr_correct_lib_id"),
                sensitive_word_lib_id=snake_case_data.get("sensitive_word_lib_id"),
                dialog_round_limit=snake_case_data.get("dialog_round_limit"),
                end_speech=snake_case_data.get("end_speech"),
                status=snake_case_data.get("enabled", True) if isinstance(snake_case_data.get("enabled", True), int) else (1 if snake_case_data.get("enabled", True) else 0),
                create_by=snake_case_data.get("create_by", "system"),
                create_time=now_local(),
                update_time=now_local(),
                
                # 模型新增的字段
                model_name=snake_case_data.get("model_name"),
                system_prompt=snake_case_data.get("system_prompt", ""),
                user_prompt_template=snake_case_data.get("user_prompt_template", ""),
                metadata_json=snake_case_data.get("metadata_json", {}),
                
                # 自由对练功能新增字段
                practice_mode=snake_case_data.get("practice_mode", "剧本式"),
                knowledge_base=snake_case_data.get("knowledge_base"),
                summary_text=snake_case_data.get("summary_text"),
                exam_categories=snake_case_data.get("exam_categories"),
                scoring_rules=snake_case_data.get("scoring_rules")
            )
            
            # prompt_template 存入 metadata_json（无需额外列）
            if snake_case_data.get("prompt_template"):
                scene.metadata_json = {**(scene.metadata_json or {}), "prompt_template": snake_case_data["prompt_template"]}
            session.add(scene)
            await session.commit()
            await session.refresh(scene)
            return scene

    @staticmethod
    async def update_scene(scene_id: int, data: dict):
        async with get_db() as session:
            result = await session.execute(
                select(SceneRow).where(SceneRow.scene_id == scene_id)
            )
            scene = result.scalar_one_or_none()
            if scene:
                for key, value in data.items():
                    if value is None:
                        continue
                    
                    # 将驼峰命名转换为下划线命名
                    db_key = camel_to_snake(key)
                    
                    # 特殊处理: enabled -> status
                    if key == "enabled":
                        setattr(scene, "status", 1 if value else 0)
                    # 特殊处理: promptTemplate/prompt_template -> metadata_json.prompt_template
                    elif key == "promptTemplate" or key == "prompt_template":
                        scene.metadata_json = {**(scene.metadata_json or {}), "prompt_template": value}
                    elif hasattr(scene, db_key):
                        setattr(scene, db_key, value)
                    elif hasattr(scene, key):
                        setattr(scene, key, value)
                
                scene.update_time = now_local()
                await session.commit()
                await session.refresh(scene)
            return scene

    @staticmethod
    async def delete_scene(scene_id: int):
        async with get_db() as session:
            result = await session.execute(
                select(SceneRow).where(SceneRow.scene_id == scene_id)
            )
            scene = result.scalar_one_or_none()
            if scene:
                scene.status = 0
                scene.update_time = now_local()
                await session.commit()
                return True
            return False

class CourseService:
    @staticmethod
    async def get_courses():
        async with get_db() as session:
            result = await session.execute(
                select(CourseRow).order_by(CourseRow.create_time.desc())
            )
            return result.scalars().all()

    @staticmethod
    async def get_course(course_id: int):
        async with get_db() as session:
            result = await session.execute(
                select(CourseRow).where(CourseRow.course_id == course_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def create_course(data: dict):
        async with get_db() as session:
            snake_case_data = {camel_to_snake(k): v for k, v in data.items()}
            course = CourseRow(
                course_name=snake_case_data.get("course_name"),
                course_type=snake_case_data.get("course_type", 1),
                scene_id=snake_case_data.get("scene_id"),
                simulated_role_id=snake_case_data.get("simulated_role_id"),
                practice_mode=snake_case_data.get("practice_mode", "text"),
                difficulty=snake_case_data.get("difficulty"),
                total_score=snake_case_data.get("total_score", 100),
                passing_score=snake_case_data.get("passing_score", 60),
                time_limit=snake_case_data.get("time_limit"),
                max_attempts=snake_case_data.get("max_attempts", 1),
                start_time=snake_case_data.get("start_time"),
                end_time=snake_case_data.get("end_time"),
                status=snake_case_data.get("status", 0),
                create_by=snake_case_data.get("create_by", ''),
                create_time=now_local(),
            )
            session.add(course)
            await session.commit()
            await session.refresh(course)
            return course

    @staticmethod
    async def update_course(course_id: int, data: dict):
        async with get_db() as session:
            result = await session.execute(
                select(CourseRow).where(CourseRow.course_id == course_id)
            )
            course = result.scalar_one_or_none()
            if course:
                for key, value in data.items():
                    if value is None:
                        continue
                    db_key = camel_to_snake(key)
                    if hasattr(course, db_key):
                        setattr(course, db_key, value)
                    elif hasattr(course, key):
                        setattr(course, key, value)
                await session.commit()
                await session.refresh(course)
            return course

    @staticmethod
    async def delete_course(course_id: int):
        async with get_db() as session:
            result = await session.execute(
                select(CourseRow).where(CourseRow.course_id == course_id)
            )
            course = result.scalar_one_or_none()
            if course:
                await session.delete(course)  # 物理删除
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
                created_at=now_local()
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
    async def get_practice_records(
        user_name: str = None, 
        course_id: int = None,
        start_time: str = None,
        end_time: str = None,
        status: str = None,
        page: int = 1,
        page_size: int = 20
    ):
        async with get_db() as session:
            # 使用 CourseRecordRow (pract_course_record) 作为主表
            query = (
                select(
                    CourseRecordRow,
                    CourseRow.course_name
                )
                .outerjoin(CourseRow, CourseRecordRow.course_id == CourseRow.course_id)
            )
            if user_name:
                query = query.where(CourseRecordRow.user_name == user_name)
            if course_id:
                query = query.where(CourseRecordRow.course_id == course_id)
            if start_time:
                query = query.where(CourseRecordRow.start_time >= start_time)
            if end_time:
                query = query.where(CourseRecordRow.start_time <= end_time)
            if status == "completed":
                query = query.where(CourseRecordRow.end_time.isnot(None))
            elif status == "in_progress":
                query = query.where(CourseRecordRow.end_time.is_(None))
            query = query.order_by(desc(CourseRecordRow.start_time))
            
            # 添加分页支持
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            result = await session.execute(query)
            
            records = []
            for row in result.all():
                record = row[0]
                record_dict = {
                    "record_id": record.id,
                    "course_id": record.course_id,
                    "user_name": record.user_name,
                    "total_score": record.total_score,
                    "start_time": record.start_time.isoformat() if record.start_time else None,
                    "end_time": record.end_time.isoformat() if record.end_time else None,
                    "course_name": str(row[1]).strip() if row[1] and str(row[1]).strip() else "未知课程",
                    "scene_name": str(record.scene_name).strip() if record.scene_name and str(record.scene_name).strip() else "未知场景",
                    "summary": record.summary,
                    "practice_mode": record.practice_mode,
                }
                records.append(record_dict)
            return records

    @staticmethod
    async def get_practice_record(record_id: int):
        """获取练习记录（从 pract_course_record 获取）"""
        async with get_db() as session:
            result = await session.execute(
                select(CourseRecordRow).where(CourseRecordRow.id == record_id)
            )
            return result.scalar_one_or_none()

    @staticmethod
    async def create_practice_record(data: dict):
        """创建练习记录（使用 CourseRecordRow）"""
        async with get_db() as session:
            record = CourseRecordRow(
                course_id=data["course_id"],
                user_name=data["user_name"],
                start_time=now_local(),
            )
            session.add(record)
            await session.commit()
            await session.refresh(record)
            return record

    @staticmethod
    async def complete_practice_record(record_id: int, data: dict):
        """完成练习记录（更新 CourseRecordRow）"""
        async with get_db() as session:
            result = await session.execute(
                select(CourseRecordRow).where(CourseRecordRow.id == record_id)
            )
            record = result.scalar_one_or_none()
            if record:
                record.end_time = now_local()
                if "total_score" in data:
                    record.total_score = data["total_score"]
                if "summary" in data:
                    record.summary = data["summary"]
                if "accord_finish" in data:
                    record.accord_finish = data["accord_finish"]
                await session.commit()
                await session.refresh(record)
            return record

class DialogDetailService:
    @staticmethod
    async def create_dialog(data: dict):
        """创建一条对话记录"""
        from deerflow.roleplay.models import DialogDetailRow
        async with get_db() as session:
            detail = DialogDetailRow(
                record_id=data["record_id"],
                speaker=data["speaker"],
                content_type=data.get("content_type", "1"),  # 内容类型 (1:文本, 2:音频URL)
                content=data["content"],  # 发言内容
                content_url=data.get("content_url"),  # 录音文件地址：AI时存TTS生成的，员工时存上传的
                intent_analysis=data.get("intent_analysis"),  # AI对这句话的意图分析结果 (JSON)
                score=data.get("score"),  # 该句得分（如果有考核点）
                feedback=data.get("feedback"),  # AI对该句的实时反馈或建议
                create_time=now_local(),
            )
            session.add(detail)
            await session.commit()
            await session.refresh(detail)
            return detail

    @staticmethod
    async def update_dialog_score(dialog_id: int, score: float, feedback: str):
        """更新对话记录的评分和反馈"""
        from deerflow.roleplay.models import DialogDetailRow
        async with get_db() as session:
            result = await session.execute(
                select(DialogDetailRow).where(DialogDetailRow.dialog_id == dialog_id)
            )
            detail = result.scalar_one_or_none()
            if detail:
                detail.score = score
                detail.feedback = feedback
                await session.commit()
            return detail

    @staticmethod
    async def get_dialogs_by_record(record_id: int) -> list:
        """获取某次对练的所有对话记录，按时间排序"""
        from deerflow.roleplay.models import DialogDetailRow
        async with get_db() as session:
            result = await session.execute(
                select(DialogDetailRow)
                .where(DialogDetailRow.record_id == record_id)
                .order_by(DialogDetailRow.create_time)
            )
            return result.scalars().all()

class StatisticsService:
    @staticmethod
    async def get_user_stats(user_name: str):
        sf = get_session_factory()
        async with sf() as session:
            record_result = await session.execute(
                select(
                    func.count(CourseRecordRow.id).label("practice_count"),
                    func.sum(
                        func.unix_timestamp(CourseRecordRow.end_time) - func.unix_timestamp(CourseRecordRow.start_time)
                    ).label("total_duration"),
                    func.avg(CourseRecordRow.total_score).label("avg_score")
                ).where(CourseRecordRow.user_name == user_name)
            )
            basic_stats = record_result.first()
            
            dates_result = await session.execute(
                select(
                    func.date(CourseRecordRow.start_time).label("practice_date")
                ).where(CourseRecordRow.user_name == user_name)
                .distinct()
                .order_by(func.date(CourseRecordRow.start_time).desc())
            )
            practice_dates = [row for row in dates_result.scalars().all()]
            
            continuous_days = 0
            if practice_dates:
                today = datetime.now().date()
                last_practice_date = practice_dates[0]
                if last_practice_date == today or last_practice_date == today - timedelta(days=1):
                    continuous_days = 1
                    for i in range(1, len(practice_dates)):
                        expected_date = practice_dates[i-1] - timedelta(days=1)
                        if practice_dates[i] == expected_date:
                            continuous_days += 1
                        else:
                            break
            
            return {
                "practice_count": basic_stats.practice_count if basic_stats else 0,
                "total_duration": basic_stats.total_duration if basic_stats else 0,
                "avg_score": basic_stats.avg_score if basic_stats else 0,
                "continuous_days": continuous_days
            }

    @staticmethod
    async def get_scene_stats(course_id: int = None):
        sf = get_session_factory()
        async with sf() as session:
            query = select(
                PracticeRecordRow.course_id,
                func.count(PracticeRecordRow.record_id).label("practice_count"),
                func.avg(PracticeRecordRow.total_score).label("avg_score")
            ).group_by(PracticeRecordRow.course_id)
            if course_id:
                query = query.where(PracticeRecordRow.course_id == course_id)
            result = await session.execute(query)
            return result.all()

    @staticmethod
    async def get_leaderboard(limit: int = 10):
        sf = get_session_factory()
        async with sf() as session:
            query = select(
                PracticeRecordRow.user_name,
                func.count(PracticeRecordRow.record_id).label("practice_count"),
                func.avg(PracticeRecordRow.total_score).label("avg_score")
            ).group_by(PracticeRecordRow.user_name)\
             .order_by(desc(func.avg(PracticeRecordRow.total_score)))\
             .limit(limit)
            result = await session.execute(query)
            return result.all()