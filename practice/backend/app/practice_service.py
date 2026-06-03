"""自由式对练核心引擎 — 从 deerflow/roleplay/practice_service.py 迁移

实现 LLM 驱动的自由式对练，每轮经过：
1. 保存学员话术
2. LLM 评估打分（多维度）
3. LLM 生成客户角色下一条回复
"""

import json
import re
import random
import logging
import time
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm_factory import create_chat_model
from app.database import get_db
from app.models import SceneRow, CourseRow, DialogDetailRow, CourseRecordRow
from app.services import SceneService, CourseService, DialogDetailService
from app.timezone_utils import now_local

logger = logging.getLogger(__name__)


# ── LLM 调用工具函数 ─────────────────────────────────────────────


def _parse_json_from_text(text: str) -> dict:
    """从 LLM 返回文本中提取 JSON，兼容 markdown 代码块包裹的情况"""
    text = text.strip()
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return text


_REPAIR_STRATEGY_SUCCESS_RATES = {
    "py_fix": 0.75,
    "llm_fix": 0.85,
    "llm_regen": 0.9,
}

_ERROR_TYPE_STRATEGIES = {
    "missing_quote": ["py_fix", "llm_fix", "llm_regen"],
    "missing_comma": ["py_fix", "llm_fix", "llm_regen"],
    "missing_bracket": ["py_fix", "llm_fix", "llm_regen"],
    "format_mess": ["llm_fix", "llm_regen", "py_fix"],
    "content_empty": ["llm_regen", "llm_fix", "py_fix"],
    "unknown": ["llm_fix", "llm_regen", "py_fix"],
}


def _classify_json_error(error_msg: str) -> str:
    """识别 JSON 解析错误类型"""
    error_msg_lower = error_msg.lower()

    if "property name" in error_msg_lower or ("expecting" in error_msg_lower and "double quote" in error_msg_lower):
        return "missing_quote"
    if "expecting ','" in error_msg_lower or "expecting ',' delimiter" in error_msg_lower:
        return "missing_comma"
    if "unexpected end of json" in error_msg_lower:
        return "missing_bracket"
    if "invalid" in error_msg_lower or "multiple" in error_msg_lower:
        return "format_mess"
    if "null" in error_msg_lower or "empty" in error_msg_lower:
        return "content_empty"
    return "unknown"


def _get_optimized_strategy_order(error_type: str) -> list:
    """根据错误类型和成功率获取优化后的策略执行顺序"""
    base_strategies = _ERROR_TYPE_STRATEGIES.get(error_type, ["llm_fix", "llm_regen", "py_fix"])
    scored_strategies = []
    for strategy in base_strategies:
        scored_strategies.append((strategy, _REPAIR_STRATEGY_SUCCESS_RATES.get(strategy, 0.5)))
    scored_strategies.sort(key=lambda x: -x[1])
    return [s[0] for s in scored_strategies]


async def _parse_json_with_retry(text: str, model_name: str | None = None, max_rounds: int = 3) -> dict:
    """带智能重试机制的 JSON 解析"""
    cleaned_text = _parse_json_from_text(text)
    error_type = "unknown"

    try:
        result = json.loads(cleaned_text)
        if isinstance(result, dict):
            logger.debug("【JSON解析成功】基础解析一次性成功")
            return result
    except json.JSONDecodeError as e:
        error_type = _classify_json_error(str(e))
        logger.warning(f"【JSON解析失败】基础解析失败，错误类型: {error_type}, 错误消息: {e}")

    strategy_order = _get_optimized_strategy_order(error_type)
    logger.info(f"【JSON修复】错误类型: {error_type}, 优化策略顺序: {strategy_order}")

    for round_num in range(1, max_rounds + 1):
        logger.info(f"【JSON修复】开始第{round_num}/{max_rounds}轮重试")

        for strategy in strategy_order:
            step_name = {"py_fix": "Python代码修复", "llm_fix": "LLM格式修复", "llm_regen": "LLM重新生成"}[strategy]
            logger.info(f"【JSON修复】第{round_num}轮-{step_name}")

            try:
                if strategy == "py_fix":
                    fixed_json = _fix_json_with_code(cleaned_text)
                elif strategy == "llm_fix":
                    fixed_json = await _fix_json_format(cleaned_text, model_name)
                elif strategy == "llm_regen":
                    fixed_json = await _regenerate_json(text, model_name)
                    if fixed_json:
                        fixed_json = _parse_json_from_text(fixed_json)
                else:
                    continue

                if fixed_json:
                    result = json.loads(fixed_json)
                    if isinstance(result, dict):
                        logger.info(f"【JSON修复成功】第{round_num}轮-{step_name}成功")
                        return result
            except Exception as e:
                logger.warning(f"【JSON修复失败】第{round_num}轮-{step_name}失败: {e}")

    logger.error(f"【JSON解析完全失败】经过{max_rounds}轮重试后仍无法解析")
    logger.error(f"原始文本: {text[:500]}...")
    return {
        "dimension_scores": {},
        "summary": "程序出错了，请稍后再试。",
        "strengths": [],
        "improvements": [],
    }


