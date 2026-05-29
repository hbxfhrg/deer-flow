"""自由式对练核心引擎

实现 LLM 驱动的自由式对练，每轮经过：
1. 保存学员话术
2. LLM 评估打分（多维度）
3. LLM 生成客户角色下一条回复
"""

import json
import re
import random
import logging
from datetime import datetime

from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# 导入时区工具（从配置读取时区）
from deerflow.roleplay.timezone_utils import now_local

from deerflow.models import create_chat_model
from deerflow.roleplay import get_db
from deerflow.roleplay.models import SceneRow, CourseRow, DialogDetailRow, CourseRecordRow
from deerflow.roleplay.services import SceneService, CourseService, DialogDetailService

logger = logging.getLogger(__name__)


# ── LLM 调用工具函数 ─────────────────────────────────────────

def _parse_json_from_text(text: str) -> dict:
    """从 LLM 返回文本中提取 JSON，兼容 markdown 代码块包裹的情况"""
    text = text.strip()
    match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    return text


# 修复策略成功率统计（基于经验值，可根据实际运行数据动态调整）
_REPAIR_STRATEGY_SUCCESS_RATES = {
    "py_fix": 0.75,    # Python代码修复成功率
    "llm_fix": 0.85,   # LLM格式修复成功率
    "llm_regen": 0.9,  # LLM重新生成成功率
}

# 错误类型与推荐策略映射
_ERROR_TYPE_STRATEGIES = {
    "missing_quote": ["py_fix", "llm_fix", "llm_regen"],     # 缺引号：Py修复最有效
    "missing_comma": ["py_fix", "llm_fix", "llm_regen"],     # 缺逗号：Py修复最有效
    "missing_bracket": ["py_fix", "llm_fix", "llm_regen"],   # 缺括号：Py修复最有效
    "format_mess": ["llm_fix", "llm_regen", "py_fix"],       # 格式混乱：LLM修复更有效
    "content_empty": ["llm_regen", "llm_fix", "py_fix"],     # 内容缺失：重新生成最有效
    "unknown": ["llm_fix", "llm_regen", "py_fix"],           # 未知错误：优先LLM
}


def _classify_json_error(error_msg: str) -> str:
    """
    识别 JSON 解析错误类型
    
    Args:
        error_msg: JSONDecodeError 的错误消息
    
    Returns:
        错误类型：missing_quote, missing_comma, missing_bracket, format_mess, content_empty, unknown
    """
    error_msg_lower = error_msg.lower()
    
    # 缺引号：Expecting property name enclosed in double quotes
    if "property name" in error_msg_lower or "expecting" in error_msg_lower and "double quote" in error_msg_lower:
        return "missing_quote"
    
    # 缺逗号：Expecting ',' delimiter
    if "expecting ','" in error_msg_lower or "expecting ',' delimiter" in error_msg_lower:
        return "missing_comma"
    
    # 缺括号：Unexpected end of JSON input
    if "unexpected end of json" in error_msg_lower:
        return "missing_bracket"
    
    # 格式混乱：Invalid JSON, multiple errors
    if "invalid" in error_msg_lower or "multiple" in error_msg_lower:
        return "format_mess"
    
    # 内容缺失：JSON结构正确但数据为空
    if "null" in error_msg_lower or "empty" in error_msg_lower:
        return "content_empty"
    
    return "unknown"


def _get_optimized_strategy_order(error_type: str) -> list:
    """
    根据错误类型和成功率获取优化后的策略执行顺序
    
    Args:
        error_type: 错误类型
    
    Returns:
        策略顺序列表
    """
    # 获取该错误类型的推荐策略顺序
    base_strategies = _ERROR_TYPE_STRATEGIES.get(error_type, ["llm_fix", "llm_regen", "py_fix"])
    
    # 根据成功率排序，保持推荐顺序的同时优先高成功率策略
    scored_strategies = []
    for strategy in base_strategies:
        scored_strategies.append((strategy, _REPAIR_STRATEGY_SUCCESS_RATES.get(strategy, 0.5)))
    
    # 按成功率从高到低排序
    scored_strategies.sort(key=lambda x: -x[1])
    
    return [s[0] for s in scored_strategies]


