"""OSS 上传工具 — 从 deerflow/utils/oss_upload.py 迁移"""

import io
import logging
import time
from typing import BinaryIO

import oss2

from app.config import get_config

logger = logging.getLogger(__name__)


async def upload_file_to_oss(
    file_data: bytes | BinaryIO,
    filename: str,
    content_type: str = "audio/aac"
) -> str:
    """上传文件到阿里云 OSS

    Args:
        file_data: 文件内容（bytes 或 file-like object）
        filename: OSS 中的目标文件名
        content_type: MIME 类型

    Returns:
        上传后的文件 URL

    Raises:
        RuntimeError: OSS 未配置或上传失败
    """
    config = get_config().oss

    if not config.is_configured():
        raise RuntimeError(
            "OSS not configured. Please set endpoint, access_key_id, "
            "access_key_secret, and bucket_name in config.yaml."
        )

    try:
        auth = oss2.Auth(config.resolved_access_key_id, config.resolved_access_key_secret)
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
    """生成唯一的 OSS 文件名"""
    timestamp = int(time.time())
    extension = ""

    if original_filename and "." in original_filename:
        extension = "." + original_filename.split(".")[-1].lower()

    return f"voice/upload_{timestamp}{extension}"