async def _fix_json_format(malformed_json: str, model_name: str | None = None) -> str | None:
    """调用 LLM 修复格式错误的 JSON"""
    system_prompt = """
你是一个 JSON 格式修复专家。请修复以下 JSON 文本中的格式错误：

要求：
1. 保持原始数据内容不变
2. 修复语法错误（如缺失逗号、引号不匹配等）
3. 返回纯 JSON 字符串，不要包含其他内容
4. 如果无法修复，返回空字符串
"""
    user_prompt = f"请修复以下 JSON 的格式错误：\n{malformed_json}"

    try:
        response = await _llm_invoke_text(system_prompt, user_prompt, model_name)
        cleaned = _parse_json_from_text(response)
        json.loads(cleaned)
        return cleaned
    except Exception as e:
        logger.error(f"LLM格式修复失败: {e}")
        return None


async def _regenerate_json(original_text: str, model_name: str | None = None) -> str | None:
    """调用 LLM 重新生成完整的 JSON"""
    system_prompt = """
你是一个专业的数据分析师。根据以下对话内容，重新生成一份格式正确的评估报告 JSON：

要求：
1. 输出必须是纯 JSON 格式，不要包含 markdown 代码块
2. JSON 必须包含以下字段：
   - dimension_scores: 对象，包含各个考核维度的分数
   - summary: 字符串，总结评价内容
   - strengths: 数组，列出优点
   - improvements: 数组，列出改进建议
3. 如果没有足够信息，使用合理的默认值
"""
    user_prompt = f"根据以下对话内容，生成评估报告 JSON：\n{original_text}"

    try:
        response = await _llm_invoke_text(system_prompt, user_prompt, model_name)
        cleaned = _parse_json_from_text(response)
        json.loads(cleaned)
        return cleaned
    except Exception as e:
        logger.error(f"LLM重新生成失败: {e}")
        return None


