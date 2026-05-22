import asyncio
from deerflow.config.app_config import get_app_config
from deerflow.roleplay import init_roleplay_db
from deerflow.roleplay.practice_service import PracticeService

async def test_practice_start():
    try:
        config = get_app_config()
        init_roleplay_db(config.database)
        
        print("调用PracticeService.start...")
        result = await PracticeService.start(3, "testuser")
        print(f"成功! 结果: {result}")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_practice_start())