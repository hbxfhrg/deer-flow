"""Debug ASR API response format - download transcription URL."""

import dashscope
import json
import urllib.request

# 设置API Key
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
    
    if task_response.status_code != 200:
        print(f"❌ Failed to submit task: {task_response.message}")
        exit(1)
    
    task_id = task_response.output.task_id
    print(f"✅ Task ID: {task_id}")
    
    # 等待转写完成
    print("\n2. Waiting for transcription...")
    transcription_response = Transcription.wait(task=task_id)
    
    print(f"Transcription Status: {transcription_response.status_code}")
    
    # 获取转写URL
    results = transcription_response.output.get('results', [])
    if results:
        result = results[0]
        transcription_url = result.get('transcription_url')
        print(f"\n3. Transcription URL: {transcription_url}")
        
        # 下载转写结果
        if transcription_url:
            print("\n4. Downloading transcription result...")
            with urllib.request.urlopen(transcription_url) as response:
                transcription_data = response.read().decode('utf-8')
                print(f"Raw JSON content:")
                print("-" * 50)
                print(transcription_data)
                print("-" * 50)
                
                # 解析JSON
                transcription_json = json.loads(transcription_data)
                print(f"\n5. JSON structure keys:")
                print(f"   Top level keys: {list(transcription_json.keys())}")
                
                # 检查各种可能的结构
                if 'Sentences' in transcription_json:
                    print(f"\n   Sentences found: {len(transcription_json['Sentences'])} items")
                    for i, sentence in enumerate(transcription_json['Sentences']):
                        print(f"     Sentence {i}: {sentence}")
                elif 'results' in transcription_json:
                    print(f"\n   Results found: {len(transcription_json['results'])} items")
                    for i, res in enumerate(transcription_json['results']):
                        print(f"     Result {i}: {res}")
                else:
                    print(f"\n   Unknown format - printing full JSON:")
                    print(json.dumps(transcription_json, indent=2, ensure_ascii=False))
    
    print("\n✅ Done!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()