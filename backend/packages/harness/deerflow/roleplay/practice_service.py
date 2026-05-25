"""自由式对练核心引擎

实现 LLM 驱动的自由式对练，每轮经过：
1. 保存学员话术
2. LLM 评估打分（多维度）
3. LLM 生成客户角色下一条回复
"""

import json
import re
import random
from datetime import UTC, datetime

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from deerflow.models import create_chat_model
from deerflow.roleplay import get_db
from deerflow.roleplay.models import SceneRow, CourseRow, PracticeRecordRow, DialogDetailRow, CourseRecordRow
from deerflow.roleplay.services import SceneService, CourseService, PracticeRecordService, DialogDetailService


# ── LLM 调用工具函数 ─────────────────────────────────────────

def _parse_json_from_text(text: str) -> dict:
    """从 LLM 返回文本中提取 JSON，兼容 markdown 代码块包裹的情况"""
    text = text.strip()
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


async def _llm_invoke_json(system_prompt: str, user_prompt: str, model_name: str | None = None) -> dict:
    """通用 LLM 调用，返回解析后的 JSON dict"""
    llm = _create_llm(model_name)
    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    raw = response.content
    if isinstance(raw, list):
        raw = " ".join(str(c) for c in raw)
    return _parse_json_from_text(raw)


async def _llm_invoke_text(system_prompt: str, user_prompt: str, model_name: str | None = None) -> str:
    """通用 LLM 调用，返回纯文本"""
    llm = _create_llm(model_name)
    response = await llm.ainvoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])
    raw = response.content
    if isinstance(raw, list):
        raw = " ".join(str(c) for c in raw)
    return raw.strip()


def _create_llm(model_name: str | None = None):
    """创建 LLM 实例，优先使用指定模型，否则系统默认"""
    try:
        return create_chat_model(name=model_name, thinking_enabled=False)
    except ValueError:
        import logging
        logging.getLogger("roleplay").warning(
            f"场景指定模型 '{model_name}' 不在 config 中，已自动切换为默认模型"
        )
        return create_chat_model(name=None, thinking_enabled=False)


# ── Prompt 模板 ──────────────────────────────────────────────

CUSTOMER_SYSTEM_PROMPT = """系统角色：你正在模拟一位真实客户，正在进行一场对话练习。

【场景背景】
{scene_description}

【场景知识】
{summary_text}

【你的人物设定】
- 说话自然、口语化，避免 AI 味
- 先回应对方上一条回答（简要总结或表达理解），再自然过渡到下一个问题
- 可以表现出犹豫、追问、表达疑虑或感兴趣
- 根据对方的回复自然地推进对话，保持对话连贯性
- 不要主动结束对话
- 你的回复要简短，2-4句话即可
- **关键要求**：提出**开放性问题**，鼓励学员详细阐述，不要问只能用"是"或"否"回答的问题

【当前对话轮次】：第 {round} / {total_rounds} 轮

【本轮考察重点】：{current_category}
- **硬性要求**：你的问题和对话内容**必须100%与此维度相关**，不允许谈论任何无关话题
- 你是来深入了解此维度的潜在客户，不是闲聊
- 提出与此维度直接相关的**具体、深入**的问题或疑虑
- 引导学员详细讲解、解释或推销此维度的特点、优势和价值
- 可以提出质疑、追问细节，促使学员充分展示专业知识
- 如果学员偏离话题，礼貌地将话题拉回到此维度上

例如，如果本轮考察"三电系统"，你可以问：
- "你能详细介绍一下这款车的电池技术吗？续航表现如何？"
- "充电速度怎么样？支持哪些充电方式？"
- "电机的动力性能如何？加速表现怎么样？"

例如，回应学员回答后再提问：
- 学员说："我们的车续航里程很长。"
- 你可以回答："续航长确实是个重要优势，能具体说说在不同路况下的实际表现吗？"

请根据以上设定，生成你对学员上一句话的回复。先简要回应，再提出相关问题。只输出回复内容，不要加任何前缀或说明。"""


