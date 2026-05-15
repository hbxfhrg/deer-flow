from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from deerflow.roleplay import get_db
from deerflow.roleplay.services import SceneService, EvaluationService, PracticeRecordService, StatisticsService

router = APIRouter(prefix="/api/roleplay", tags=["roleplay"])

class SceneCreate(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = ""
    difficulty: Optional[str] = "medium"
    rounds: Optional[int] = 5
    time_per_round: Optional[int] = 120
    total_time_limit: Optional[int] = 600
    model_name: Optional[str] = "gpt-4o-mini"
    system_prompt: Optional[str] = ""
    user_prompt_template: Optional[str] = ""
    enabled: Optional[bool] = True
    metadata_json: Optional[Dict] = {}

class SceneUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    difficulty: Optional[str] = None
    rounds: Optional[int] = None
    time_per_round: Optional[int] = None
    total_time_limit: Optional[int] = None
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    enabled: Optional[bool] = None
    metadata_json: Optional[Dict] = None

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
            "id": s.id,
            "name": s.name,
            "description": s.description,
            "difficulty": s.difficulty,
            "rounds": s.rounds,
            "time_per_round": s.time_per_round,
            "total_time_limit": s.total_time_limit,
            "model_name": s.model_name,
            "enabled": s.enabled,
            "created_at": s.created_at.isoformat() if s.created_at else None
        } for s in scenes
    ]}

@router.get("/scenes/{scene_id}", summary="获取场景详情")
async def get_scene(scene_id: str):
    scene = await SceneService.get_scene(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {
        "id": scene.id,
        "name": scene.name,
        "description": scene.description,
        "difficulty": scene.difficulty,
        "rounds": scene.rounds,
        "time_per_round": scene.time_per_round,
        "total_time_limit": scene.total_time_limit,
        "model_name": scene.model_name,
        "system_prompt": scene.system_prompt,
        "user_prompt_template": scene.user_prompt_template,
        "enabled": scene.enabled,
        "metadata_json": scene.metadata_json,
        "created_at": scene.created_at.isoformat() if scene.created_at else None,
        "updated_at": scene.updated_at.isoformat() if scene.updated_at else None
    }

@router.post("/scenes", summary="创建场景")
async def create_scene(scene: SceneCreate):
    result = await SceneService.create_scene(scene.dict())
    return {"message": "Scene created successfully", "scene_id": result.id}

@router.put("/scenes/{scene_id}", summary="更新场景")
async def update_scene(scene_id: str, scene: SceneUpdate):
    result = await SceneService.update_scene(scene_id, scene.dict(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {"message": "Scene updated successfully"}

@router.delete("/scenes/{scene_id}", summary="删除场景")
async def delete_scene(scene_id: str):
    result = await SceneService.delete_scene(scene_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scene not found")
    return {"message": "Scene deleted successfully"}

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