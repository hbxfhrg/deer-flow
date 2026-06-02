"""Full test for ASR transcription including downloading result JSON."""

import dashscope
from dashscope.audio.asr import Transcription
import urllib.request
import json

# DashScope Configuration
DASHSCOPE_API_KEY = "sk-4285a0496c9d4f4fb3d2a4d19299cf43"
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

def test_asr_transcription_full():
    """Test ASR transcription with full result download."""
    print("="*60)
    print("Testing ASR Transcription (Full)")
    print("="*60)
    
    # Set DashScope API key
    dashscope.api_key = DASHSCOPE_API_KEY
    dashscope.base_http_api_url = DASHSCOPE_BASE_URL
    
    # Use the audio file we uploaded earlier
    audio_url = "https://cvm-demo.oss-cn-hangzhou.aliyuncs.com/voice/upload_1780388685.mp3"
    
    try:
        print(f"Audio URL: {audio_url}")
        print("\n1. Submitting transcription task...")
        
        # Submit async transcription task
        task_response = Transcription.async_call(
            model='paraformer-v2',
            file_urls=[audio_url]
        )
        
        print(f"Task Status Code: {task_response.status_code}")
        
        if task_response.status_code != 200:
            print(f"❌ Failed to submit task: {task_response.message}")
            return None
        
        task_id = task_response.output.task_id
        print(f"✅ Task ID: {task_id}")
        
        # Wait for transcription
        print("\n2. Waiting for transcription...")
        transcription_response = Transcription.wait(task=task_id)
        
        print(f"Transcription Status: {transcription_response.status_code}")
        
        if transcription_response.status_code != 200:
            print(f"❌ Transcription failed: {transcription_response.message}")
            return None
        
        # Extract results
        results = transcription_response.output.get('results', [])
        
        if not results:
            print("❌ No results found in response")
            return None
        
        result = results[0]
        transcription_url = result.get('transcription_url')
        
        if not transcription_url:
            print("❌ No transcription URL found in result")
            return None
        
        print(f"\n3. Transcription URL found: {transcription_url[:50]}...")
        
        # Download and parse transcription JSON
        print("\n4. Downloading transcription result...")
        try:
            with urllib.request.urlopen(transcription_url) as response:
                transcription_data = response.read().decode('utf-8')
                transcription_json = json.loads(transcription_data)
                
                print(f"✅ Downloaded JSON data: {len(transcription_data)} characters")
                print(f"JSON keys: {list(transcription_json.keys())}")
                
                # Parse the transcripts
                transcripts = transcription_json.get('transcripts', [])
                print(f"\n5. Parsing transcripts...")
                print(f"Number of transcripts: {len(transcripts)}")
                
                if transcripts:
                    full_text = ' '.join([t.get('text', '') for t in transcripts])
                    print(f"\n✅ Final transcribed text:")
                    print(f"   {full_text}")
                    return full_text
                else:
                    print("❌ No transcripts found in downloaded data")
                    return None
                    
        except Exception as e:
            print(f"❌ Failed to download transcription result: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_asr_transcription_full()