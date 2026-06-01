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


def generate_filename(original_filename: str | None = None) -> str:
    """
    Generate a unique filename for OSS storage.
    
    Args:
        original_filename: Optional original filename for extension preservation
    
    Returns:
        A unique filename with timestamp
    """
    timestamp = int(time.time())
    extension = ""
    
    if original_filename and "." in original_filename:
        extension = "." + original_filename.split(".")[-1].lower()
    
    return f"voice/upload_{timestamp}{extension}"