async def _parse_json_with_retry(text: str, model_name: str | None = None, max_rounds: int = 3) -> dict:
    """
    带智能重试机制的 JSON 解析：
    
    优化策略：
    1. 错误类型识别：根据 JSON 解析错误类型选择最佳修复策略
    2. 智能步骤排序：根据成功率动态调整策略执行顺序
    
    每轮按优化后的顺序执行修复策略，最多走3轮。
    
    Args:
        text: LLM 返回的原始文本
        model_name: 模型名称
        max_rounds: 最大重试轮数（默认3）
    
    Returns:
        解析后的 JSON 字典，或包含错误提示的字典
    """
    # 第一步：尝试基础解析
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
    
    # 获取优化后的策略执行顺序
    strategy_order = _get_optimized_strategy_order(error_type)
    logger.info(f"【JSON修复】错误类型: {error_type}, 优化策略顺序: {strategy_order}")
    
    # 智能重试：最多3轮，每轮按优化顺序执行策略
    for round_num in range(1, max_rounds + 1):
        logger.info(f"【JSON修复】开始第{round_num}/{max_rounds}轮重试")
        
        for strategy in strategy_order:
            step_name = {
                "py_fix": "Python代码修复",
                "llm_fix": "LLM格式修复",
                "llm_regen": "LLM重新生成"
            }[strategy]
            
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
        
        logger.info(f"【JSON修复】第{round_num}轮结束，进入下一轮")
    
    # 所有轮次都失败，返回错误提示
    logger.error(f"【JSON解析完全失败】经过{max_rounds}轮重试后仍无法解析")
    logger.error(f"原始文本: {text[:500]}...")
    return {
        "dimension_scores": {},
        "summary": "程序出错了，请稍后再试。",
        "strengths": [],
        "improvements": [],
    }


async def _fix_json_format(malformed_json: str, model_name: str | None = None) -> str | None:
    """调用 LLM 修复格式错误的 JSON（第1轮重试）"""
    system_prompt = """
你是一个 JSON 格式修复专家。请修复以下 JSON 文本中的格式错误：

要求：
1. 保持原始数据内容不变
2. 修复语法错误（如缺失逗号、引号不匹配等）
3. 返回纯 JSON 字符串，不要包含其他内容
4. 如果无法修复，返回空字符串

示例：
输入：{"name": "test", "value": 123
输出：{"name": "test", "value": 123}
"""
    
    user_prompt = f"请修复以下 JSON 的格式错误：\n{malformed_json}"
    
    try:
        response = await _llm_invoke_text(system_prompt, user_prompt, model_name)
        # 清理响应，提取 JSON
        cleaned = _parse_json_from_text(response)
        # 验证是否是有效的 JSON
        json.loads(cleaned)
        return cleaned
    except Exception as e:
        logger.error(f"LLM格式修复失败: {e}")
        return None


async def _regenerate_json(original_text: str, model_name: str | None = None) -> str | None:
    """调用 LLM 重新生成完整的 JSON（第2轮重试）"""
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

