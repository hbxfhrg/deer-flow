from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from deerflow.roleplay import get_db
from deerflow.roleplay.services import SceneService, EvaluationService, PracticeRecordService, StatisticsService, CourseService
from deerflow.roleplay.practice_service import PracticeService
from deerflow.roleplay.auth_service import AuthService

router = APIRouter(prefix="/roleplay", tags=["roleplay"])

class SceneCreate(BaseModel):
    scene_id: Optional[int] = None
    scene_name: str
    scene_description: Optional[str] = ""
    model_name: Optional[str] = Field(default=None, alias="modelName")
    system_prompt: Optional[str] = ""
    user_prompt_template: Optional[str] = ""
    enabled: Optional[bool] = True
    metadata_json: Optional[Dict] = {}
    # 自由对练功能新增字段
    practice_mode: Optional[str] = Field(default="剧本式", alias="practiceMode")
    knowledge_base: Optional[str] = Field(default=None, alias="knowledgeBase")
    summary_text: Optional[str] = Field(default=None, alias="summaryText")
    exam_categories: Optional[str] = Field(default=None, alias="examCategories")
    scoring_rules: Optional[str] = Field(default=None, alias="scoringRules")
    prompt_template: Optional[str] = Field(default=None, alias="promptTemplate")
    create_by: Optional[str] = Field(default=None, alias="createBy")

    class Config:
        populate_by_name = True

class SceneUpdate(BaseModel):
    scene_name: Optional[str] = None
    scene_description: Optional[str] = None
    model_name: Optional[str] = Field(default=None, alias="modelName")
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    enabled: Optional[bool] = None
    metadata_json: Optional[Dict] = None
    # 自由对练功能新增字段
    practice_mode: Optional[str] = Field(default=None, alias="practiceMode")
    knowledge_base: Optional[str] = Field(default=None, alias="knowledgeBase")
    summary_text: Optional[str] = Field(default=None, alias="summaryText")
    exam_categories: Optional[str] = Field(default=None, alias="examCategories")
    scoring_rules: Optional[str] = Field(default=None, alias="scoringRules")
    prompt_template: Optional[str] = Field(default=None, alias="promptTemplate")

    class Config:
        populate_by_name = True

class EvaluationCreate(BaseModel):
    id: Optional[str] = None
    thread_id: str
    run_id: str
    scene_id: str
    user_id: str
    round_number: Optional[int] = 1
    total_score: Optional[int] = 0
    dimension_scores: Optional[Dict] = {}
    strengths: Optional[Dict] = {}
    improvements: Optional[Dict] = {}
    summary: Optional[str] = ""
    status: Optional[str] = "pending"

class EvaluationUpdate(BaseModel):
    total_score: Optional[int] = None
    dimension_scores: Optional[Dict] = None
    strengths: Optional[Dict] = None
    improvements: Optional[Dict] = None
    summary: Optional[str] = None
    status: Optional[str] = None

class PracticeRecordCreate(BaseModel):
    id: Optional[str] = None
    thread_id: str
    scene_id: str
    user_id: str
    total_rounds: Optional[int] = 5

class PracticeRecordComplete(BaseModel):
    dialog_rounds: Optional[int] = None
    total_score: Optional[float] = None
    report_data: Optional[Dict] = None
    duration: Optional[int] = None

