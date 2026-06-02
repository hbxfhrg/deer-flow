"""Test TTS synthesis and OSS upload functionality."""

import asyncio
import httpx
import json
import time

async def test_oss_config():
    """Test OSS configuration endpoint."""
    print("="*60)
    print("1. Testing OSS Configuration")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/api/oss/config")
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                config = response.json()
                print(f"Configured: {config.get('configured')}")
                print(f"Endpoint: {config.get('endpoint')}")
                print(f"Bucket Name: {config.get('bucket_name')}")
                print(f"Bucket Host: {config.get('bucket_host')}")
                return config.get('configured', False)
            else:
                print(f"❌ Failed to get OSS config: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

async def test_tts_synthesis():
    """Test TTS synthesis and OSS upload."""
    print("\n" + "="*60)
    print("2. Testing TTS Synthesis")
    print("="*60)
    
    test_text = "您好，这是一个测试语音合成的示例。"
    
    async with httpx.AsyncClient() as client:
        try:
            # 提交TTS任务
            print(f"Text to synthesize: {test_text}")
            print("\nSubmitting TTS task...")
            
            submit_response = await client.post(
                "http://localhost:8000/api/tts/synthesize",
                json={
                    "text": test_text,
                    "model": "qwen3-tts-flash",
                    "voice": "Cherry",
                    "language": "zh"
                }
            )
            
            print(f"Status Code: {submit_response.status_code}")
            
            if submit_response.status_code != 200:
                print(f"❌ Failed: {submit_response.text}")
                return None
            
            submit_data = submit_response.json()
            print(f"Response: {submit_data}")
            
            if not submit_data.get("success"):
                print(f"❌ Failed to submit task")
                return None
            
            task_id = submit_data.get("task_id")
            print(f"✅ Task submitted: {task_id}")
            
            # 轮询查询结果
            print("\nQuerying task status...")
            max_retries = 60  # 最多等待60秒
            for i in range(max_retries):
                await asyncio.sleep(1)
                
                query_response = await client.get(
                    f"http://localhost:8000/api/tts/query/{task_id}"
                )
                
                query_data = query_response.json()
                status = query_data.get("status")
                audio_url = query_data.get("audio_url", "")
                
                print(f"  [{i+1}/{max_retries}] Status: {status}, Audio URL: '{audio_url[:50]}...' if len(audio_url) > 50 else audio_url")
                
                if status == "completed":
                    print(f"\n✅ TTS synthesis completed!")
                    print(f"   Audio URL: {audio_url}")
                    
                    # 验证OSS文件是否可访问
                    if audio_url:
                        print("\n3. Verifying OSS file accessibility...")
                        audio_response = await client.get(audio_url)
                        if audio_response.status_code == 200:
                            print(f"✅ OSS file accessible! Content length: {len(audio_response.content)} bytes")
                        else:
                            print(f"❌ OSS file not accessible! Status: {audio_response.status_code}")
                    
                    return audio_url
                elif status == "failed":
                    print(f"\n❌ TTS synthesis failed!")
                    return None
            
            print(f"\n⏰ Timeout: Task did not complete within {max_retries} seconds")
            return None
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None

async def test_oss_direct_upload():
    """Test direct OSS upload functionality."""
    print("\n" + "="*60)
    print("4. Testing Direct OSS Upload")
    print("="*60)
    
    # 创建测试音频数据（简单的音频文件头）
    test_audio_data = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    
    async with httpx.AsyncClient() as client:
        try:
            files = {'file': ('test.wav', test_audio_data, 'audio/wav')}
            response = await client.post(
                "http://localhost:8000/api/oss/upload",
                files=files
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Upload successful!")
                print(f"   URL: {result.get('url')}")
                print(f"   Filename: {result.get('filename')}")
                
                # 验证上传的文件
                uploaded_url = result.get('url')
                if uploaded_url:
                    verify_response = await client.get(uploaded_url)
                    if verify_response.status_code == 200:
                        print(f"✅ Uploaded file accessible!")
                    else:
                        print(f"❌ Uploaded file not accessible! Status: {verify_response.status_code}")
                
                return result.get('url')
            else:
                print(f"❌ Upload failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return None

async def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("TTS and OSS Upload Test Suite")
    print("="*70)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Test 1: Check OSS config
    oss_configured = await test_oss_config()
    
    if not oss_configured:
        print("\n❌ OSS is not configured! Cannot proceed with upload tests.")
        return
    
    # Test 2: TTS synthesis
    tts_url = await test_tts_synthesis()
    
    # Test 3: Direct OSS upload
    oss_url = await test_oss_direct_upload()
    
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"TTS Synthesis: {'✅ PASSED' if tts_url else '❌ FAILED'}")
    print(f"OSS Direct Upload: {'✅ PASSED' if oss_url else '❌ FAILED'}")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())