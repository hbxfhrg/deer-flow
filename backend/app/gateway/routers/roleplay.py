from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from deerflow.roleplay import get_db
from deerflow.roleplay.services import SceneService, EvaluationService, PracticeRecordService, StatisticsService
from deerflow.roleplay.auth_service import AuthService

router = APIRouter(prefix="/api/roleplay", tags=["roleplay"])

class SceneCreate(BaseModel):
    scene_id: Optional[int] = None
    scene_name: str
    scene_description: Optional[str] = ""
    difficulty: Optional[str] = "简单"
    rounds: Optional[int] = 5
    time_per_round: Optional[int] = Field(default=120, alias="timePerRound")
    total_time_limit: Optional[int] = Field(default=600, alias="totalTimeLimit")
    model_name: Optional[str] = "gpt-4o-mini"
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

    class Config:
        populate_by_name = True

class SceneUpdate(BaseModel):
    scene_name: Optional[str] = None
    scene_description: Optional[str] = None
    difficulty: Optional[str] = None
    rounds: Optional[int] = None
    time_per_round: Optional[int] = Field(default=None, alias="timePerRound")
    total_time_limit: Optional[int] = Field(default=None, alias="totalTimeLimit")
    model_name: Optional[str] = None
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
    completed_rounds: int
    avg_score: int
    metadata_json: Optional[Dict] = {}

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
            "difficulty": s.difficulty,
            "rounds": s.rounds,
            "timePerRound": s.time_per_round,
            "totalTimeLimit": s.total_time_limit,
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
            "scoringRules": s.scoring_rules
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
        "difficulty": scene.difficulty,
        "rounds": scene.rounds,
        "timePerRound": scene.time_per_round,
        "totalTimeLimit": scene.total_time_limit,
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

# 提取摘要请求模型
class ExtractSummaryRequest(BaseModel):
    knowledgeBase: str = Field(description="知识库文本内容")
    promptTemplate: Optional[str] = Field(default=None, description="自定义提示词模板")

@router.post("/scenes/extract-summary", summary="提取摘要")
async def extract_summary(request: ExtractSummaryRequest):
    """使用大模型从知识库文本中提取摘要（直调大模型，不经过工作流）"""
    from deerflow.models import create_chat_model
    from langchain_core.messages import HumanMessage
    
    if not request.knowledgeBase or not request.knowledgeBase.strip():
        raise HTTPException(status_code=400, detail="知识库内容不能为空")
    
    # 使用默认模板或自定义模板
    default_template = """请对以下文本进行分析，提取关键信息：

1. 识别文本中的主要分类（如产品介绍、客户需求、销售策略等）
2. 提取每个分类下的关键要点
3. 按照指定格式输出

输出格式要求：
- 每行一个分类:要点
- 分类和要点之间用英文冒号:分隔
- 分类尽量简洁（2-4个汉字）
- 要点描述清晰准确

文本内容：
{{TEXT}}"""
    
    prompt = request.promptTemplate.replace("{{TEXT}}", request.knowledgeBase) if request.promptTemplate else default_template.replace("{{TEXT}}", request.knowledgeBase)
    
    try:
        # 直接创建大模型实例，不经过工作流
        llm = create_chat_model(
            name="gpt-4o-mini",
            thinking_enabled=False
        )
        
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
async def get_practice_records(user_id: Optional[str] = None, scene_id: Optional[str] = None):
    records = await PracticeRecordService.get_practice_records(user_id, scene_id)
    return {"records": [
        {
            "id": r.id,
            "thread_id": r.thread_id,
            "scene_id": r.scene_id,
            "user_id": r.user_id,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
            "total_rounds": r.total_rounds,
            "completed_rounds": r.completed_rounds,
            "avg_score": r.avg_score,
            "status": r.status,
            "metadata_json": r.metadata_json
        } for r in records
    ]}

@router.get("/practice-records/{record_id}", summary="获取练习记录详情")
async def get_practice_record(record_id: str):
    record = await PracticeRecordService.get_practice_record(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Practice record not found")
    return {
        "id": record.id,
        "thread_id": record.thread_id,
        "scene_id": record.scene_id,
        "user_id": record.user_id,
        "start_time": record.start_time.isoformat() if record.start_time else None,
        "end_time": record.end_time.isoformat() if record.end_time else None,
        "total_rounds": record.total_rounds,
        "completed_rounds": record.completed_rounds,
        "avg_score": record.avg_score,
        "status": record.status,
        "metadata_json": record.metadata_json
    }

@router.post("/practice-records", summary="创建练习记录")
async def create_practice_record(record: PracticeRecordCreate):
    result = await PracticeRecordService.create_practice_record(record.dict())
    return {"message": "Practice record created successfully", "record_id": result.id}

@router.post("/practice-records/{record_id}/complete", summary="完成练习记录")
async def complete_practice_record(record_id: str, data: PracticeRecordComplete):
    result = await PracticeRecordService.complete_practice_record(record_id, data.dict())
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