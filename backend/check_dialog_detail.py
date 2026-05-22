import asyncio
import aiomysql
from deerflow.config.app_config import get_app_config

async def check_table():
    try:
        config = get_app_config()
        db_config = config.database
        
        conn = await aiomysql.connect(
            host=db_config.roleplay_db_host,
            port=db_config.roleplay_db_port,
            user=db_config.roleplay_db_user,
            password=db_config.roleplay_db_password,
            db=db_config.roleplay_db_name,
            connect_timeout=10
        )
        
        print("检查pract_dialog_detail表结构...")
        async with conn.cursor() as cursor:
            await cursor.execute("DESCRIBE pract_dialog_detail")
            columns = await cursor.fetchall()
            
            print("\n当前表结构:")
            for col in columns:
                print(f"  {col[0]}: {col[1]}")
            
            # 检查是否需要添加round_number字段
            has_round_number = any(col[0] == 'round_number' for col in columns)
            print(f"\n是否有round_number字段: {has_round_number}")
            
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    asyncio.run(check_table())