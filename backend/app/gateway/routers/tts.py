"""TTS API router for text-to-speech using Qwen3-TTS-Flash."""

import asyncio
import logging
import time
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from deerflow.config.app_config import get_app_config
from deerflow.utils.oss_upload import generate_filename, upload_file_to_oss

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["TTS"])

# 模拟任务存储（生产环境应使用Redis或数据库）
tts_tasks = {}


class TTSSynthesizeRequest(BaseModel):
    """Request model for TTS synthesis."""
    
    text: str = Field(description="Text to synthesize")
    model: str = Field(description="TTS model to use", default="qwen3-tts-flash")
    voice: str = Field(description="Voice name", default="zh-female")
    language: str = Field(description="Language code", default="zh")


class TTSSubmitResponse(BaseModel):
    """Response model for submit TTS task."""
    
    success: bool = Field(description="Whether the task was submitted successfully")
    task_id: str = Field(description="Task ID for querying results")


class TTSQueryResponse(BaseModel):
    """Response model for query TTS result."""
    
    task_id: str = Field(description="Task ID")
    status: str = Field(description="Task status: pending, processing, completed, failed")
    audio_url: str = Field(description="URL of synthesized audio file", default="")
    message: str = Field(description="Status message", default="")


@router.post("/synthesize", response_model=TTSSubmitResponse)
async def submit_synthesize(request: TTSSynthesizeRequest) -> TTSSubmitResponse:
    """
    Submit text for synthesis using Qwen3-TTS-Flash.
    
    Args:
        request: TTS synthesis request containing text and options
        
    Returns:
        TTSSubmitResponse: Task submission result with task ID
    """
    task_id = str(uuid4())
    
    # 初始化任务状态
    tts_tasks[task_id] = {
        "status": "pending",
        "audio_url": "",
        "text": request.text,
        "voice": request.voice,
        "language": request.language,
        "model": request.model
    }
    
    # 异步处理合成
    asyncio.create_task(process_tts_task(task_id))
    
    return TTSSubmitResponse(
        success=True,
        task_id=task_id
    )


@router.get("/query/{task_id}", response_model=TTSQueryResponse)
async def query_synthesize(task_id: str) -> TTSQueryResponse:
    """
    Query the status and result of a TTS synthesis task.
    
    Args:
        task_id: ID of the TTS task
        
    Returns:
        TTSQueryResponse: Task status and audio URL
    """
    task = tts_tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TTSQueryResponse(
        task_id=task_id,
        status=task["status"],
        audio_url=task["audio_url"],
        message="Processing..." if task["status"] != "completed" else "Synthesis completed"
    )


async def process_tts_task(task_id: str):
    """
    Process TTS synthesis task asynchronously.
    Simulates Qwen3-TTS-Flash API call with delay.
    """
    task = tts_tasks.get(task_id)
    if not task:
        return
    
    # 模拟处理延迟（1-3秒）
    task["status"] = "processing"
    await asyncio.sleep(1 + time.time() % 2)  # 1-3秒随机延迟
    
    try:
        # 模拟生成音频文件（实际实现中应调用Qwen3-TTS-Flash API）
        # 这里生成一个模拟的音频URL
        
        # 在实际实现中，应该：
        # 1. 调用Qwen3-TTS-Flash API生成音频
        # 2. 获取音频数据
        # 3. 上传到OSS
        # 4. 返回OSS URL
        
        # 模拟：生成一个模拟的音频URL
        config = get_app_config().oss
        if config.is_configured():
            # 如果OSS已配置，生成一个带时间戳的URL
            audio_url = f"{config.bucket_host}/voice/ai_{task_id[:8]}_{int(time.time())}.mp3"
        else:
            # OSS未配置，返回模拟URL
            audio_url = f"https://example.com/voice/ai_{task_id[:8]}.mp3"
        
        task["audio_url"] = audio_url
        task["status"] = "completed"
        
        logger.info(f"TTS synthesis completed for task {task_id}")
        
    except Exception as e:
        task["status"] = "failed"
        logger.error(f"TTS synthesis failed for task {task_id}: {e}")
    
    # 清理：任务完成后30秒删除（可选）
    asyncio.create_task(cleanup_tts_task(task_id, delay=30))


async def cleanup_tts_task(task_id: str, delay: int = 30):
    """Clean up completed task after delay."""
    await asyncio.sleep(delay)
    tts_tasks.pop(task_id, None)
