"""Test ASR with real audio URL."""

import asyncio
import httpx
import json

# 使用刚才上传的真实音频URL
AUDIO_URL = "https://cvm-demo.oss-cn-hangzhou.aliyuncs.com/voice/upload_1780368502.aac"

async def test_asr_with_real_audio():
    """Test ASR transcription with real audio URL."""
    print("="*60)
    print("Testing ASR with Real Audio URL")
    print("="*60)
    print(f"Audio URL: {AUDIO_URL}")
    
    async with httpx.AsyncClient() as client:
        try:
            # 提交转写任务
            print("\n1. Submitting transcription task...")
            submit_response = await client.post(
                "http://localhost:8000/api/asr/transcribe",
                json={
                    "model": "paraformer-v2",
                    "audio_url": AUDIO_URL,
                    "language": "zh"
                }
            )
            
            print(f"Status Code: {submit_response.status_code}")
            
            if submit_response.status_code != 200:
                print(f"❌ Failed: {submit_response.text}")
                return
            
            submit_data = submit_response.json()
            print(f"Response: {submit_data}")
            
            if not submit_data.get("success"):
                print(f"❌ Failed to submit task")
                return
            
            task_id = submit_data.get("task_id")
            print(f"✅ Task submitted: {task_id}")
            
            # 轮询查询结果
            print("\n2. Querying task status...")
            max_retries = 60  # 最多等待60秒
            for i in range(max_retries):
                await asyncio.sleep(1)
                
                query_response = await client.get(
                    f"http://localhost:8000/api/asr/query/{task_id}"
                )
                
                query_data = query_response.json()
                status = query_data.get("status")
                text = query_data.get("text", "")
                
                print(f"  [{i+1}/{max_retries}] Status: {status}, Text: '{text}'")
                
                if status == "completed":
                    print(f"\n✅ Transcription completed!")
                    print(f"   Text: {text}")
                    break
                elif status == "failed":
                    print(f"\n❌ Transcription failed!")
                    break
            
            if query_data.get("status") != "completed":
                print(f"\n⏰ Timeout: Task did not complete within {max_retries} seconds")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_asr_with_real_audio())