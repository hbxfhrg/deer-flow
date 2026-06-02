"""OSS upload API router."""

import logging
import time
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from deerflow.config.app_config import get_app_config
from deerflow.utils.oss_upload import generate_filename, upload_file_to_oss

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/oss", tags=["OSS"])


class OSSUploadResponse(BaseModel):
    """Response model for OSS upload."""
    
    success: bool = Field(description="Whether the upload was successful")
    url: str = Field(description="URL of the uploaded file")
    filename: str = Field(description="Filename in OSS")
    message: str = Field(description="Status message")


class OSSConfigResponse(BaseModel):
    """Response model for OSS configuration."""
    
    configured: bool = Field(description="Whether OSS is configured")
    endpoint: str = Field(description="OSS endpoint")
    bucket_name: str = Field(description="OSS bucket name")
    bucket_host: str = Field(description="OSS bucket host URL")


@router.post("/upload", response_model=OSSUploadResponse)
async def upload_to_oss(
    file: Annotated[UploadFile, File(description="File to upload")]
) -> OSSUploadResponse:
    """
    Upload a file to Aliyun OSS.
    
    Args:
        file: The file to upload
        
    Returns:
        OSSUploadResponse: Upload result containing URL and filename
    """
    config = get_app_config().oss
    
    if not config.is_configured():
        raise HTTPException(
            status_code=500,
            detail="OSS not configured. Please set OSS_ENDPOINT, OSS_ACCESS_KEY_ID, "
                   "OSS_ACCESS_KEY_SECRET, and OSS_BUCKET_NAME in config.yaml or environment variables."
        )
    
    try:
        file_content = await file.read()
        
        # 根据内容类型确定扩展名
        extension = ".aac"
        if file.content_type:
            if file.content_type.startswith("audio/mpeg"):
                extension = ".mp3"
            elif file.content_type.startswith("audio/wav"):
                extension = ".wav"
            elif file.content_type.startswith("audio/webm"):
                extension = ".webm"
        
        # 生成文件名，使用确定的扩展名
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
    """
    Get current OSS configuration status.
    
    Returns:
        OSSConfigResponse: Current OSS configuration
    """
    config = get_app_config().oss
    
    return OSSConfigResponse(
        configured=config.is_configured(),
        endpoint=config.endpoint,
        bucket_name=config.bucket_name,
        bucket_host=config.bucket_host
    )