def _fix_json_with_code(malformed_json: str) -> str | None:
    """使用 Python 代码修复常见的 JSON 格式错误"""
    try:
        fixed = malformed_json

        # 修复未加引号的键名
        fixed = re.sub(r'{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'{"\1":', fixed)
        fixed = re.sub(r',\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r',"\1":', fixed)

        # 修复末尾缺少闭合括号
        if fixed.count('{') > fixed.count('}'):
            fixed += '}' * (fixed.count('{') - fixed.count('}'))
        if fixed.count('[') > fixed.count(']'):
            fixed += ']' * (fixed.count('[') - fixed.count(']'))

        # 修复字符串末尾缺少引号
        lines = fixed.split('\n')
        fixed_lines = []
        for line in lines:
            if line.count('"') % 2 != 0:
                fixed_lines.append(line.rstrip() + '"')
            else:
                fixed_lines.append(line)
        fixed = '\n'.join(fixed_lines)

        result = json.loads(fixed)
        if isinstance(result, dict):
            return json.dumps(result)
        return None
    except Exception as e:
        logger.error(f"Python代码修复失败: {e}")
        return None


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
    return await _parse_json_with_retry(raw, model_name, max_rounds=3)


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
        logging.getLogger("roleplay").warning(
            f"场景指定模型 '{model_name}' 不在 config 中，已自动切换为默认模型"
        )
        return create_chat_model(name=None, thinking_enabled=False)


# ── Prompt 模板 ──────────────────────────────────────────────────

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

请根据以上设定，生成你对学员上一句话的回复。先简要回应，再提出相关问题。只输出回复内容，不要加任何前缀或说明。"""

OPENING_PROMPT = """系统角色：你正在模拟一位真实客户，正在进行一场对话练习。

【场景背景】
{scene_description}

【场景知识】
{summary_text}

【你的人物设定】
- 这是对话的开始，你需要先做自我介绍，然后提出问题
- 说话自然、口语化，避免 AI 味
- 自我介绍要简短亲切，说明你的身份（如：我是来买车的客户、我是面试者等）
- 自我介绍后，自然过渡到第一个问题
- 你的回复要简短，2-4句话即可
- **关键要求**：提出**开放性问题**，鼓励学员详细阐述

【本轮考察重点】：{current_category}
- 你的问题必须与此维度相关
- 提出与此维度直接相关的具体问题或疑虑

请根据以上设定，生成开场白。先做简短自我介绍，再提出第一个问题。只输出开场白内容，不要加任何前缀或说明。"""

DETAIL_SUGGESTION_PROMPT = """系统角色：你是一位专业的对练教练，负责为学员提供详细的改进建议。

【场景背景】
{scene_description}

【场景知识】
{summary_text}

【本轮考察重点】：{current_category}

【对话历史】
{dialog_history}

【学员最新回复】
{user_message}

【任务要求】
请针对学员的最新回复，生成详细的评价建议，包括：

1. **改进建议列表**：列出3-5条具体、可操作的改进建议
   - 每条建议要具体，指出学员哪里做得不够好
   - 提供具体的改进方向
   - 使用简洁明了的语言

2. **润色表达**：重新组织学员的回复，使其更加专业、流畅、有说服力
   - 保持原意不变
   - 使用更恰当的词汇和表达方式
   - 增加必要的细节和数据支持

【输出格式】
请按以下 JSON 格式输出，不要包含任何额外内容：
{{
  "suggestions": ["改进建议1", "改进建议2", "改进建议3"],
  "polishedExpression": "润色后的完整表达"
}}"""


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
1. total_score 取所有维度分的平均值
2. dimension_scores 列出每个考核维度的最终得分（满分100）
3. dimension_feedbacks 对每个考核维度给出详细评估：
   - 如果该维度表现优秀，描述做得好的具体方面
   - 如果该维度需要改进，给出具体的改进建议
   - 评估要中肯客观，既肯定优点也指出不足
   - 描述时避免使用具体的轮次数字（如"第X轮"、"X轮对话"），使用"对话中"、"整个对话过程"等中性描述
4. strengths 列出学员的突出优点（从各维度中提炼）
5. improvements 列出需要改进的方向（从各维度中提炼）
6. summary 给出整体评价，总结表现并提出鼓励

按以下 JSON 格式输出（仅输出 JSON）：

{{
  "total_score": 82,
  "dimension_scores": {{"产品知识": 80, "沟通技巧": 85, "问题解决": 80}},
  "dimension_feedbacks": {{
    "产品知识": "表现优秀：对产品功能和特点非常熟悉，能够准确回答客户关于产品配置的问题。建议：可以进一步了解竞品信息，以便更好地突出产品优势。",
    "沟通技巧": "表现良好：能够倾听客户需求并给予回应。建议：可以增加更多开放性问题，引导客户深入表达需求。",
    "问题解决": "表现一般：在处理客户异议时思路不够清晰。建议：可以学习结构化的问题解决方法。"
  }},
  "strengths": ["产品知识扎实", "善于倾听客户需求", "表达清晰"],
  "improvements": ["需要加强异议处理技巧", "建议使用更多数据说服客户"],
  "summary": "整体表现良好，产品知识扎实，沟通能力较强。建议在异议处理方面多加练习，相信会有更大的进步！"
}}"""


INSPIRATION_PROMPT = """
你是一个专业的对话灵感助手，帮助学员在模拟对练中获得知识点提示。

## 当前考核维度
{current_category}

## 当前场景
{scene_description}

## 知识库
{knowledge_base}

## 对话历史
{dialog_history}

## 任务
请针对当前考核维度，生成2-3条简短的知识点提示，帮助学员更好地回应客户。

## 要求
1. 必须针对当前考核维度生成，不偏离主题
2. 每条提示不超过100字，语言简洁
3. 语言自然友好，像朋友在旁边给的小提示
4. 提供思路和要点，不直接给出答案
5. 保持积极鼓励的语气

请以JSON格式输出，格式如下：
{{
  "tips": [
    {{"category": "简短标题", "content": "简洁提示，不超过100字"}},
    {{"category": "简短标题", "content": "简洁提示，不超过100字"}}
  ]
}}
"""


# ── 辅助函数 ─────────────────────────────────────────────────────


def _build_dialog_history(dialogs: list) -> str:
    """将对话记录列表转为可读的历史文本"""
    lines = []
    ai_reply_count = 0
    round_num = 0
    for d in dialogs:
        role = "学员" if d.speaker == 1 else "客户"

        if d.speaker == 2 and d.content:
            ai_reply_count += 1
            round_num = ai_reply_count

        suffix = ""
        if d.score is not None:
            suffix += f" [得分: {d.score}]"
        if d.feedback:
            suffix += f" [反馈: {d.feedback}]"
        lines.append(f"[第{round_num}轮] {role}: {d.content}{suffix}")
    return "\n".join(lines)


def _get_current_category(scene: SceneRow, round_num: int, seed: int = 0) -> str:
    """根据轮次获取当前需要考察的考核维度"""
    if not scene.exam_categories:
        return ""

    categories = scene.exam_categories.replace("，", ",").split(",")
    categories = [cat.strip() for cat in categories if cat.strip()]

    if not categories:
        return ""

    if seed != 0 and len(categories) > 1:
        rng = random.Random(seed)
        categories = categories.copy()
        rng.shuffle(categories)

    index = round_num - 1
    if index < len(categories):
        return categories[index]
    return categories[-1]


async def _generate_opening(scene: SceneRow, total_rounds: int, current_category: str = "") -> str:
    """调用 LLM 生成开场白"""
    system_prompt = OPENING_PROMPT.format(
        scene_description=scene.scene_description or "",
        summary_text=scene.summary_text or scene.knowledge_base or "",
        current_category=current_category or "综合能力",
    )
    return await _llm_invoke_text(system_prompt, "请生成开场白。", scene.model_name)


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


async def _generate_detailed_suggestions(
    scene: SceneRow, dialog_history: list, user_message: str, current_category: str = ""
) -> dict:
    """调用 LLM 生成详细评价建议"""
    history_text = _build_dialog_history(dialog_history) if dialog_history else "（对话刚开始，暂无历史）"

    system_prompt = DETAIL_SUGGESTION_PROMPT.format(
        scene_description=scene.scene_description or "",
        summary_text=scene.summary_text or scene.knowledge_base or "",
        current_category=current_category or "综合能力",
        user_message=user_message,
        dialog_history=history_text,
    )
    return await _llm_invoke_json(system_prompt, "请生成详细评价建议。", scene.model_name)


async def _generate_inspiration(scene: SceneRow, dialogs: list) -> dict:
    """调用 LLM 生成对话灵感（知识点提示）"""
    history_text = _build_dialog_history(dialogs) if dialogs else "（对话刚开始，暂无历史）"

    current_round = 0
    for d in dialogs:
        if d.speaker == 1 and d.content:
            current_round += 1
    current_category = _get_current_category(scene, current_round, None)

    system_prompt = INSPIRATION_PROMPT.format(
        current_category=current_category or "综合能力",
        scene_description=scene.scene_description or "",
        knowledge_base=scene.summary_text or scene.knowledge_base or "暂无知识库内容",
        dialog_history=history_text,
    )

    try:
        result = await _llm_invoke_json(system_prompt, "请生成对话灵感。", scene.model_name)
        tips = result.get("tips", [])
        return [
            {"category": t.get("category", ""), "content": t.get("content", "")[:150]}
            for t in tips[:3]
        ]
    except Exception as e:
        logger.error(f"生成灵感失败：{str(e)}")
        if scene.summary_text:
            tips = []
            for line in scene.summary_text.split('\n'):
                line = line.strip()
                if line and ':' in line:
                    category, content = line.split(':', 1)
                    tips.append({"category": category.strip()[:20], "content": content.strip()[:150]})
            return tips[:3]
        return []


async def _generate_report(scene: SceneRow, dialogs: list) -> dict:
    """调用 LLM 生成最终评估报告"""
    dialog_text = _build_dialog_history(dialogs)

    system_prompt = REPORT_SYSTEM_PROMPT.format(
        exam_categories=scene.exam_categories or "沟通能力，专业素养",
        scoring_rules=scene.scoring_rules or "根据学员综合表现进行评分",
        full_dialog_with_scores=dialog_text,
    )
    return await _llm_invoke_json(system_prompt, "请生成最终报告。", scene.model_name)


async def _generate_closing_message(scene: SceneRow, dialogs: list, total_score: float) -> str:
    """生成对练结束语"""
    dialog_text = _build_dialog_history(dialogs)

    system_prompt = f"""
系统角色：你正在模拟一位真实客户，与学员完成了一场对话练习。

【场景背景】
{scene.scene_description or ''}

【对话历史】
{dialog_text}

【你的任务】
对话已结束，请生成一条自然、友好的结束语：
1. 感谢学员的耐心解答
2. 表达对产品/服务的满意或兴趣
3. 表示期待下次交流或购买意愿
4. 语气亲切、自然，符合日常对话习惯
5. 不要超过3句话
"""

    response = await _llm_invoke_text(system_prompt, "请生成自然友好的结束语。", scene.model_name)
    return response.strip() if response else "感谢你的解答，期待下次交流！"


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
    """根据记录 ID 加载记录、课程和场景"""
    from sqlalchemy import select as sa_select

    async with get_db() as session:
        result = await session.execute(
            sa_select(CourseRecordRow).where(CourseRecordRow.id == record_id)
        )
        record = result.scalar_one_or_none()
        if not record:
            raise ValueError(f"练习记录 {record_id} 不存在")

        if record.end_time is not None:
            raise ValueError("本次对练已结束，无法继续")

    course, scene = await _load_scene_by_course(record.course_id)
    return record, course, scene


# ── TTS 语音合成 ─────────────────────────────────────────────────


async def _generate_tts(text: str, record_id: int) -> str:
    """生成 TTS 语音（使用 DashScope Qwen3-TTS-Flash）"""
    import dashscope
    import httpx
    from app.config import get_config
    from app.oss_upload import generate_filename, upload_file_to_oss

    config = get_config()
    timestamp = int(time.time())

    dashscope_config = config.dashscope
    if not dashscope_config.is_configured():
        logger.warning("【TTS生成】DashScope未配置")
        oss_config = config.oss
        if oss_config.is_configured():
            filename = generate_filename(f"ai_{record_id}_{timestamp}.mp3")
            bucket_host = oss_config.bucket_host if oss_config.bucket_host else f"https://{oss_config.bucket_name}.{oss_config.endpoint}"
            oss_url = f"{bucket_host}/{filename}"
            logger.info(f"【TTS生成】DashScope未配置，使用模拟OSS地址: {oss_url}")
            return oss_url
        else:
            return f"/uploads/voice/ai_{record_id}_{timestamp}.mp3"

    dashscope.api_key = dashscope_config.resolved_api_key
    dashscope.base_http_api_url = dashscope_config.base_url

    try:
        response = dashscope.MultiModalConversation.call(
            model="qwen3-tts-flash",
            text=text,
            voice="Cherry",
            language_type="Chinese",
            stream=False
        )

        if response.status_code != 200:
            raise Exception(f"DashScope TTS API error: {response.message}")

        audio_url = response.output.audio.url
        logger.info(f"【TTS生成】DashScope返回音频URL: {audio_url}")

        oss_config = config.oss
        if oss_config.is_configured():
            async with httpx.AsyncClient() as client:
                audio_response = await client.get(audio_url)
                if audio_response.status_code != 200:
                    raise Exception(f"Failed to download audio from DashScope: {audio_response.status_code}")

                audio_data = audio_response.content
                logger.info(f"【TTS生成】音频下载完成，大小: {len(audio_data)} bytes")

                filename = generate_filename(f"ai_{record_id}_{timestamp}.mp3")
                oss_url = await upload_file_to_oss(
                    file_data=audio_data,
                    filename=filename,
                    content_type="audio/mpeg"
                )
                logger.info(f"【TTS生成】成功上传到OSS: {oss_url}")
                return oss_url
        else:
            logger.info(f"【TTS生成】OSS未配置，使用DashScope URL")
            return audio_url

    except Exception as e:
        logger.error(f"【TTS生成】失败: {e}")
        raise RuntimeError(f"TTS generation failed: {str(e)}")


# ── PracticeService ──────────────────────────────────────────────


class PracticeService:
    """自由式对练核心引擎"""

    @staticmethod
    async def start(course_id: int, user_name: str) -> dict:
        """开始对练"""
        course, scene = await _load_scene_by_course(course_id)

        logger.info(f"【总轮次计算】practice_mode={repr(scene.practice_mode)}, exam_categories={repr(scene.exam_categories)}, dialog_round_limit={scene.dialog_round_limit}")

        if (scene.practice_mode == "text" or scene.practice_mode == "自由式") and scene.exam_categories:
            categories = scene.exam_categories.replace("，", ",").split(",")
            total_rounds = len([cat.strip() for cat in categories if cat.strip()])
            if total_rounds == 0:
                total_rounds = 5
        else:
            total_rounds = scene.dialog_round_limit or 5

        async with get_db() as session:
            course_record = CourseRecordRow(
                course_id=course_id,
                scene_id=scene.scene_id,
                start_time=now_local(),
                user_name=user_name,
                scene_name=scene.scene_name,
                course_type=course.course_type,
                practice_mode=course.practice_mode,
            )
            try:
                course_record.total_rounds = total_rounds
            except Exception:
                logger.warning("total_rounds 字段尚未在数据库中添加，将跳过该字段的写入")
            session.add(course_record)
            await session.commit()
            await session.refresh(course_record)
            record_id = course_record.id

        first_category = _get_current_category(scene, 1, record_id)
        opening_message = await _generate_opening(scene, total_rounds, first_category)

        opening_dialog_data = {
            "record_id": record_id,
            "speaker": 2,
            "content": opening_message,
            "content_type": "2" if course.practice_mode == "voice" else "1",
        }
        if course.practice_mode == "voice":
            tts_url = await _generate_tts(opening_message, record_id)
            opening_dialog_data["content_url"] = tts_url

        await DialogDetailService.create_dialog(opening_dialog_data)

        return {
            "recordId": record_id,
            "courseName": course.course_name,
            "sceneName": scene.scene_name,
            "sceneDescription": scene.scene_description,
            "totalRounds": total_rounds,
            "customerMessage": opening_message,
            "contentType": "2" if course.practice_mode == "voice" else "1",
            "contentUrl": opening_dialog_data.get("content_url"),
            "round": 1,
            "practiceMode": course.practice_mode,
        }

    @staticmethod
    async def turn(record_id: int, user_message: str, practice_mode: str = "text") -> dict:
        """对练对话轮次处理"""
        user_message = user_message.strip()
        if not user_message:
            raise ValueError("消息内容不能为空")

        if re.match(r'^[?？,，\s]+$', user_message):
            raise ValueError("无效的消息内容")

        record, course, scene = await _load_scene_by_record(record_id)

        practice_mode = record.practice_mode or course.practice_mode
        total_rounds = record.total_rounds or 5
        logger.info(f"【轮次处理】从记录读取配置: practice_mode={repr(practice_mode)}, total_rounds={total_rounds}")

        all_dialogs = await DialogDetailService.get_dialogs_by_record(record_id)
        ai_reply_count = 0
        for d in all_dialogs:
            if d.speaker == 2 and d.content:
                ai_reply_count += 1
        current_round = ai_reply_count

        dialog_data = {
            "record_id": record_id,
            "speaker": 1,
            "content": user_message,
            "content_type": "2" if practice_mode == "voice" else "1",
        }

        if practice_mode == "voice":
            logger.info(f"【学员语音】practice_mode={practice_mode}, user_message长度={len(user_message)}, 消息开头={user_message[:50]}")
            url_match = re.search(r'\[url\](.+?)\[/url\]', user_message, re.DOTALL)

            if not url_match:
                url_match = re.search(r'https?://[^\s]+\.(mp3|aac|wav)', user_message)

            if url_match:
                oss_url = url_match.group(1).strip()
                dialog_data["content_url"] = oss_url
                dialog_data["content"] = re.sub(r'\[url\].+?\[/url\]\s*|\s*https?://[^\s]+\.(mp3|aac|wav)\s*', '', user_message, flags=re.DOTALL).strip()
                logger.info(f"【学员语音】提取OSS URL成功: {oss_url}, 转写文本: {dialog_data['content']}")
            else:
                logger.error(f"【学员语音】未找到OSS URL，原始消息: {user_message[:200]}")
                raise ValueError("语音模式下必须提供音频URL")
        else:
            logger.info(f"【文本模式】practice_mode={practice_mode}")

        await DialogDetailService.create_dialog(dialog_data)

        all_dialogs = await DialogDetailService.get_dialogs_by_record(record_id)
        ai_reply_count = 0
        for d in all_dialogs:
            if d.speaker == 2 and d.content:
                ai_reply_count += 1
        current_round = ai_reply_count

        current_category = _get_current_category(scene, current_round, record_id)
        evaluation = await _evaluate_user_message(scene, all_dialogs, user_message, current_category)

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

        user_reply_count = 0
        for d in all_dialogs:
            if d.speaker == 1 and d.content:
                user_reply_count += 1
        is_complete = user_reply_count >= total_rounds
        logger.info(f"【结束判断】total_rounds={total_rounds}, user_reply_count={user_reply_count}, is_complete={is_complete}")

        if is_complete:
            report = await _generate_report(scene, all_dialogs)
            total_score = _calc_total_score(report)
            end_time = now_local()

            async with get_db() as session:
                from sqlalchemy import update as sa_update

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

            closing_message = await _generate_closing_message(scene, all_dialogs, total_score)

            closing_dialog_data = {
                "record_id": record_id,
                "speaker": 2,
                "content": closing_message,
                "content_type": "1",
            }
            await DialogDetailService.create_dialog(closing_dialog_data)

            return {
                "recordId": record_id,
                "round": total_rounds,
                "evaluation": {
                    "roundScore": evaluation.get("round_score", 0),
                    "dimensionScores": evaluation.get("dimension_scores", {}),
                    "feedback": evaluation.get("feedback", ""),
                },
                "customerMessage": closing_message,
                "contentUrl": "",
                "contentType": "1",
                "isComplete": True,
                "report": report,
            }

        next_round = current_round + 1
        next_category = _get_current_category(scene, next_round, record_id)
        customer_message = await _generate_customer_reply(scene, all_dialogs, next_round, total_rounds, next_category)

        ai_dialog_data = {
            "record_id": record_id,
            "speaker": 2,
            "content": customer_message,
            "content_type": "2" if practice_mode == "voice" else "1",
        }
        if practice_mode == "voice":
            tts_url = await _generate_tts(customer_message, record_id)
            ai_dialog_data["content_url"] = tts_url

        await DialogDetailService.create_dialog(ai_dialog_data)

        all_dialogs = await DialogDetailService.get_dialogs_by_record(record_id)
        ai_reply_count = 0
        for d in all_dialogs:
            if d.speaker == 2 and d.content:
                ai_reply_count += 1
        updated_round = ai_reply_count

        async with get_db() as session:
            from sqlalchemy import update as sa_update
            await session.execute(
                sa_update(CourseRecordRow)
                .where(CourseRecordRow.id == record_id)
                .values(last_time=now_local())
            )
            await session.commit()

        voice_url = ai_dialog_data.get("content_url", "") if practice_mode == "voice" else ""

        return {
            "recordId": record_id,
            "round": updated_round,
            "totalRounds": total_rounds,
            "evaluation": {
                "roundScore": evaluation.get("round_score", 0),
                "dimensionScores": evaluation.get("dimension_scores", {}),
                "feedback": evaluation.get("feedback", ""),
            },
            "customerMessage": customer_message,
            "contentUrl": voice_url,
            "contentType": "2" if practice_mode == "voice" else "1",
            "isComplete": False,
        }

    @staticmethod
    async def end(record_id: int) -> dict:
        """手动结束对练"""
        record, course, scene = await _load_scene_by_record(record_id)

        if record.end_time is not None:
            return {
                "recordId": record_id,
                "totalRounds": record.total_score or 0,
                "report": record.summary or "",
                "message": "本次对练已结束",
            }

        all_dialogs = await DialogDetailService.get_dialogs_by_record(record_id)

        current_round = 0
        for d in all_dialogs:
            if d.speaker == 1 and d.content:
                current_round += 1

        report = await _generate_report(scene, all_dialogs)
        total_score = _calc_total_score(report)
        end_time = now_local()

        async with get_db() as session:
            from sqlalchemy import update as sa_update

            await session.execute(
                sa_update(CourseRecordRow)
                .where(CourseRecordRow.id == record_id)
                .values(
                    total_score=total_score,
                    end_time=end_time,
                    summary=report.get("summary", "")[:65535] if report else "",
                    accord_finish=2,
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
    async def get_practice_history(record_id: int) -> dict:
        """获取某次对练的完整对话历史"""
        dialogs = await DialogDetailService.get_dialogs_by_record(record_id)

        record = None
        async with get_db() as session:
            record = await session.get(CourseRecordRow, record_id)

        total_rounds = record.total_rounds if record and record.total_rounds else 5

        result = []
        ai_reply_count = 0
        current_round = 0

        for d in dialogs:
            if d.speaker == 2 and d.content:
                ai_reply_count += 1
                current_round = ai_reply_count

            content = d.content
            if content:
                content = re.sub(r'\[url\].+?\[/url\]\s*', '', content, flags=re.DOTALL).strip()

            has_audio = (d.content_type == "2") or (d.content_url and d.content_url.strip())

            result.append({
                "dialog_id": d.dialog_id,
                "record_id": d.record_id,
                "speaker": d.speaker,
                "content_type": d.content_type,
                "content": content,
                "content_url": d.content_url,
                "audio_url": d.content_url,
                "has_audio": has_audio,
                "is_audio": has_audio,
                "isAudio": has_audio,
                "audio": has_audio,
                "intent_analysis": d.intent_analysis,
                "round_number": current_round,
                "score": d.score,
                "feedback": d.feedback,
                "create_time": d.create_time.isoformat() if d.create_time else None,
            })

        practice_mode = 'text'
        if record and record.practice_mode:
            practice_mode = record.practice_mode
        else:
            for d in dialogs:
                if d.content_type == "2" or (d.content_url and d.content_url.strip()):
                    practice_mode = 'voice'
                    break

        logger.info(f"【历史查询】record_id={record_id}, practice_mode={practice_mode}, total_rounds={total_rounds}")

        return {
            "history": result,
            "totalRounds": total_rounds,
            "practiceMode": practice_mode,
            "practice_mode": practice_mode,
        }

    @staticmethod
    async def get_report(record_id: int) -> dict:
        """获取最终评估报告"""
        from sqlalchemy import select as sa_select

        async with get_db() as session:
            result = await session.execute(
                sa_select(CourseRecordRow).where(CourseRecordRow.id == record_id)
            )
            record = result.scalar_one_or_none()
            if not record:
                raise ValueError(f"练习记录 {record_id} 不存在")

            is_completed = record.end_time is not None and record.summary is not None

            report = {
                "summary": "",
                "total_score": record.total_score or 0,
                "dimension_scores": {},
                "dimension_feedbacks": {},
                "strengths": [],
                "improvements": [],
            }

            if is_completed and record.summary:
                try:
                    parsed_report = json.loads(record.summary)
                    if isinstance(parsed_report, dict):
                        report.update(parsed_report)
                    else:
                        report["summary"] = record.summary
                except json.JSONDecodeError:
                    report["summary"] = record.summary

            calculated_total_score = _calc_total_score(report)

            return {
                "success": True,
                "record_id": record.id,
                "total_score": calculated_total_score,
                "summary": report.get("summary", ""),
                "status": "completed" if is_completed else "generating",
                "report": {
                    **report,
                    "total_score": calculated_total_score,
                },
            }

    @staticmethod
    async def regenerate_report(record_id: int) -> dict:
        """重新生成评估报告"""
        from sqlalchemy import select as sa_select

        logger.info(f"开始重新生成评估报告，record_id={record_id}")

        async with get_db() as session:
            result = await session.execute(
                sa_select(CourseRecordRow).where(CourseRecordRow.id == record_id)
            )
            record = result.scalar_one_or_none()
            if not record:
                raise ValueError(f"练习记录 {record_id} 不存在")

            dialogs_result = await session.execute(
                sa_select(DialogDetailRow).where(DialogDetailRow.record_id == record_id)
            )
            dialogs = dialogs_result.scalars().all()

            report = await _generate_report_by_scene(record.scene_id, dialogs)

            record.summary = json.dumps(report, ensure_ascii=False)
            record.total_score = _calc_total_score(report)
            record.end_time = datetime.now()

            await session.commit()

            return {
                "success": True,
                "record_id": record.id,
                "total_score": report.get("total_score", 0),
                "summary": report.get("summary", ""),
                "status": "completed",
                "report": report,
            }

    @staticmethod
    async def get_detailed_suggestions(record_id: int, dialog_id: int) -> dict:
        """获取指定对话的详细评价建议"""
        record, course, scene = await _load_scene_by_record(record_id)

        dialogs = await DialogDetailService.get_dialogs_by_record(record_id)

        target_dialog = None
        for d in dialogs:
            if d.dialog_id == dialog_id:
                target_dialog = d
                break

        if not target_dialog:
            raise ValueError(f"对话记录 {dialog_id} 不存在")

        current_round = 0
        for d in dialogs:
            if d.speaker == 1 and d.content:
                current_round += 1
                if d.dialog_id == dialog_id:
                    break

        current_category = _get_current_category(scene, current_round, record_id)

        suggestions = await _generate_detailed_suggestions(
            scene, dialogs, target_dialog.content, current_category
        )

        return {
            "recordId": record_id,
            "dialogId": dialog_id,
            "round": current_round,
            "currentCategory": current_category,
            "suggestions": suggestions.get("suggestions", []),
            "polishedExpression": suggestions.get("polishedExpression", ""),
        }

    @staticmethod
    async def generate_inspiration(record_id: int) -> dict:
        """根据当前对话历史生成对话灵感"""
        record, course, scene = await _load_scene_by_record(record_id)

        dialogs = await DialogDetailService.get_dialogs_by_record(record_id)

        current_round = 0
        for d in dialogs:
            if d.speaker == 1 and d.content:
                current_round += 1
        current_category = _get_current_category(scene, current_round, record_id)

        inspiration = await _generate_inspiration(scene, dialogs)

        return {
            "recordId": record_id,
            "currentRound": current_round,
            "currentCategory": current_category or "综合能力",
            "inspiration": inspiration,
        }


async def _generate_report_by_scene(scene_id: int, dialogs: list) -> dict:
    """根据场景 ID 重新生成报告"""
    from sqlalchemy import select as sa_select

    async with get_db() as session:
        result = await session.execute(
            sa_select(SceneRow).where(SceneRow.scene_id == scene_id)
        )
        scene = result.scalar_one_or_none()
        if not scene:
            raise ValueError(f"场景 {scene_id} 不存在")

        return await _generate_report(scene, dialogs)
