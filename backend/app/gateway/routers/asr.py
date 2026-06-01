"""ASR API router for speech recognition using FunASR."""

import asyncio
import logging
import time
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/asr", tags=["ASR"])

# 模拟任务存储（生产环境应使用Redis或数据库）
asr_tasks = {}


class ASRTranscribeRequest(BaseModel):
    """Request model for ASR transcription."""
    
    model: str = Field(description="ASR model to use", default="fun-asr")
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
    Submit an audio file for transcription using FunASR.
    
    Args:
        request: ASR transcription request containing audio URL and options
        
    Returns:
        ASRSubmitResponse: Task submission result with task ID
    """
    task_id = str(uuid4())
    
    # 初始化任务状态
    asr_tasks[task_id] = {
        "status": "pending",
        "text": "",
        "audio_url": request.audio_url,
        "language": request.language,
        "model": request.model
    }
    
    # 异步处理转写（模拟FunASR调用）
    asyncio.create_task(process_asr_task(task_id))
    
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


async def process_asr_task(task_id: str):
    """
    Process ASR transcription task asynchronously.
    Simulates FunASR API call with delay.
    """
    task = asr_tasks.get(task_id)
    if not task:
        return
    
    # 模拟处理延迟（2-5秒）
    task["status"] = "processing"
    await asyncio.sleep(3 + time.time() % 3)  # 2-5秒随机延迟
    
    # 模拟FunASR转写结果
    # 在实际实现中，这里应该调用FunASR API
    # 例如：使用funasr-sdk或通过HTTP调用FunASR服务
    
    # 模拟转写文本（根据语言返回不同内容）
    if task["language"] == "zh":
        # 模拟中文转写结果
        task["text"] = "你好，我是客服小林，很高兴为你服务。请问有什么可以帮助你的吗？"
    else:
        task["text"] = "Hello, this is customer service. How can I help you?"
    
    task["status"] = "completed"
    
    # 清理：任务完成后30秒删除（可选）
    asyncio.create_task(cleanup_task(task_id, delay=30))


async def cleanup_task(task_id: str, delay: int = 30):
    """Clean up completed task after delay."""
    await asyncio.sleep(delay)
    asr_tasks.pop(task_id, None)
