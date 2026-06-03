"""ASR API 路由 — 语音识别（DashScope FunASR）"""

import asyncio
import logging
from uuid import uuid4

import dashscope
from dashscope.audio.asr import Transcription
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/asr", tags=["ASR"])

asr_tasks = {}


class ASRTranscribeRequest(BaseModel):
    model: str = Field(description="ASR model to use", default="paraformer-v2")
    audio_url: str = Field(description="URL of audio file to transcribe")
    language: str = Field(description="Language code", default="zh")


class ASRSubmitResponse(BaseModel):
    success: bool = Field(description="Whether the task was submitted successfully")
    task_id: str = Field(description="Task ID for querying results")


class ASRQueryResponse(BaseModel):
    task_id: str = Field(description="Task ID")
    status: str = Field(description="Task status: pending, processing, completed, failed")
    text: str = Field(description="Transcribed text", default="")
    message: str = Field(description="Status message", default="")


@router.post("/transcribe", response_model=ASRSubmitResponse)
async def submit_transcribe(request: ASRTranscribeRequest) -> ASRSubmitResponse:
    config = get_config().dashscope

    if not config.is_configured():
        raise HTTPException(
            status_code=500,
            detail="DashScope not configured. Please set api_key in config.yaml."
        )

    dashscope.api_key = config.resolved_api_key
    dashscope.base_http_api_url = config.base_url

    task_id = str(uuid4())

    asr_tasks[task_id] = {
        "status": "pending",
        "text": "",
        "audio_url": request.audio_url,
        "language": request.language,
        "model": request.model
    }

    asyncio.create_task(process_asr_task(task_id, request.audio_url, request.model))

    return ASRSubmitResponse(success=True, task_id=task_id)


@router.get("/query/{task_id}", response_model=ASRQueryResponse)
async def query_transcribe(task_id: str) -> ASRQueryResponse:
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
    task = asr_tasks.get(task_id)
    if not task:
        return

    config = get_config()
    dashscope.api_key = config.dashscope.resolved_api_key
    dashscope.base_http_api_url = config.dashscope.base_url

    task["status"] = "processing"

    try:
        task_response = Transcription.async_call(
            model=model,
            file_urls=[audio_url]
        )

        if task_response.status_code != 200:
            raise Exception(f"DashScope API error: {task_response.message}")

        transcription_response = Transcription.wait(task=task_response.output.task_id)

        if transcription_response.status_code != 200:
            raise Exception(f"Transcription failed: {transcription_response.message}")

        results = transcription_response.output.get('results', [])
        logger.info(f"ASR raw response: {transcription_response.output}")

        if results:
            result = results[0]
            transcription_url = result.get('transcription_url')
            logger.info(f"Transcription URL: {transcription_url}")

            if transcription_url:
                try:
                    import urllib.request
                    import json
                    with urllib.request.urlopen(transcription_url) as response:
                        transcription_data = response.read().decode('utf-8')
                        transcription_json = json.loads(transcription_data)
                        logger.info(f"Downloaded transcription data: {transcription_json}")

                        transcripts = transcription_json.get('transcripts', [])
                        if transcripts:
                            full_text = ' '.join([t.get('text', '') for t in transcripts])
                            task["text"] = full_text
                            logger.info(f"Final transcribed text: {full_text}")
                        else:
                            task["text"] = ""
                except Exception as e:
                    task["text"] = ""
                    logger.error(f"Failed to download transcription result: {e}")
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

    asyncio.create_task(cleanup_task(task_id, delay=30))


async def cleanup_task(task_id: str, delay: int = 30):
    await asyncio.sleep(delay)
    asr_tasks.pop(task_id, None)
