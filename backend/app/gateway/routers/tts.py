"""TTS API router for text-to-speech using DashScope Qwen3-TTS-Flash."""

import asyncio
import logging
import time
from uuid import uuid4

import dashscope
import httpx
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
    voice: str = Field(description="Voice name", default="Cherry")
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
    Submit text for synthesis using DashScope Qwen3-TTS-Flash.
    
    Args:
        request: TTS synthesis request containing text and options
        
    Returns:
        TTSSubmitResponse: Task submission result with task ID
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
    tts_tasks[task_id] = {
        "status": "pending",
        "audio_url": "",
        "text": request.text,
        "voice": request.voice,
        "language": request.language,
        "model": request.model
    }
    
    # 异步处理合成
    asyncio.create_task(process_tts_task(task_id, request.text, request.model, request.voice, request.language))
    
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


async def process_tts_task(task_id: str, text: str, model: str, voice: str, language: str):
    """
    Process TTS synthesis task asynchronously using DashScope API.
    """
    task = tts_tasks.get(task_id)
    if not task:
        return
    
    config = get_app_config().dashscope
    dashscope.api_key = config.api_key
    dashscope.base_http_api_url = config.base_url
    
    # 更新状态为处理中
    task["status"] = "processing"
    
    try:
        # 调用DashScope Qwen3-TTS-Flash API
        response = dashscope.MultiModalConversation.call(
            model=model,
            text=text,
            voice=voice,
            language_type="Chinese" if language == "zh" else language,
            stream=False
        )
        
        if response.status_code != 200:
            raise Exception(f"DashScope TTS API error: {response.message}")
        
        # 获取音频URL
        audio_url = response.output.audio.url
        
        # 下载音频并上传到OSS
        async with httpx.AsyncClient() as client:
            audio_response = await client.get(audio_url)
            if audio_response.status_code != 200:
                raise Exception(f"Failed to download audio from DashScope: {audio_response.status_code}")
            
            audio_data = audio_response.content
            
            # 上传到OSS
            oss_config = get_app_config().oss
            if oss_config.is_configured():
                filename = generate_filename(f"ai_{task_id[:8]}.mp3")
                oss_url = await upload_file_to_oss(
                    file_data=audio_data,
                    filename=filename,
                    content_type="audio/mpeg"
                )
                task["audio_url"] = oss_url
            else:
                # OSS未配置，直接使用DashScope返回的URL
                task["audio_url"] = audio_url
        
        task["status"] = "completed"
        logger.info(f"TTS synthesis completed for task {task_id}")
        
    except Exception as e:
        task["status"] = "failed"
        task["audio_url"] = ""
        logger.error(f"TTS synthesis failed for task {task_id}: {e}")
    
    # 清理：任务完成后30秒删除（可选）
    asyncio.create_task(cleanup_tts_task(task_id, delay=30))


async def cleanup_tts_task(task_id: str, delay: int = 30):
    """Clean up completed task after delay."""
    await asyncio.sleep(delay)
    tts_tasks.pop(task_id, None)