示例输出：
{"dimension_scores": {"沟通能力": 80, "专业素养": 85}, "summary": "整体表现良好", "strengths": ["表达清晰"], "improvements": ["需要更多技术细节"]}
"""
    
    user_prompt = f"根据以下对话内容，生成评估报告 JSON：\n{original_text}"
    
    try:
        response = await _llm_invoke_text(system_prompt, user_prompt, model_name)
        # 清理响应，提取 JSON
        cleaned = _parse_json_from_text(response)
        # 验证是否是有效的 JSON
        json.loads(cleaned)
        return cleaned
    except Exception as e:
        logger.error(f"LLM重新生成失败: {e}")
        return None


def _fix_json_with_code(malformed_json: str) -> str | None:
    """使用 Python 代码尝试修复常见的 JSON 格式错误（第3轮重试）"""
    try:
        # 修复1：添加缺失的引号
        fixed = malformed_json
        
        # 修复未加引号的键名
        import re
        # 匹配未加引号的键名：{key: value} -> {"key": value}
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
            # 查找未闭合的字符串
            if line.count('"') % 2 != 0:
                # 在末尾添加引号
                fixed_lines.append(line.rstrip() + '"')
            else:
                fixed_lines.append(line)
        fixed = '\n'.join(fixed_lines)
        
        # 验证修复结果
        result = json.loads(fixed)
        if isinstance(result, dict):
            return json.dumps(result)
        return None
    except Exception as e:
        logger.error(f"Python代码修复失败: {e}")
        return None


async def _llm_invoke_json(system_prompt: str, user_prompt: str, model_name: str | None = None) -> dict:
    """通用 LLM 调用，返回解析后的 JSON dict（带重试机制）"""
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

# 开场白专用模板 - 包含自我介绍
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

例如，如果场景是汽车销售，考察"三电系统"：
- "您好！我是来看车的客户，想了解一下你们的电动车。能先介绍一下这款车的电池技术吗？"
- "你好，我最近在考虑换车，对电动车比较感兴趣。这款车的续航表现怎么样？"

例如，如果场景是面试：
- "你好，我是面试官陈翔。请先介绍一下你申请的职位和相关工作经验。"

请根据以上设定，生成开场白。先做简短自我介绍，再提出第一个问题。只输出开场白内容，不要加任何前缀或说明。"""

# 详细评价建议模板 - 生成改进建议和润色表达
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
}}