EVALUATION_SYSTEM_PROMPT = """系统角色：你是一位专业的对练教练，负责评估学员的对话表现。

【考核维度】（本次练习的全部考核维度）
{exam_categories}

【评分规则】（通用评分标准）
{scoring_rules}

【本轮考察重点】（当前轮次需要重点考察的维度）
{current_category}

【对话历史】（已完成的对话，含历史评分）
{dialog_history}

【学员刚才的发言】
{user_message}

请根据当前对话内容，对学员刚才的发言进行多维度评估。注意：
- 重点评估【本轮考察重点】中指定的维度
- 对每个考核维度独立打分（0-100 分），重点维度必须打分，其他维度如未涉及可不打分
- round_score 主要基于本轮重点考察维度的得分
- 按以下 JSON 格式输出（仅输出 JSON，不要其他内容）：

{{
  "round_score": 85,
  "dimension_scores": {{"产品知识": 80, "沟通技巧": 90}},
  "feedback": "你的回复很好，抓住了客户的疑问点并给出了专业解释。建议下一步可以更主动地引导客户需求。"
}}"""


REPORT_SYSTEM_PROMPT = """系统角色：你是一位专业的对练教练，请基于整场对话和每轮评分记录，生成最终评估报告。

【考核维度】（本次练习的全部考核维度）
{exam_categories}

【评分规则】（通用评分标准）
{scoring_rules}

【完整对话历史】（含每轮学员发言、AI 回复、每轮评分）
{full_dialog_with_scores}

请综合以上信息，生成完整的评估报告。要求：
- total_score 取所有维度分的平均值
- dimension_scores 列出每个考核维度的最终得分
- strengths 列出学员的突出优点
- improvements 列出需要改进的方向
- summary 给出整体评价

按以下 JSON 格式输出（仅输出 JSON）：

{{
  "total_score": 82,
  "dimension_scores": {{"产品知识": 80, "沟通技巧": 85, "问题解决": 80}},
  "strengths": ["产品知识扎实", "善于倾听客户需求"],
  "improvements": ["需要加强异议处理技巧", "建议使用更多数据说服客户"],
  "summary": "整体表现良好，产品知识扎实..."
}}"""


# ── 辅助函数 ─────────────────────────────────────────────────

def _build_dialog_history(dialogs: list) -> str:
    """将对话记录列表转为可读的历史文本"""
    lines = []
    round_num = 0
    for d in dialogs:
        # 学员回复开始新的一轮（AI开场白不算轮次）
        if d.speaker == 1:
            round_num += 1
        role = "学员" if d.speaker == 1 else "客户"
        suffix = ""
        if d.score is not None:
            suffix += f" [得分: {d.score}]"
        if d.feedback:
            suffix += f" [反馈: {d.feedback}]"
        lines.append(f"[第{round_num}轮] {role}: {d.content}{suffix}")
    return "\n".join(lines)


def _get_current_category(scene: SceneRow, round_num: int, seed: int = 0) -> str:
    """根据轮次获取当前需要考察的考核维度（使用 seed 保证同一次对练维度顺序一致）"""
    if not scene.exam_categories:
        return ""
    
    # 解析考核维度（支持中英文逗号）
    categories = scene.exam_categories.replace("，", ",").split(",")
    categories = [cat.strip() for cat in categories if cat.strip()]
    
    if not categories:
        return ""
    
    # 使用 seed 进行确定性随机打乱（保证同一次对练维度顺序一致）
    if seed != 0 and len(categories) > 1:
        rng = random.Random(seed)
        categories = categories.copy()
        rng.shuffle(categories)
    
    # 根据轮次返回对应的维度（轮次从1开始）
    index = round_num - 1
    if index < len(categories):
        return categories[index]
    
    # 如果轮次超过维度数量，返回最后一个维度
    return categories[-1]


async def _generate_customer_reply(
    scene: SceneRow, dialog_history: list, round_num: int, total_rounds: int, current_category: str = ""
) -> str:
    """调用 LLM 生成客户角色回复"""
    history_text = _build_dialog_history(dialog_history)
    user_prompt = f"【当前对话历史】\n{history_text}\n\n请生成你的下一条回复（1-3句话）。"

    system_prompt = CUSTOMER_SYSTEM_PROMPT.format(
        scene_description=scene.scene_description or "",
        summary_text=scene.summary_text or scene.knowledge_base or "",
        round=round_num,
        total_rounds=total_rounds,
        current_category=current_category or "综合能力",
    )
    return await _llm_invoke_text(system_prompt, user_prompt, scene.model_name)


async def _evaluate_user_message(
    scene: SceneRow, dialog_history: list, user_message: str, current_category: str = ""
) -> dict:
    """调用 LLM 评估学员发言"""
    history_text = _build_dialog_history(dialog_history) if dialog_history else "（对话刚开始，暂无历史）"

    system_prompt = EVALUATION_SYSTEM_PROMPT.format(
        exam_categories=scene.exam_categories or "沟通能力,专业素养",
        scoring_rules=scene.scoring_rules or "根据学员回复的准确性、完整性和说服力进行评分",
        dialog_history=history_text,
        user_message=user_message,
        current_category=current_category,
    )
    return await _llm_invoke_json(system_prompt, "请评估。", scene.model_name)


