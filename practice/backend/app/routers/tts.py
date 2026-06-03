"""TTS API 路由 — 语音合成（DashScope Qwen3-TTS-Flash）"""

import asyncio
import logging
from uuid import uuid4

import dashscope
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_config
from app.oss_upload import generate_filename, upload_file_to_oss

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["TTS"])

tts_tasks = {}


class TTSSynthesizeRequest(BaseModel):
    text: str = Field(description="Text to synthesize")
    model: str = Field(description="TTS model to use", default="qwen3-tts-flash")
    voice: str = Field(description="Voice name", default="Cherry")
    language: str = Field(description="Language code", default="zh")


class TTSSubmitResponse(BaseModel):
    success: bool = Field(description="Whether the task was submitted successfully")
    task_id: str = Field(description="Task ID for querying results")


class TTSQueryResponse(BaseModel):
    task_id: str = Field(description="Task ID")
    status: str = Field(description="Task status: pending, processing, completed, failed")
    audio_url: str = Field(description="URL of synthesized audio file", default="")
    message: str = Field(description="Status message", default="")


@router.post("/synthesize", response_model=TTSSubmitResponse)
async def submit_synthesize(request: TTSSynthesizeRequest) -> TTSSubmitResponse:
    config = get_config().dashscope

    if not config.is_configured():
        raise HTTPException(
            status_code=500,
            detail="DashScope not configured. Please set api_key in config.yaml."
        )

    dashscope.api_key = config.resolved_api_key
    dashscope.base_http_api_url = config.base_url

    task_id = str(uuid4())

    tts_tasks[task_id] = {
        "status": "pending",
        "audio_url": "",
        "text": request.text,
        "voice": request.voice,
        "language": request.language,
        "model": request.model
    }

    asyncio.create_task(process_tts_task(task_id, request.text, request.model, request.voice, request.language))

    return TTSSubmitResponse(success=True, task_id=task_id)


@router.get("/query/{task_id}", response_model=TTSQueryResponse)
async def query_synthesize(task_id: str) -> TTSQueryResponse:
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
    task = tts_tasks.get(task_id)
    if not task:
        return

    config = get_config()
    dashscope.api_key = config.dashscope.resolved_api_key
    dashscope.base_http_api_url = config.dashscope.base_url

    task["status"] = "processing"

    try:
        response = dashscope.MultiModalConversation.call(
            model=model,
            text=text,
            voice=voice,
            language_type="Chinese" if language == "zh" else language,
            stream=False
        )

        if response.status_code != 200:
            raise Exception(f"DashScope TTS API error: {response.message}")

        audio_url = response.output.audio.url

        async with httpx.AsyncClient() as client:
            audio_response = await client.get(audio_url)
            if audio_response.status_code != 200:
                raise Exception(f"Failed to download audio from DashScope: {audio_response.status_code}")

            audio_data = audio_response.content

            oss_config = config.oss
            if oss_config.is_configured():
                filename = generate_filename(f"ai_{task_id[:8]}.mp3")
                oss_url = await upload_file_to_oss(
                    file_data=audio_data,
                    filename=filename,
                    content_type="audio/mpeg"
                )
                task["audio_url"] = oss_url
            else:
                task["audio_url"] = audio_url

        task["status"] = "completed"
        logger.info(f"TTS synthesis completed for task {task_id}")

    except Exception as e:
        task["status"] = "failed"
        task["audio_url"] = ""
        logger.error(f"TTS synthesis failed for task {task_id}: {e}")

    asyncio.create_task(cleanup_tts_task(task_id, delay=30))


async def cleanup_tts_task(task_id: str, delay: int = 30):
    await asyncio.sleep(delay)
    tts_tasks.pop(task_id, None)
