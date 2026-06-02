"""Simple test for ASR transcription using DashScope."""

import dashscope
from dashscope.audio.asr import Transcription

# DashScope Configuration
DASHSCOPE_API_KEY = "sk-4285a0496c9d4f4fb3d2a4d19299cf43"
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

def test_asr_transcription():
    """Test ASR transcription with DashScope."""
    print("="*60)
    print("Testing ASR Transcription")
    print("="*60)
    
    # Set DashScope API key
    dashscope.api_key = DASHSCOPE_API_KEY
    dashscope.base_http_api_url = DASHSCOPE_BASE_URL
    
    # Use the audio file we just uploaded
    audio_url = "https://cvm-demo.oss-cn-hangzhou.aliyuncs.com/voice/upload_1780388685.mp3"
    
    try:
        print(f"Audio URL: {audio_url}")
        print("\nSubmitting transcription task...")
        
        # Submit async transcription task
        task_response = Transcription.async_call(
            model='paraformer-v2',
            file_urls=[audio_url]
        )
        
        print(f"Task Status: {task_response.status_code}")
        
        if task_response.status_code != 200:
            print(f"❌ Failed to submit task: {task_response.message}")
            return None
        
        task_id = task_response.output.task_id
        print(f"✅ Task ID: {task_id}")
        
        # Wait for transcription
        print("\nWaiting for transcription...")
        transcription_response = Transcription.wait(task=task_id)
        
        print(f"Transcription Status: {transcription_response.status_code}")
        
        if transcription_response.status_code != 200:
            print(f"❌ Transcription failed: {transcription_response.message}")
            return None
        
        # Print detailed output
        print("\nTranscription Output:")
        print(f"Type: {type(transcription_response.output)}")
        print(f"Output: {transcription_response.output}")
        
        # Extract results
        results = transcription_response.output.get('results', [])
        print(f"\nResults: {results}")
        
        if results:
            result = results[0]
            print(f"\nFirst result keys: {result.keys()}")
            
            # Check for various possible fields
            if 'text' in result:
                print(f"Text: {result.get('text')}")
            if 'transcripts' in result:
                print(f"Transcripts: {result.get('transcripts')}")
            if 'sentences' in result:
                print(f"Sentences: {result.get('sentences')}")
            
            # Parse and combine text
            full_text = ""
            if 'text' in result:
                full_text = result.get('text', '')
            elif 'transcripts' in result:
                transcripts = result.get('transcripts', [])
                full_text = ' '.join([t.get('text', '') for t in transcripts])
            
            print(f"\n✅ Final transcribed text: {full_text}")
            return full_text
        else:
            print("❌ No results found in response")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_asr_transcription()