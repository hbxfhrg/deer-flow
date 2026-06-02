"""Test script for ASR, TTS and OSS APIs."""

import asyncio
import httpx
import json
import os

# API base URL
BASE_URL = "http://localhost:8000"

# Test configuration
TEST_CONFIG = {
    "tts": {
        "text": "你好，我是客服小林，很高兴为您服务",
        "model": "qwen3-tts-flash",
        "voice": "Cherry",
        "language": "zh"
    },
    "asr": {
        "model": "paraformer-v2",
        "audio_url": "https://example.com/test-audio.mp3",
        "language": "zh"
    }
}


async def test_oss_config():
    """Test OSS configuration endpoint."""
    print("\n" + "="*60)
    print("Testing OSS Configuration")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/oss/config")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get("configured"):
                    print("✅ OSS is configured")
                    print(f"   Bucket: {data.get('bucket_name')}")
                    print(f"   Endpoint: {data.get('endpoint')}")
                else:
                    print("❌ OSS is not configured")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_tts_synthesize():
    """Test TTS synthesis endpoint."""
    print("\n" + "="*60)
    print("Testing TTS Synthesis")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            # Submit synthesis task
            print(f"\nSubmitting TTS task...")
            print(f"Text: {TEST_CONFIG['tts']['text']}")
            print(f"Model: {TEST_CONFIG['tts']['model']}")
            print(f"Voice: {TEST_CONFIG['tts']['voice']}")
            
            response = await client.post(
                f"{BASE_URL}/api/tts/synthesize",
                json=TEST_CONFIG["tts"]
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get("success"):
                    task_id = data.get("task_id")
                    print(f"✅ Task submitted successfully")
                    print(f"   Task ID: {task_id}")
                    
                    # Query task status
                    print(f"\nQuerying task status...")
                    await asyncio.sleep(2)  # Wait a bit
                    
                    query_response = await client.get(f"{BASE_URL}/api/tts/query/{task_id}")
                    query_data = query_response.json()
                    print(f"Status: {query_data.get('status')}")
                    print(f"Audio URL: {query_data.get('audio_url')}")
                    
                    if query_data.get("status") == "completed":
                        print("✅ TTS synthesis completed successfully")
                    elif query_data.get("status") == "processing":
                        print("⏳ TTS synthesis is still processing...")
                    else:
                        print(f"❌ TTS synthesis failed: {query_data.get('message')}")
                else:
                    print(f"❌ Failed to submit task")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_asr_transcribe():
    """Test ASR transcription endpoint."""
    print("\n" + "="*60)
    print("Testing ASR Transcription")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            # Submit transcription task
            print(f"\nSubmitting ASR task...")
            print(f"Audio URL: {TEST_CONFIG['asr']['audio_url']}")
            print(f"Model: {TEST_CONFIG['asr']['model']}")
            
            response = await client.post(
                f"{BASE_URL}/api/asr/transcribe",
                json=TEST_CONFIG["asr"]
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get("success"):
                    task_id = data.get("task_id")
                    print(f"✅ Task submitted successfully")
                    print(f"   Task ID: {task_id}")
                    
                    # Query task status
                    print(f"\nQuerying task status...")
                    await asyncio.sleep(2)  # Wait a bit
                    
                    query_response = await client.get(f"{BASE_URL}/api/asr/query/{task_id}")
                    query_data = query_response.json()
                    print(f"Status: {query_data.get('status')}")
                    print(f"Text: {query_data.get('text')}")
                    
                    if query_data.get("status") == "completed":
                        print("✅ ASR transcription completed successfully")
                    elif query_data.get("status") == "processing":
                        print("⏳ ASR transcription is still processing...")
                    else:
                        print(f"❌ ASR transcription failed: {query_data.get('message')}")
                else:
                    print(f"❌ Failed to submit task")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_oss_upload():
    """Test OSS file upload endpoint."""
    print("\n" + "="*60)
    print("Testing OSS File Upload")
    print("="*60)
    
    # Create a test audio file
    test_audio_path = os.path.join(os.path.dirname(__file__), "test_audio.aac")
    
    # Generate a small test audio file (just for testing the upload mechanism)
    test_data = b"FAKE_AUDIO_DATA_FOR_TESTING_UPLOAD"
    
    async with httpx.AsyncClient() as client:
        try:
            print(f"\nUploading test audio file...")
            
            files = {
                "file": ("test_audio.aac", test_data, "audio/aac")
            }
            
            response = await client.post(
                f"{BASE_URL}/api/oss/upload",
                files=files
            )
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                if data.get("success"):
                    print("✅ File uploaded successfully")
                    print(f"   URL: {data.get('url')}")
                    print(f"   Filename: {data.get('filename')}")
                else:
                    print(f"❌ Upload failed: {data.get('message')}")
            else:
                print(f"❌ Failed: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ASR, TTS and OSS API Test Suite")
    print("="*60)
    print(f"Base URL: {BASE_URL}")
    
    # Test OSS configuration
    await test_oss_config()
    
    # Test OSS upload
    await test_oss_upload()
    
    # Test TTS synthesis
    await test_tts_synthesize()
    
    # Test ASR transcription
    await test_asr_transcribe()
    
    print("\n" + "="*60)
    print("Test Suite Completed")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())