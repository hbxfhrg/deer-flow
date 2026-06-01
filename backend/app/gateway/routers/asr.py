"""ASR API router for speech recognition using DashScope FunASR."""

import asyncio
import logging
import time
from uuid import uuid4

import dashscope
from dashscope.audio.asr import Transcription
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from deerflow.config.app_config import get_app_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/asr", tags=["ASR"])

# 模拟任务存储（生产环境应使用Redis或数据库）
asr_tasks = {}


class ASRTranscribeRequest(BaseModel):
    """Request model for ASR transcription."""
    
    model: str = Field(description="ASR model to use", default="paraformer-v2")
    audio_url: str = Field(description="URL of audio file to transcribe")
    language: str = Field(description="Language code", default="zh")


class ASRSubmitResponse(BaseModel):
    """Response model for submit transcription task."""
    
    success: bool = Field(description="Whether the task was submitted successfully")
    task_id: str = Field(description="Task ID for querying results")


class ASRQueryResponse(BaseModel):
    """Response model for query transcription result."""
    
    task_id: str = Field(description="Task ID")
    status: str = Field(description="Task status: pending, processing, completed, failed")
    text: str = Field(description="Transcribed text (empty if not completed)", default="")
    message: str = Field(description="Status message", default="")


@router.post("/transcribe", response_model=ASRSubmitResponse)
async def submit_transcribe(request: ASRTranscribeRequest) -> ASRSubmitResponse:
    """
    Submit an audio file for transcription using DashScope FunASR.
    
    Args:
        request: ASR transcription request containing audio URL and options
        
    Returns:
        ASRSubmitResponse: Task submission result with task ID
    """
    config = get_app_config().dashscope
    
    if not config.is_configured():
        raise HTTPException(
            status_code=500,
            detail="DashScope not configured. Please set DASHSCOPE_API_KEY in config.yaml or environment variables."
        )
    
    # 设置DashScope API Key
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    
    task_id = str(uuid4())
    
    # 初始化任务状态
    asr_tasks[task_id] = {
        "status": "pending",
        "text": "",
        "audio_url": request.audio_url,
        "language": request.language,
        "model": request.model
    }
    
    # 异步处理转写
    asyncio.create_task(process_asr_task(task_id, request.audio_url, request.model))
    
    return ASRSubmitResponse(
        success=True,
        task_id=task_id
    )


@router.get("/query/{task_id}", response_model=ASRQueryResponse)
async def query_transcribe(task_id: str) -> ASRQueryResponse:
    """
    Query the status and result of a transcription task.
    
    Args:
        task_id: ID of the transcription task
        
    Returns:
        ASRQueryResponse: Task status and transcribed text
    """
    task = asr_tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return ASRQueryResponse(
        task_id=task_id,
        status=task["status"],
        text=task["text"],
        message="Processing..." if task["status"] != "completed" else "Transcription completed"
    )


async def process_asr_task(task_id: str, audio_url: str, model: str):
    """
    Process ASR transcription task asynchronously using DashScope API.
    """
    task = asr_tasks.get(task_id)
    if not task:
        return
    
    config = get_app_config().dashscope
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    
    # 更新状态为处理中
    task["status"] = "processing"
    
    try:
        # 调用DashScope FunASR API
        # 使用异步方式提交转写任务
        task_response = Transcription.async_call(
            model=model,
            file_urls=[audio_url]
        )
        
        if task_response.status_code != 200:
            raise Exception(f"DashScope API error: {task_response.message}")
        
        # 等待转写完成
        transcription_response = Transcription.wait(task=task_response.output.task_id)
        
        if transcription_response.status_code != 200:
            raise Exception(f"Transcription failed: {transcription_response.message}")
        
        # 获取转写结果
        results = transcription_response.output.get('results', [])
        if results:
            # 从第一个结果中提取转写文本
            result = results[0]
            transcripts = result.get('transcripts', [])
            if transcripts:
                # 合并所有句子
                full_text = ' '.join([t.get('text', '') for t in transcripts])
                task["text"] = full_text
            else:
                task["text"] = ""
        else:
            task["text"] = ""
        
        task["status"] = "completed"
        logger.info(f"ASR transcription completed for task {task_id}")
        
    except Exception as e:
        task["status"] = "failed"
        task["text"] = ""
        logger.error(f"ASR transcription failed for task {task_id}: {e}")
    
    # 清理：任务完成后30秒删除（可选）
    asyncio.create_task(cleanup_task(task_id, delay=30))


async def cleanup_task(task_id: str, delay: int = 30):
    """Clean up completed task after delay."""
    await asyncio.sleep(delay)
    asr_tasks.pop(task_id, None)