示例输出：
{{
  "suggestions": [
    "可以在介绍产品时更加详细，确保客户了解产品的特点和优势",
    "尝试使用更友好的语气，增加与客户的互动",
    "在回答时，确保语句完整，避免使用不清晰的表达"
  ],
  "polishedExpression": "你好，陈翔！很高兴认识你。我们的产品主要是硬件工牌，它具有高耐用性和多功能性，可以帮助企业更好地管理员工信息..."
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


# ── 辅助函数 ─────────────────────────────────────────────────

def _build_dialog_history(dialogs: list) -> str:
    """将对话记录列表转为可读的历史文本"""
    lines = []
    ai_reply_count = 0
    round_num = 0
    for d in dialogs:
        role = "学员" if d.speaker == 1 else "客户"
        
        # 以AI回复计算轮次（开场白算第1轮）
        if d.speaker == 2 and d.content:
            ai_reply_count += 1
            round_num = ai_reply_count  # 开场白算第1轮
        
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


async def _generate_opening(
    scene: SceneRow, total_rounds: int, current_category: str = ""
) -> str:
    """调用 LLM 生成开场白（包含自我介绍）"""
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
    """调用 LLM 评估学员发言（基础评估，用于实时反馈）"""
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
    """调用 LLM 生成详细评价建议（包括改进建议列表和润色表达）"""
    history_text = _build_dialog_history(dialog_history) if dialog_history else "（对话刚开始，暂无历史）"

    system_prompt = DETAIL_SUGGESTION_PROMPT.format(
        scene_description=scene.scene_description or "",
        summary_text=scene.summary_text or scene.knowledge_base or "",
        current_category=current_category or "综合能力",
        user_message=user_message,
        dialog_history=history_text,
    )
    return await _llm_invoke_json(system_prompt, "请生成详细评价建议。", scene.model_name)


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


async def _generate_inspiration(scene: SceneRow, dialogs: list) -> dict:
    """调用 LLM 生成对话灵感（知识点提示）"""
    history_text = _build_dialog_history(dialogs) if dialogs else "（对话刚开始，暂无历史）"
    
    # 计算当前轮次和对应的考核维度
    current_round = 0
    for d in dialogs:
        if d.speaker == 1 and d.content:  # 学员回复
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
        # 限制数量和长度
        return [
            {"category": t.get("category", ""), "content": t.get("content", "")[:150]}
            for t in tips[:3]
        ]
    except Exception as e:
        # 如果调用失败，返回默认的知识库内容
        logger = logging.getLogger(__name__)
        logger.error(f"生成灵感失败：{str(e)}")
        # 解析摘要文本作为备选
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

【示例】
- "感谢你的详细介绍！我对这款产品很感兴趣，考虑一下后会联系你。再见！"
- "谢谢你的耐心解答，我了解得很清楚了。期待下次见面！"
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
        # - 自由式对练（practice_mode="text"或"自由式"）：取exam_categories字段中逗号分隔的类别数量
        # - 其他模式：使用dialog_round_limit配置，默认5轮
        logger.info(f"【总轮次计算】practice_mode={repr(scene.practice_mode)}, exam_categories={repr(scene.exam_categories)}, dialog_round_limit={scene.dialog_round_limit}")
        if (scene.practice_mode == "text" or scene.practice_mode == "自由式") and scene.exam_categories:
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
                start_time=now_local(),
                user_name=user_name,
                scene_name=scene.scene_name,
                course_type=course.course_type,
                practice_mode=course.practice_mode,
            )
            # 设置总轮次（如果数据库字段已添加）
            try:
                course_record.total_rounds = total_rounds
            except Exception:
                logger.warning("total_rounds 字段尚未在数据库中添加，将跳过该字段的写入")
            session.add(course_record)
            await session.commit()
            await session.refresh(course_record)
            
            record_id = course_record.id  # 使用 course_record 的 id 作为 record_id

        # 3. LLM 生成开场白（第1轮对应第一个随机后的考核维度，使用 record_id 作为种子）
        first_category = _get_current_category(scene, 1, record_id)
        opening_message = await _generate_opening(scene, total_rounds, first_category)

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
            "round": 1,  # 开场白算第1轮开始
            "practiceMode": course.practice_mode,
        }

    @staticmethod
    async def turn(record_id: int, user_message: str) -> dict:
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
        # - 自由式对练（practice_mode="text"或"自由式"）：取exam_categories字段中逗号分隔的类别数量
        # - 其他模式：使用dialog_round_limit配置，默认5轮
        logger.info(f"【总轮次计算】practice_mode={repr(scene.practice_mode)}, exam_categories={repr(scene.exam_categories)}, dialog_round_limit={scene.dialog_round_limit}")
        if (scene.practice_mode == "text" or scene.practice_mode == "自由式") and scene.exam_categories:
            # 同时支持中文逗号和英文逗号分割
            categories = scene.exam_categories.replace("，", ",").split(",")
            total_rounds = len([cat.strip() for cat in categories if cat.strip()])
            if total_rounds == 0:
                total_rounds = 5
        else:
            total_rounds = scene.dialog_round_limit or 5
        
        # 获取当前对话历史，动态计算当前轮次
        all_dialogs = await DialogDetailService.get_dialogs_by_record(record_id)
        # 计算当前轮次：以AI生成的回复数量计算（开场白算第1轮）
        ai_reply_count = 0
        for d in all_dialogs:
            if d.speaker == 2 and d.content:  # AI回复
                ai_reply_count += 1
        
        # 当前轮次 = AI回复数量（开场白算第1轮）
        # ai_reply_count: 1=开场白(第1轮), 2=第2轮AI回复, 3=第3轮AI回复...
        current_round = ai_reply_count

        # 2. 写入学员话术
        await DialogDetailService.create_dialog({
            "record_id": record_id,
            "speaker": 1,  # 学员
            "content": user_message,
        })

        # 3. 获取最新对话历史（用于评估上下文）
        all_dialogs = await DialogDetailService.get_dialogs_by_record(record_id)

        # 重新计算当前轮次（学员消息已写入）
        ai_reply_count = 0
        for d in all_dialogs:
            if d.speaker == 2 and d.content:
                ai_reply_count += 1
        current_round = ai_reply_count

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

        # 6. 判断是否完成：使用学员回复数量来判定结束
        user_reply_count = 0
        for d in all_dialogs:
            if d.speaker == 1 and d.content:
                user_reply_count += 1
        is_complete = user_reply_count >= total_rounds

        if is_complete:
            # 自动结束：生成最终报告
            report = await _generate_report(scene, all_dialogs)
            total_score = _calc_total_score(report)
            end_time = now_local()

            async with get_db() as session:
                from sqlalchemy import update as sa_update
                
                # 更新 pract_course_record（报告数据存储到 summary 字段）
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

            # 生成结束语
            closing_message = await _generate_closing_message(scene, all_dialogs, total_score)
            
            await DialogDetailService.create_dialog({
                "record_id": record_id,
                "speaker": 2,
                "content": closing_message,
            })
            
            return {
                "recordId": record_id,
                "round": total_rounds,  # 结束语不算轮次，直接返回总轮数
                "evaluation": {
                    "roundScore": evaluation.get("round_score", 0),
                    "dimensionScores": evaluation.get("dimension_scores", {}),
                    "feedback": evaluation.get("feedback", ""),
                },
                "customerMessage": closing_message,
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

        # 8. 重新计算当前轮次（AI回复已写入）
        all_dialogs = await DialogDetailService.get_dialogs_by_record(record_id)
        ai_reply_count = 0
        for d in all_dialogs:
            if d.speaker == 2 and d.content:
                ai_reply_count += 1
        updated_round = ai_reply_count

        # 9. 更新 pract_course_record 的 last_time
        async with get_db() as session:
            from sqlalchemy import update as sa_update
            await session.execute(
                sa_update(CourseRecordRow)
                .where(CourseRecordRow.id == record_id)
                .values(last_time=now_local())
            )
            await session.commit()

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
        end_time = now_local()

        async with get_db() as session:
            from sqlalchemy import update as sa_update
            
            # 更新 pract_course_record（报告数据存储到 summary 字段）
            await session.execute(
                sa_update(CourseRecordRow)
                .where(CourseRecordRow.id == record_id)
                .values(
                    total_score=total_score,
                    end_time=end_time,
                    summary=report.get("summary", "")[:65535] if report else "",
                    accord_finish=2,  # 手动结束
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
        """获取某次对练的完整对话历史（含评分和总轮次）"""
        # 获取对话历史
        dialogs = await DialogDetailService.get_dialogs_by_record(record_id)
        
        # 通过 record_id 获取 course_record，获取总轮次（直接从记录中读取，不再重新计算）
        record = None
        async with get_db() as session:
            record = await session.get(CourseRecordRow, record_id)
        
        # 获取总轮次（优先使用记录中存储的值，避免重复计算）
        total_rounds = record.total_rounds if record and record.total_rounds else 5
        
        # 构建对话历史列表
        result = []
        ai_reply_count = 0  # 统计AI回复数量
        current_round = 0    # 当前轮次
        
        for d in dialogs:
            if d.speaker == 2 and d.content:  # AI回复
                ai_reply_count += 1
                # 开场白算第1轮，AI回复数量即为当前轮次
                current_round = ai_reply_count
            
            result.append({
                "dialog_id": d.dialog_id,
                "record_id": d.record_id,
                "speaker": d.speaker,
                "content_type": d.content_type,
                "content": d.content,
                "round_number": current_round,
                "score": d.score,
                "feedback": d.feedback,
                "create_time": d.create_time.isoformat() if d.create_time else None,
            })
        
        return {
            "history": result,
            "totalRounds": total_rounds,
        }

    @staticmethod
    async def get_report(record_id: int) -> dict:
        """获取最终评估报告（包含完整维度评分和反馈）"""
        from sqlalchemy import select as sa_select
        import json

        async with get_db() as session:
            result = await session.execute(
                sa_select(CourseRecordRow).where(CourseRecordRow.id == record_id)
            )
            record = result.scalar_one_or_none()
            if not record:
                raise ValueError(f"练习记录 {record_id} 不存在")
            
            # 判断报告是否已生成（通过检查 end_time 和 summary 是否存在）
            is_completed = record.end_time is not None and record.summary is not None
            
            # 尝试从 summary 字段解析 JSON 格式的完整报告
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
                    # 尝试解析 JSON
                    parsed_report = json.loads(record.summary)
                    if isinstance(parsed_report, dict):
                        report.update(parsed_report)
                    else:
                        # 如果不是 JSON，作为普通摘要文本处理
                        report["summary"] = record.summary
                except json.JSONDecodeError:
                    # 如果解析失败，作为普通摘要文本处理
                    report["summary"] = record.summary
            
            # 根据实际维度得分计算总分，确保一致性
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
        """重新生成评估报告（用于调试）"""
        from sqlalchemy import select as sa_select
        
        logger.info(f"开始重新生成评估报告，record_id={record_id}")
        
        async with get_db() as session:
            try:
                # 获取记录
                result = await session.execute(
                    sa_select(CourseRecordRow).where(CourseRecordRow.id == record_id)
                )
                record = result.scalar_one_or_none()
                if not record:
                    logger.error(f"练习记录 {record_id} 不存在")
                    raise ValueError(f"练习记录 {record_id} 不存在")
                
                logger.info(f"找到练习记录，scene_id={record.scene_id}")
                
                # 获取对话历史
                dialogs_result = await session.execute(
                    sa_select(DialogDetailRow).where(DialogDetailRow.record_id == record_id)
                )
                dialogs = dialogs_result.scalars().all()
                logger.info(f"找到 {len(dialogs)} 条对话记录")
                
                if not dialogs:
                    logger.warning(f"练习记录 {record_id} 没有对话历史")
                
                # 重新生成报告
                logger.info(f"开始调用LLM生成报告")
                report = await _generate_report_by_scene(record.scene_id, dialogs)
                logger.info(f"报告生成成功")
                
                # 更新记录：将完整报告序列化为 JSON 存储到 summary 字段
                import json
                record.summary = json.dumps(report, ensure_ascii=False)
                # 根据实际维度得分计算总分，确保一致性
                record.total_score = _calc_total_score(report)
                record.end_time = datetime.now()
                
                await session.commit()
                logger.info(f"练习记录 {record_id} 更新成功")
                
                return {
                    "success": True,
                    "record_id": record.id,
                    "total_score": report.get("total_score", 0),
                    "summary": report.get("summary", ""),
                    "status": "completed",
                    "report": report,
                }
            except Exception as e:
                logger.error(f"重新生成报告失败，record_id={record_id}，错误：{str(e)}", exc_info=True)
                raise

    @staticmethod
    async def get_detailed_suggestions(record_id: int, dialog_id: int) -> dict:
        """
        获取指定对话的详细评价建议（包括改进建议列表和润色表达）
        - 与对话轮次分开返回，不影响主要流转速度
        """
        # 1. 加载记录、课程、场景
        record, course, scene = await _load_scene_by_record(record_id)

        # 2. 获取对话详情
        dialogs = await DialogDetailService.get_dialogs_by_record(record_id)
        
        # 3. 找到指定的对话
        target_dialog = None
        for d in dialogs:
            if d.dialog_id == dialog_id:
                target_dialog = d
                break
        
        if not target_dialog:
            raise ValueError(f"对话记录 {dialog_id} 不存在")
        
        # 4. 计算当前轮次和考核维度
        current_round = 0
        for d in dialogs:
            if d.speaker == 1 and d.content:  # 学员回复
                current_round += 1
                if d.dialog_id == dialog_id:
                    break
        
        current_category = _get_current_category(scene, current_round, record_id)

        # 5. 生成详细评价建议
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
        """
        根据当前对话历史生成对话灵感（知识点提示）
        - 用户在练习过程中点击灵感按钮时调用此接口
        - 根据场景知识库和当前对话生成相关知识点提示
        """
        # 1. 加载记录、课程、场景
        record, course, scene = await _load_scene_by_record(record_id)

        # 2. 获取对话历史
        dialogs = await DialogDetailService.get_dialogs_by_record(record_id)

        # 3. 计算当前轮次和对应的考核维度
        current_round = 0
        for d in dialogs:
            if d.speaker == 1 and d.content:  # 学员回复
                current_round += 1
        current_category = _get_current_category(scene, current_round, record_id)

        # 4. 生成灵感
        inspiration = await _generate_inspiration(scene, dialogs)

        return {
            "recordId": record_id,
            "currentRound": current_round,
            "currentCategory": current_category or "综合能力",
            "inspiration": inspiration,
        }
