import asyncio
from deerflow.roleplay.practice_service import PracticeService

async def test_history():
    result = await PracticeService.get_practice_history(75)
    print('practiceMode:', result.get('practiceMode'))
    print('totalRounds:', result.get('totalRounds'))
    print('history count:', len(result.get('history', [])))
    for h in result.get('history', []):
        print(f"dialog_id={h['dialog_id']}, speaker={h['speaker']}, content_type={h['content_type']}, content_url exists={bool(h.get('content_url'))}")

if __name__ == '__main__':
    asyncio.run(test_history())