"""Test script for ASR, TTS and OSS APIs using internal auth."""

import secrets

# Generate internal auth token
INTERNAL_AUTH_TOKEN = secrets.token_urlsafe(32)
INTERNAL_AUTH_HEADER_NAME = "X-DeerFlow-Internal-Token"

print(f"Internal Auth Token: {INTERNAL_AUTH_TOKEN}")
print(f"Header Name: {INTERNAL_AUTH_HEADER_NAME}")
print(f"\nUse this header in your requests:")
print(f"  {INTERNAL_AUTH_HEADER_NAME}: {INTERNAL_AUTH_TOKEN}")