async def _generate_report(scene: SceneRow, dialogs: list) -> dict:
    """调用 LLM 生成最终评估报告"""
    dialog_text = _build_dialog_history(dialogs)

    system_prompt = REPORT_SYSTEM_PROMPT.format(
        exam_categories=scene.exam_categories or "沟通能力,专业素养",
        scoring_rules=scene.scoring_rules or "根据学员综合表现进行评分",
        full_dialog_with_scores=dialog_text,
    )
    return await _llm_invoke_json(system_prompt, "请生成最终报告。", scene.model_name)


def _calc_total_score(report: dict) -> float:
    """从报告的 dimension_scores 计算总分"""
    dims = report.get("dimension_scores", {})
    if not dims:
        return 0.0
    return round(sum(dims.values()) / len(dims), 2)


async def _load_scene_by_course(course_id: int) -> tuple[CourseRow, SceneRow]:
    """根据课程 ID 加载课程和关联场景"""
    course = await CourseService.get_course(course_id)
    if not course:
        raise ValueError(f"课程 {course_id} 不存在")
    if not course.scene_id:
        raise ValueError(f"课程 {course_id} 未关联场景")

    scene = await SceneService.get_scene(course.scene_id)
    if not scene:
        raise ValueError(f"场景 {course.scene_id} 不存在")
    return course, scene


async def _load_scene_by_record(record_id: int) -> tuple[CourseRecordRow, CourseRow, SceneRow]:
    """根据记录 ID 加载记录、课程和场景（从 pract_course_record 加载）"""
    from sqlalchemy import select as sa_select

    async with get_db() as session:
        result = await session.execute(
            sa_select(CourseRecordRow).where(CourseRecordRow.id == record_id)
        )
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError(f"练习记录 {record_id} 不存在")
        
        # 检查对练是否已结束
        if record.end_time is not None:
            raise ValueError("本次对练已结束，无法继续")

    course, scene = await _load_scene_by_course(record.course_id)
    return record, course, scene


# ── PracticeService ───────────────────────────────────────────