@router.get("/scenes", summary="获取场景列表")
async def get_scenes():
    scenes = await SceneService.get_scenes()
    return {"scenes": [
        {
            "scene_id": s.scene_id,
            "scene_name": s.scene_name,
            "scene_description": s.scene_description,
            "scene_cover": s.scene_cover,
            "asr_correct_lib_id": s.asr_correct_lib_id,
            "sensitive_word_lib_id": s.sensitive_word_lib_id,
            "dialog_round_limit": s.dialog_round_limit,
            "end_speech": s.end_speech,
            "modelName": s.model_name,
            "systemPrompt": s.system_prompt,
            "userPromptTemplate": s.user_prompt_template,
            "enabled": s.status == 1,
            "createBy": s.create_by,
            "createdAt": s.create_time.isoformat() if s.create_time else None,
            "updatedAt": s.update_time.isoformat() if s.update_time else None,
            # 自由对练功能新增字段（使用驼峰命名）
            "practiceMode": s.practice_mode,
            "knowledgeBase": s.knowledge_base,
            "summaryText": s.summary_text,
            "examCategories": s.exam_categories,
            "scoringRules": s.scoring_rules,
            # 摘要提取提示词模板（存储在 metadata_json 中）
            "promptTemplate": (s.metadata_json or {}).get("prompt_template"),
        } for s in scenes
    ]}

@router.get("/scenes/{scene_id}", summary="获取场景详情")
async def get_scene(scene_id: int):
    scene = await SceneService.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {
        "scene_id": scene.scene_id,
        "scene_name": scene.scene_name,
        "scene_description": scene.scene_description,
        "scene_cover": scene.scene_cover,
        "asr_correct_lib_id": scene.asr_correct_lib_id,
        "sensitive_word_lib_id": scene.sensitive_word_lib_id,
        "dialog_round_limit": scene.dialog_round_limit,
        "end_speech": scene.end_speech,
        "modelName": scene.model_name,
        "systemPrompt": scene.system_prompt,
        "userPromptTemplate": scene.user_prompt_template,
        "enabled": scene.status == 1,
        "createBy": scene.create_by,
        "metadataJson": scene.metadata_json,
        "createdAt": scene.create_time.isoformat() if scene.create_time else None,
        "updatedAt": scene.update_time.isoformat() if scene.update_time else None,
        # 自由对练功能新增字段（使用驼峰命名）
        "practiceMode": scene.practice_mode,
        "knowledgeBase": scene.knowledge_base,
        "summaryText": scene.summary_text,
        "examCategories": scene.exam_categories,
        "scoringRules": scene.scoring_rules
    }

@router.post("/scenes", summary="创建场景")
async def create_scene(scene: SceneCreate):
    # Pydantic已通过alias将驼峰命名转换为下划线命名，直接传递即可
    result = await SceneService.create_scene(scene.dict())
    return {"message": "Scene created successfully", "scene_id": result.scene_id}

