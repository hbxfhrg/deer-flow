import asyncio
import aiomysql
from deerflow.config.app_config import get_app_config

async def test_mysql():
    try:
        config = get_app_config()
        db_config = config.database
        
        print(f"连接信息:")
        print(f"  Host: {db_config.roleplay_db_host}")
        print(f"  Port: {db_config.roleplay_db_port}")
        print(f"  Database: {db_config.roleplay_db_name}")
        print(f"  User: {db_config.roleplay_db_user}")
        
        print("\n正在连接MySQL...")
        conn = await aiomysql.connect(
            host=db_config.roleplay_db_host,
            port=db_config.roleplay_db_port,
            user=db_config.roleplay_db_user,
            password=db_config.roleplay_db_password,
            db=db_config.roleplay_db_name,
            connect_timeout=10
        )
        
        print("连接成功！")
        
        async with conn.cursor() as cursor:
            # 检查表是否存在
            await cursor.execute("SHOW TABLES LIKE 'pract_%'")
            tables = await cursor.fetchall()
            print(f"\n现有的对练相关表: {[t[0] for t in tables]}")
            
            # 检查pract_scene_set表
            await cursor.execute("DESCRIBE pract_scene_set")
            if cursor.description:
                print("\npract_scene_set表结构:")
                for row in await cursor.fetchall():
                    print(f"  {row[0]}: {row[1]}")
            
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    asyncio.run(test_mysql())