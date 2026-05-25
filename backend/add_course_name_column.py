import asyncio
import aiomysql
from deerflow.config.app_config import get_app_config

async def add_course_name_column():
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
        
        print("添加course_name字段到pract_course_record表...")
        async with conn.cursor() as cursor:
            # 添加course_name字段
            sql = """
            ALTER TABLE pract_course_record
            ADD COLUMN course_name VARCHAR(255) NULL AFTER conversation_id
            """
            await cursor.execute(sql)
            await conn.commit()
            
            print("字段添加成功！")
            
            # 验证
            await cursor.execute("DESCRIBE pract_course_record")
            columns = await cursor.fetchall()
            print("\npract_course_record表结构:")
            for col in columns:
                print(f"  {col[0]}: {col[1]}")
            
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    asyncio.run(add_course_name_column())