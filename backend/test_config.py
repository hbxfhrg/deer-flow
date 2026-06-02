"""Test configuration loading."""

from deerflow.config.app_config import get_app_config

config = get_app_config()

print("="*60)
print("Configuration Loading Test")
print("="*60)

print("\nOSS Configuration:")
print(f"  endpoint: {config.oss.endpoint}")
print(f"  access_key_id: {config.oss.access_key_id[:10]}..." if config.oss.access_key_id else "  access_key_id: (empty)")
print(f"  access_key_secret: {config.oss.access_key_secret[:10]}..." if config.oss.access_key_secret else "  access_key_secret: (empty)")
print(f"  bucket_name: {config.oss.bucket_name}")
print(f"  bucket_host: {config.oss.bucket_host}")
print(f"  is_configured: {config.oss.is_configured()}")

print("\nDashScope Configuration:")
print(f"  api_key: {config.dashscope.api_key[:10]}..." if config.dashscope.api_key else "  api_key: (empty)")
print(f"  base_url: {config.dashscope.base_url}")
print(f"  is_configured: {config.dashscope.is_configured()}")

print("\n" + "="*60)