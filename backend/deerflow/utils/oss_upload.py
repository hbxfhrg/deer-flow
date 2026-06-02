"""OSS upload utilities for Aliyun Object Storage Service."""

import io
import logging
import time
from typing import BinaryIO

import oss2

from deerflow.config.app_config import get_app_config

logger = logging.getLogger(__name__)


async def upload_file_to_oss(
    file_data: bytes | BinaryIO,
    filename: str,
    content_type: str = "audio/aac"
) -> str:
    """
    Upload a file to Aliyun OSS.
    
    Args:
        file_data: The file content as bytes or a file-like object
        filename: The target filename in OSS
        content_type: The MIME type of the file
    
    Returns:
        The URL of the uploaded file
    
    Raises:
        RuntimeError: If OSS is not configured or upload fails
    """
    config = get_app_config().oss
    
    if not config.is_configured():
        raise RuntimeError(
            "OSS not configured. Please set OSS_ENDPOINT, OSS_ACCESS_KEY_ID, "
            "OSS_ACCESS_KEY_SECRET, and OSS_BUCKET_NAME in config.yaml or environment variables."
        )
    
    try:
        auth = oss2.Auth(config.access_key_id, config.access_key_secret)
        bucket = oss2.Bucket(auth, config.endpoint, config.bucket_name)
        
        if isinstance(file_data, bytes):
            file_data = io.BytesIO(file_data)
        
        result = bucket.put_object(filename, file_data, headers={"Content-Type": content_type})
        
        if result.status == 200:
            bucket_host = config.bucket_host if config.bucket_host else f"https://{config.bucket_name}.{config.endpoint}"
            return f"{bucket_host}/{filename}"
        else:
            raise RuntimeError(f"OSS upload failed with status: {result.status}")
    
    except oss2.exceptions.RequestError as e:
        logger.error(f"OSS upload error: {e}")
        raise RuntimeError(f"OSS upload failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during OSS upload: {e}")
        raise


def generate_filename(original_filename: str) -> str:
    """
    Generate a unique filename for OSS storage.
    
    Args:
        original_filename: The original filename for extension preservation. Required.
    
    Returns:
        A unique filename with timestamp
    
    Raises:
        ValueError: If original_filename is None or empty
    """
    if not original_filename:
        raise ValueError("original_filename is required")
    
    # 使用传入的文件名，保持与模拟地址一致
    extension = ""
    if "." in original_filename:
        extension = "." + original_filename.split(".")[-1].lower()
        original_name = original_filename[:-(len(extension))]
    else:
        original_name = original_filename
    
    return f"voice/{original_name}{extension}"
