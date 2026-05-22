import asyncio
from deerflow.config.app_config import get_app_config
from deerflow.roleplay import init_roleplay_db, create_roleplay_tables, get_db

async def check_tables():
    try:
        config = get_app_config()
        init_roleplay_db(config.database)
        
        print("创建表...")
        await create_roleplay_tables()
        print("表创建成功")
        
        async with get_db() as session:
            # 检查表是否存在
            result = await session.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = result.fetchall()
            print(f"\n数据库中的表: {[t[0] for t in tables]}")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_tables())