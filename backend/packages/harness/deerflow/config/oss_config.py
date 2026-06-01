"""OSS configuration for Aliyun Object Storage Service."""

from pydantic import BaseModel, Field


class OSSConfig(BaseModel):
    """Configuration for Aliyun Object Storage Service."""

    endpoint: str = Field(
        default="oss-cn-hangzhou.aliyuncs.com",
        description="OSS endpoint"
    )
    access_key_id: str = Field(
        default="",
        description="OSS access key ID"
    )
    access_key_secret: str = Field(
        default="",
        description="OSS access key secret"
    )
    bucket_name: str = Field(
        default="",
        description="OSS bucket name"
    )
    bucket_host: str = Field(
        default="",
        description="OSS bucket host URL"
    )

    def is_configured(self) -> bool:
        """Check if OSS is properly configured."""
        return all([
            self.endpoint,
            self.access_key_id,
            self.access_key_secret,
            self.bucket_name
        ])