class PracticeService:
    """自由式对练核心引擎"""

    @staticmethod
    async def start(course_id: int, user_name: str) -> dict:
        """
        开始对练：
        1. 加载课程和关联场景配置
        2. 创建 pract_course_record（DB 自增 record_id）
        3. LLM 生成开场白（使用 record_id 作为随机种子打乱维度顺序）
        4. 开场白写入 pract_dialog_detail（speaker=2, round=1）
        5. 返回 record_id + 开场白内容
        """
        # 1. 加载课程和场景
        course, scene = await _load_scene_by_course(course_id)
        
        # 总轮次计算逻辑：
        # - 自由式对练（practice_mode="text"）：取exam_categories字段中逗号分隔的类别数量
        # - 其他模式：使用dialog_round_limit配置，默认5轮
        if scene.practice_mode == "text" and scene.exam_categories:
            # 同时支持中文逗号和英文逗号分割
            categories = scene.exam_categories.replace("，", ",").split(",")
            total_rounds = len([cat.strip() for cat in categories if cat.strip()])
            if total_rounds == 0:
                total_rounds = 5
        else:
            total_rounds = scene.dialog_round_limit or 5

        # 2. 创建 pract_course_record 记录（在对练开始时创建）
        async with get_db() as session:
            course_record = CourseRecordRow(
                course_id=course_id,
                scene_id=scene.scene_id,
                start_time=datetime.now(UTC),
                user_name=user_name,
                scene_name=scene.scene_name,
                course_type=course.course_type,
                practice_mode=course.practice_mode,
            )
            session.add(course_record)
            await session.commit()
            await session.refresh(course_record)
            
            record_id = course_record.id  # 使用 course_record 的 id 作为 record_id

        # 3. LLM 生成开场白（第1轮对应第一个随机后的考核维度，使用 record_id 作为种子）
        first_category = _get_current_category(scene, 1, record_id)
        opening_message = await _generate_customer_reply(scene, [], 1, total_rounds, first_category)

        # 4. 写入 dialog_detail
        await DialogDetailService.create_dialog({
            "record_id": record_id,
            "speaker": 2,  # AI/客户
            "content": opening_message,
        })

        return {
            "recordId": record_id,
            "courseName": course.course_name,
            "sceneName": scene.scene_name,
            "sceneDescription": scene.scene_description,
            "totalRounds": total_rounds,
            "customerMessage": opening_message,
            "round": 1,
        }

    @staticmethod
    async def turn(cls, record_id: int, user_message: str) -> dict:
        """
        对练对话轮次处理流程：
        1. 加载记录、课程、场景
        2. 写入学员话术（speaker=1）
        3. 获取当前对话历史
        4. LLM 评估打分
        5. 写入 dialog_detail.score / .feedback
        6. 判断是否完成（dialog_rounds >= 场景设定的总轮数）
           ├─ 是 → 进入结束流程，生成最终报告
           └─ 否 → LLM 生成下一轮客户回复
        7. 客户回复写入 dialog_detail（speaker=2, 新 round）
        8. 更新 dialog_rounds
        9. 返回：customer_message, evaluation, is_complete, round
        """
        # 验证用户消息
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("消息内容不能为空")
        
        # 检查是否是无效消息（全是问号或特殊字符）
        if re.match(r'^[?？,，\s]+$', user_message):
            raise ValueError("无效的消息内容")
        
        # 1. 加载记录、课程、场景
        record, course, scene = await _load_scene_by_record(record_id)

        # 总轮次计算逻辑：
        # - 自由式对练（practice_mode="text"）：取exam_categories字段中逗号分隔的类别数量
        # - 其他模式：使用dialog_round_limit配置，默认5轮
        if scene.practice_mode == "text" and scene.exam_categories:
            # 同时支持中文逗号和英文逗号分割
            categories = scene.exam_categories.replace("，", ",").split(",")
            total_rounds = len([cat.strip() for cat in categories if cat.strip()])
            if total_rounds == 0:
                total_rounds = 5
        else:
            total_rounds = scene.dialog_round_limit or 5
        
        # 获取当前对话历史，动态计算当前轮次
        all_dialogs = await DialogDetailService.get_dialogs_by_record(record_id)
        # 计算当前轮次：AI开场白不算轮次，统计学员回复的数量即为当前轮次
        current_round = 0
        for d in all_dialogs:
            if d.speaker == 1 and d.content:  # 学员回复
                current_round += 1

        # 2. 写入学员话术
        await DialogDetailService.create_dialog({
            "record_id": record_id,
            "speaker": 1,  # 学员
            "content": user_message,
        })
        
        # 学员回复后，当前轮次 + 1（这才是真正的当前轮次）
        current_round += 1

        # 3. 获取最新对话历史（用于评估上下文）
        all_dialogs = await DialogDetailService.get_dialogs_by_record(record_id)

        # 4. LLM 评估打分（聚焦当前轮次的考核维度，使用 record_id 作为随机种子）
        current_category = _get_current_category(scene, current_round, record_id)
        evaluation = await _evaluate_user_message(scene, all_dialogs, user_message, current_category)

        # 5. 写入评分到最新一条学员话术
        # 按时间倒序查找最新的学员对话
        user_dialog = None
        for d in reversed(all_dialogs):
            if d.speaker == 1:
                user_dialog = d
                break
        if user_dialog:
            await DialogDetailService.update_dialog_score(
                user_dialog.dialog_id,
                evaluation.get("round_score", 0),
                evaluation.get("feedback", ""),
            )

        # 6. 判断是否完成
        is_complete = current_round >= total_rounds

        if is_complete:
            # 自动结束：生成最终报告
            report = await _generate_report(scene, all_dialogs)
            total_score = _calc_total_score(report)
            end_time = datetime.now(UTC)

            async with get_db() as session:
                from sqlalchemy import update as sa_update
                
                # 创建 pract_record（在对练结束时创建）
                practice_record = PracticeRecordRow(
                    course_id=record.course_id,
                    user_name=record.user_name,
                    start_time=record.start_time,
                    dialog_rounds=current_round,
                    total_score=total_score,
                    report_data=report,
                    end_time=end_time,
                )
                session.add(practice_record)
                
                # 更新 pract_course_record
                await session.execute(
                    sa_update(CourseRecordRow)
                    .where(CourseRecordRow.id == record_id)
                    .values(
                        total_score=total_score,
                        end_time=end_time,
                        summary=report.get("summary", "")[:65535] if report else "",
                        accord_finish=1 if total_score >= (course.passing_score or 60) else 0,
                    )
                )
                
                await session.commit()

            return {
                "recordId": record_id,
                "round": current_round,
                "evaluation": {
                    "roundScore": evaluation.get("round_score", 0),
                    "dimensionScores": evaluation.get("dimension_scores", {}),
                    "feedback": evaluation.get("feedback", ""),
                },
                "customerMessage": "",
                "isComplete": True,
                "report": report,
            }

        # 7. 生成下一轮客户回复（对应下一个考核维度，使用 record_id 作为随机种子）
        next_round = current_round + 1
        next_category = _get_current_category(scene, next_round, record_id)
        customer_message = await _generate_customer_reply(scene, all_dialogs, next_round, total_rounds, next_category)

        await DialogDetailService.create_dialog({
            "record_id": record_id,
            "speaker": 2,
            "content": customer_message,
        })

        # 8. 更新 pract_course_record 的 last_time
        async with get_db() as session:
            from sqlalchemy import update as sa_update
            await session.execute(
                sa_update(CourseRecordRow)
                .where(CourseRecordRow.id == record_id)
                .values(last_time=datetime.now(UTC))
            )
            await session.commit()

        return {
            "recordId": record_id,
            "round": current_round,
            "evaluation": {
                "roundScore": evaluation.get("round_score", 0),
                "dimensionScores": evaluation.get("dimension_scores", {}),
                "feedback": evaluation.get("feedback", ""),
            },
            "customerMessage": customer_message,
            "isComplete": False,
        }

    @staticmethod
    async def end(record_id: int) -> dict:
        """
        手动结束对练：
        1. 查询 record 和对话历史
        2. LLM 生成最终评估报告
        3. 创建 pract_record（total_score, report_data, end_time）
        4. 更新 pract_course_record
        5. 返回完整报告
        """
        record, course, scene = await _load_scene_by_record(record_id)

        # 如果已结束，直接返回
        if record.end_time is not None:
            return {
                "recordId": record_id,
                "totalRounds": record.total_score or 0,
                "report": record.summary or "",
                "message": "本次对练已结束",
            }

        all_dialogs = await DialogDetailService.get_dialogs_by_record(record_id)
        
        # 计算当前轮次：统计学员回复数量
        current_round = 0
        for d in all_dialogs:
            if d.speaker == 1 and d.content:  # 学员回复
                current_round += 1

        # LLM 生成最终报告
        report = await _generate_report(scene, all_dialogs)
        total_score = _calc_total_score(report)
        end_time = datetime.now(UTC)

        async with get_db() as session:
            from sqlalchemy import update as sa_update
            
            # 创建 pract_record（在对练结束时创建）
            practice_record = PracticeRecordRow(
                course_id=record.course_id,
                user_name=record.user_name,
                start_time=record.start_time,
                dialog_rounds=current_round,
                total_score=total_score,
                report_data=report,
                end_time=end_time,
            )
            session.add(practice_record)
            
            # 更新 pract_course_record
            await session.execute(
                sa_update(CourseRecordRow)
                .where(CourseRecordRow.id == record_id)
                .values(
                    total_score=total_score,
                    end_time=end_time,
                    summary=report.get("summary", "")[:65535] if report else "",
                    accord_finish=1 if total_score >= (course.passing_score or 60) else 0,
                )
            )
            
            await session.commit()

        return {
            "recordId": record_id,
            "totalRounds": current_round,
            "report": report,
            "message": "本次对练已结束，稍后查看整个结果",
        }

    @staticmethod
    async def get_practice_history(record_id: int) -> list[dict]:
        """获取某次对练的完整对话历史（含评分）"""
        dialogs = await DialogDetailService.get_dialogs_by_record(record_id)
        result = []
        round_num = 1
        for i, d in enumerate(dialogs):
            # 动态计算轮次：AI开场白后，每两条对话（学员+AI）为一轮
            if i > 0 and d.speaker == 2:
                round_num += 1
            result.append({
                "dialog_id": d.dialog_id,
                "record_id": d.record_id,
                "speaker": d.speaker,
                "content_type": d.content_type,
                "content": d.content,
                "round_number": round_num,
                "score": d.score,
                "feedback": d.feedback,
                "create_time": d.create_time.isoformat() if d.create_time else None,
            })
        return result

    @staticmethod
    async def get_report(record_id: int) -> dict:
        """获取最终评估报告"""
        from sqlalchemy import select as sa_select

        async with get_db() as session:
            result = await session.execute(
                sa_select(PracticeRecordRow).where(PracticeRecordRow.record_id == record_id)
            )
            record = result.scalar_one_or_none()
            if not record:
                raise ValueError(f"练习记录 {record_id} 不存在")
            return {
                "record_id": record.record_id,
                "total_score": record.total_score,
                "dialog_rounds": record.dialog_rounds,
                "report": record.report_data or {},
            }
