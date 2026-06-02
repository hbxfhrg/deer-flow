"""Debug ASR API response format."""

import dashscope
import json

# 设置API Key - 使用正确的DashScope API Key
dashscope.api_key = "sk-4285a0496c9d4f4fb3d2a4d19299cf43"

# 使用真实音频URL
AUDIO_URL = "https://cvm-demo.oss-cn-hangzhou.aliyuncs.com/voice/upload_1780368502.aac"

print("="*60)
print("Debugging DashScope ASR API Response")
print("="*60)
print(f"Audio URL: {AUDIO_URL}")

try:
    # 同步调用转写
    from dashscope.audio.asr import Transcription
    
    print("\n1. Submitting transcription task...")
    task_response = Transcription.async_call(
        model='paraformer-v2',
        file_urls=[AUDIO_URL]
    )
    
    print(f"Task Response Status: {task_response.status_code}")
    print(f"Task Response: {task_response}")
    
    if task_response.status_code != 200:
        print(f"❌ Failed to submit task: {task_response.message}")
        exit(1)
    
    task_id = task_response.output.task_id
    print(f"✅ Task ID: {task_id}")
    
    # 等待转写完成
    print("\n2. Waiting for transcription...")
    transcription_response = Transcription.wait(task=task_id)
    
    print(f"Transcription Status: {transcription_response.status_code}")
    print(f"Full Response: {transcription_response}")
    
    # 打印详细的输出结构
    print("\n3. Detailed output structure:")
    print(f"Type of output: {type(transcription_response.output)}")
    print(f"Output keys: {transcription_response.output.keys() if hasattr(transcription_response.output, 'keys') else 'Not a dict'}")
    
    # 尝试获取结果
    results = transcription_response.output.get('results', [])
    print(f"\nResults: {results}")
    
    if results:
        result = results[0]
        print(f"\nFirst result keys: {result.keys()}")
        
        # 检查各种可能的字段
        if 'transcripts' in result:
            print(f"Transcripts: {result['transcripts']}")
        if 'text' in result:
            print(f"Text: {result.get('text')}")
        if 'sentences' in result:
            print(f"Sentences: {result.get('sentences')}")
        
    print("\n✅ Done!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()