@router.put("/scenes/{scene_id}", summary="更新场景")
async def update_scene(scene_id: int, scene: SceneUpdate):
    # Pydantic已通过alias将驼峰命名转换为下划线命名，直接传递即可
    result = await SceneService.update_scene(scene_id, scene.dict(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {"message": "Scene updated successfully"}

@router.delete("/scenes/{scene_id}", summary="删除场景")
async def delete_scene(scene_id: int):
    result = await SceneService.delete_scene(scene_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {"message": "Scene deleted successfully"}

# ==================== 课程管理 APIs ====================

class CourseCreate(BaseModel):
    course_name: str
    course_type: Optional[int] = Field(default=1, alias="courseType")  # 1: 练习，2: 考试
    scene_id: Optional[int] = Field(default=None, alias="sceneId")
    simulated_role_id: Optional[int] = Field(default=None, alias="simulatedRoleId")
    practice_mode: Optional[str] = Field(default="text", alias="practiceMode")  # text/voice/call
    difficulty: Optional[int] = Field(default=None, alias="difficulty")
    total_score: Optional[int] = Field(default=100, alias="totalScore")
    passing_score: Optional[int] = Field(default=60, alias="passingScore")
    time_limit: Optional[int] = Field(default=None, alias="timeLimit")
    max_attempts: Optional[int] = Field(default=1, alias="maxAttempts")
    start_time: Optional[str] = Field(default=None, alias="startTime")
    end_time: Optional[str] = Field(default=None, alias="endTime")
    status: Optional[int] = Field(default=0, alias="status")  # 0: 未发布，1: 已发布，2: 已结束
    create_by: Optional[str] = None

    class Config:
        populate_by_name = True

class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    course_type: Optional[int] = Field(default=None, alias="courseType")
    scene_id: Optional[int] = Field(default=None, alias="sceneId")
    simulated_role_id: Optional[int] = Field(default=None, alias="simulatedRoleId")
    practice_mode: Optional[str] = Field(default=None, alias="practiceMode")
    difficulty: Optional[int] = Field(default=None, alias="difficulty")
    total_score: Optional[int] = Field(default=None, alias="totalScore")
    passing_score: Optional[int] = Field(default=None, alias="passingScore")
    time_limit: Optional[int] = Field(default=None, alias="timeLimit")
    max_attempts: Optional[int] = Field(default=None, alias="maxAttempts")
    start_time: Optional[str] = Field(default=None, alias="startTime")
    end_time: Optional[str] = Field(default=None, alias="endTime")
    status: Optional[int] = Field(default=None, alias="status")

    class Config:
        populate_by_name = True

def _course_to_dict(course, scene_map: dict = None):
    """将 CourseRow 转为前端驼峰命名 dict"""
    return {
        "courseId": course.course_id,
        "course_name": course.course_name,
        "courseType": course.course_type,
        "sceneId": course.scene_id,
        "sceneName": scene_map.get(course.scene_id) if scene_map and course.scene_id else None,
        "sceneDescription": scene_map.get(f"desc_{course.scene_id}") if scene_map and course.scene_id else None,
        "simulatedRoleId": course.simulated_role_id,
        "practiceMode": course.practice_mode,
        "difficulty": course.difficulty,
        "totalScore": course.total_score,
        "passingScore": course.passing_score,
        "timeLimit": course.time_limit,
        "maxAttempts": course.max_attempts,
        "startTime": course.start_time.isoformat() if course.start_time else None,
        "endTime": course.end_time.isoformat() if course.end_time else None,
        "status": course.status,
        "create_by": course.create_by,
        "createdAt": course.create_time.isoformat() if course.create_time else None,
    }

@router.get("/courses", summary="获取课程列表")
async def get_courses():
    courses = await CourseService.get_courses()
    scenes = await SceneService.get_scenes()
    scene_map = {}
    for s in scenes:
        scene_map[s.scene_id] = s.scene_name
        scene_map[f"desc_{s.scene_id}"] = s.scene_description
    return {"courses": [_course_to_dict(c, scene_map) for c in courses]}

@router.get("/courses/{course_id}", summary="获取课程详情")
async def get_course(course_id: int):
    course = await CourseService.get_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    scene = await SceneService.get_scene(course.scene_id) if course.scene_id else None
    result = _course_to_dict(course)
    if scene:
        result["sceneName"] = scene.scene_name
        result["sceneDescription"] = scene.scene_description
    return result

@router.post("/courses", summary="创建课程")
async def create_course(course: CourseCreate):
    result = await CourseService.create_course(course.dict())
    return {"message": "Course created successfully", "course_id": result.course_id}

@router.put("/courses/{course_id}", summary="更新课程")
async def update_course(course_id: int, course: CourseUpdate):
    result = await CourseService.update_course(course_id, course.dict(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course updated successfully"}

@router.delete("/courses/{course_id}", summary="删除课程")
async def delete_course(course_id: int):
    result = await CourseService.delete_course(course_id)
    if not result:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"message": "Course deleted successfully"}

# 提取摘要请求模型
class ExtractSummaryRequest(BaseModel):
    knowledgeBase: str = Field(description="知识库文本内容")
    promptTemplate: Optional[str] = Field(default=None, description="自定义提示词模板")
    modelName: Optional[str] = Field(default=None, description="大模型名称，为空则使用系统默认模型")

@router.post("/scenes/extract-summary", summary="提取摘要")
async def extract_summary(request: ExtractSummaryRequest):
    """使用大模型从知识库文本中提取摘要（直调大模型，不经过工作流）"""
    from deerflow.models import create_chat_model
    from langchain_core.messages import HumanMessage
    
    if not request.knowledgeBase or not request.knowledgeBase.strip():
        raise HTTPException(status_code=400, detail="知识库内容不能为空")
    
    # 使用默认模板或自定义模板
    default_template = """你是一位专业的内容分析师，擅长将非结构化文本转化为清晰的结构化笔记。

请阅读以下提供的文本，并根据其内容执行以下操作：
1.  **识别维度**：分析文本语义，自动归纳出文中的核心主题或分类维度（例如：产品特点、技术参数、市场表现、用户反馈等，具体维度由文本决定）。
2.  **提取要点**：在每个维度下，提取最关键的事实、数据、观点或结论。
3.  **精简表述**：去除口语化、废话和修饰性词语，保留核心信息。

**输出格式要求：**
- 采用"维度名称：要点详情"的格式。
- 每个维度单独一行。
- 如果同一维度有多个要点，请用逗号隔开。
- **仅输出结果**，不要包含解释、前言或后记。

**参考示例（仅供参考格式，不代表实际维度）：**
核心优势：零样本学习能力突出，推理效率高
应用场景：金融风控，智能客服，医疗影像分析
技术局限：长文本处理能力较弱，存在幻觉风险

**待处理文本：**
{{TEXT}}"""
    
    prompt = request.promptTemplate.replace("{{TEXT}}", request.knowledgeBase) if request.promptTemplate else default_template.replace("{{TEXT}}", request.knowledgeBase)
    
    try:
        # 归一化：空字符串/空白 视同未指定，使用系统默认第一个模型
        model_name = (request.modelName or None) and (request.modelName.strip() or None)

        # 使用场景指定的大模型，未指定则使用系统默认第一个模型
        try:
            llm = create_chat_model(
                name=model_name,
                thinking_enabled=False
            )
        except ValueError as ve:
            if "not found in config" in str(ve):
                # 指定模型名不在配置中，自动降级到系统默认第一个模型重试
                import logging
                logging.getLogger("roleplay").warning(
                    f"场景指定模型 '{model_name}' 不在 config 中，已自动切换为默认模型"
                )
                llm = create_chat_model(name=None, thinking_enabled=False)
            else:
                raise
        
        # 调用大模型
        response = await llm.agenerate([[HumanMessage(content=prompt)]])
        
        # 解析响应
        if response and response.generations and response.generations[0]:
            summary_text = response.generations[0][0].text.strip()
            
            # 清理可能的markdown格式
            if summary_text.startswith("```"):
                summary_text = summary_text[3:]
                if summary_text.endswith("```"):
                    summary_text = summary_text[:-3]
            summary_text = summary_text.strip()
            
            return {
                "success": True,
                "summaryText": summary_text,
                "categories": parse_summary_categories(summary_text)
            }
        else:
            return {"success": False, "message": "大模型返回为空"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调用大模型失败: {str(e)}")

def parse_summary_categories(summary_text: str) -> list:
    """解析摘要文本，提取分类列表"""
    categories = []
    lines = summary_text.split('\n')
    for line in lines:
        line = line.strip()
        if line and ':' in line:
            parts = line.split(':', 1)
            if len(parts) == 2:
                categories.append(parts[0].strip())
    return categories

@router.get("/evaluations", summary="获取评估列表")
async def get_evaluations(thread_id: Optional[str] = None, user_id: Optional[str] = None):
    evaluations = await EvaluationService.get_evaluations(thread_id, user_id)
    return {"evaluations": [
        {
            "id": e.id,
            "thread_id": e.thread_id,
            "run_id": e.run_id,
            "scene_id": e.scene_id,
            "user_id": e.user_id,
            "round_number": e.round_number,
            "total_score": e.total_score,
            "dimension_scores": e.dimension_scores,
            "strengths": e.strengths,
            "improvements": e.improvements,
            "summary": e.summary,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None
        } for e in evaluations
    ]}

@router.get("/evaluations/{eval_id}", summary="获取评估详情")
async def get_evaluation(eval_id: str):
    evaluation = await EvaluationService.get_evaluation(eval_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return {
        "id": evaluation.id,
        "thread_id": evaluation.thread_id,
        "run_id": evaluation.run_id,
        "scene_id": evaluation.scene_id,
        "user_id": evaluation.user_id,
        "round_number": evaluation.round_number,
        "total_score": evaluation.total_score,
        "dimension_scores": evaluation.dimension_scores,
        "strengths": evaluation.strengths,
        "improvements": evaluation.improvements,
        "summary": evaluation.summary,
        "status": evaluation.status,
        "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None
    }

@router.post("/evaluations", summary="创建评估")
async def create_evaluation(evaluation: EvaluationCreate):
    result = await EvaluationService.create_evaluation(evaluation.dict())
    return {"message": "Evaluation created successfully", "evaluation_id": result.id}

@router.put("/evaluations/{eval_id}", summary="更新评估")
async def update_evaluation(eval_id: str, evaluation: EvaluationUpdate):
    result = await EvaluationService.update_evaluation(eval_id, evaluation.dict(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return {"message": "Evaluation updated successfully"}

@router.get("/practice-records", summary="获取练习记录列表")
async def get_practice_records(
    user_name: Optional[str] = None, 
    course_id: Optional[int] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    records = await PracticeRecordService.get_practice_records(user_name, course_id, start_time, end_time, status, page, page_size)
    return {"records": [
        {
            "recordId": r["record_id"],
            "courseId": r["course_id"],
            "userName": r["user_name"],
            "totalScore": r["total_score"],
            "courseName": r["course_name"],
            "sceneName": r["scene_name"],
            "startTime": r["start_time"],
            "endTime": r["end_time"],
            "summary": r.get("summary"),
            "practiceMode": r.get("practice_mode"),
            "accordFinish": r.get("accord_finish"),
        } for r in records
    ]}

@router.get("/practice-records/{record_id}", summary="获取练习记录详情")
async def get_practice_record(record_id: int):
    record = await PracticeRecordService.get_practice_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Practice record not found")
    return {
        "recordId": record.record_id,
        "courseId": record.course_id,
        "userName": record.user_name,
        "totalScore": record.total_score,
        "duration": record.duration,
        "dialogRounds": record.dialog_rounds,
        "reportData": record.report_data,
        "startTime": record.start_time.isoformat() if record.start_time else None,
        "endTime": record.end_time.isoformat() if record.end_time else None,
    }

class PracticeRecordCreate(BaseModel):
    course_id: int = Field(alias="courseId")
    user_name: str = Field(alias="userName")

    model_config = {"populate_by_name": True}

@router.post("/practice-records", summary="创建练习记录")
async def create_practice_record(req: PracticeRecordCreate):
    result = await PracticeRecordService.create_practice_record({
        "course_id": req.course_id,
        "user_name": req.user_name,
    })
    return {"message": "Practice record created successfully", "recordId": result.record_id}

@router.post("/practice-records/{record_id}/complete", summary="完成练习记录")
async def complete_practice_record(record_id: int, data: PracticeRecordComplete):
    result = await PracticeRecordService.complete_practice_record(record_id, data.model_dump())
    if not result:
        raise HTTPException(status_code=404, detail="Practice record not found")
    return {"message": "Practice record completed successfully"}

@router.get("/statistics/user/{user_id}", summary="获取用户统计")
async def get_user_statistics(user_id: str):
    stats = await StatisticsService.get_user_stats(user_id)
    if not stats:
        return {"total_practices": 0, "total_duration": 0, "avg_score": 0}
    return {
        "total_practices": stats.total_practices or 0,
        "total_duration": stats.total_duration or 0,
        "avg_score": stats.avg_score or 0
    }

@router.get("/statistics/scenes", summary="获取场景统计")
async def get_scene_statistics(scene_id: Optional[str] = None):
    stats = await StatisticsService.get_scene_stats(scene_id)
    return {"scene_stats": [
        {
            "scene_id": s.scene_id,
            "practice_count": s.practice_count or 0,
            "avg_score": s.avg_score or 0
        } for s in stats
    ]}

@router.get("/statistics/leaderboard", summary="获取排行榜")
async def get_leaderboard(limit: Optional[int] = 10):
    leaderboard = await StatisticsService.get_leaderboard(limit)
    return {"leaderboard": [
        {
            "user_id": l.user_id,
            "practice_count": l.practice_count or 0,
            "avg_score": round(l.avg_score, 2) if l.avg_score else 0
        } for l in leaderboard
    ]}

# ==================== Authentication APIs ====================

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/auth/login", summary="用户登录")
async def login(request: LoginRequest):
    result = await AuthService.login(request.username, request.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    return result

@router.get("/auth/user/{user_id}", summary="获取用户信息")
async def get_user_info(user_id: int):
    result = await AuthService.get_user_info(user_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

@router.post("/auth/logout", summary="用户退出登录")
async def logout():
    return {"success": True, "message": "退出登录成功"}

@router.get("/auth/me", summary="获取当前用户信息")
async def get_current_user(user_id: int):
    result = await AuthService.get_user_info(user_id)
    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])
    return result

# ==================== 自由式对练 APIs ====================

class PracticeStartRequest(BaseModel):
    course_id: int = Field(alias="courseId")
    user_name: str = Field(alias="userName")

    model_config = {"populate_by_name": True}

class PracticeTurnRequest(BaseModel):
    record_id: int = Field(alias="recordId")
    message: str

    model_config = {"populate_by_name": True}

class PracticeEndRequest(BaseModel):
    record_id: int = Field(alias="recordId")

    model_config = {"populate_by_name": True}

@router.post("/practice/start", summary="开始对练")
async def practice_start(req: PracticeStartRequest):
    """加载场景 → 创建记录 → LLM生成开场白"""
    try:
        result = await PracticeService.start(req.course_id, req.user_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/practice/turn", summary="对练对话轮次")
async def practice_turn(req: PracticeTurnRequest):
    """存用户话术 → LLM评估 → LLM生成下一条客户回复"""
    try:
        result = await PracticeService.turn(req.record_id, req.message)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/practice/end", summary="结束对练")
async def practice_end(req: PracticeEndRequest):
    """手动结束 → LLM生成最终报告"""
    try:
        result = await PracticeService.end(req.record_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/practice/{record_id}/history", summary="获取对练历史")
async def practice_history(record_id: int):
    try:
        return await PracticeService.get_practice_history(record_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/practice/{record_id}/suggestions/{dialog_id}", summary="获取详细评价建议")
async def get_practice_suggestions(record_id: int, dialog_id: int):
    """
    获取指定对话的详细评价建议（包括改进建议列表和润色表达）
    - 与对话轮次分开返回，不影响主要流转速度
    - 用户点击"改进建议"按钮时调用此接口
    """
    try:
        return await PracticeService.get_detailed_suggestions(record_id, dialog_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/practice/{record_id}/report", summary="获取评估报告")
async def practice_report(record_id: int):
    try:
        return await PracticeService.get_report(record_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/practice/{record_id}/report/regenerate", summary="重新生成评估报告")
async def regenerate_practice_report(record_id: int):
    """重新生成评估报告（用于调试）"""
    try:
        return await PracticeService.regenerate_report(record_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # 捕获其他所有异常，返回更详细的错误信息
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"重新生成报告时发生未知错误，record_id={record_id}，错误：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(e)}")


@router.get("/practice/{record_id}/inspiration", summary="生成对话灵感")
async def generate_practice_inspiration(record_id: int):
    """
    根据当前对话历史生成对话灵感（知识点提示）
    - 用户在练习过程中点击灵感按钮时调用此接口
    - 根据场景知识库和当前对话生成相关知识点提示
    """
    try:
        return await PracticeService.generate_inspiration(record_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"生成灵感失败，record_id={record_id}，错误：{str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器内部错误：{str(e)}")