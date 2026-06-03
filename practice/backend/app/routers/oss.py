"""OSS 上传 API 路由"""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.config import get_config
from app.oss_upload import generate_filename, upload_file_to_oss

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/oss", tags=["OSS"])


class OSSUploadResponse(BaseModel):
    success: bool = Field(description="Whether the upload was successful")
    url: str = Field(description="URL of the uploaded file")
    filename: str = Field(description="Filename in OSS")
    message: str = Field(description="Status message")


class OSSConfigResponse(BaseModel):
    configured: bool = Field(description="Whether OSS is configured")
    endpoint: str = Field(description="OSS endpoint")
    bucket_name: str = Field(description="OSS bucket name")
    bucket_host: str = Field(description="OSS bucket host URL")


@router.post("/upload", response_model=OSSUploadResponse)
async def upload_to_oss(
    file: Annotated[UploadFile, File(description="File to upload")]
) -> OSSUploadResponse:
    config = get_config().oss

    if not config.is_configured():
        raise HTTPException(
            status_code=500,
            detail="OSS not configured. Please set endpoint, access_key_id, access_key_secret, and bucket_name in config.yaml."
        )

    try:
        file_content = await file.read()

        extension = ".aac"
        if file.content_type:
            if file.content_type.startswith("audio/mpeg"):
                extension = ".mp3"
            elif file.content_type.startswith("audio/wav"):
                extension = ".wav"
            elif file.content_type.startswith("audio/webm"):
                extension = ".webm"

        filename = f"voice/upload_{int(time.time())}{extension}"

        url = await upload_file_to_oss(
            file_data=file_content,
            filename=filename,
            content_type=file.content_type or "audio/aac"
        )

        return OSSUploadResponse(
            success=True,
            url=url,
            filename=filename,
            message="File uploaded successfully"
        )

    except Exception as e:
        logger.error(f"OSS upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/config", response_model=OSSConfigResponse)
async def get_oss_config() -> OSSConfigResponse:
    config = get_config().oss

    return OSSConfigResponse(
        configured=config.is_configured(),
        endpoint=config.endpoint,
        bucket_name=config.bucket_name,
        bucket_host=config.bucket_host
    )
