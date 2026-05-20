"""
Script to add free practice mode fields to scenes table in MySQL database.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def migrate_database():
    try:
        # Import aiomysql
        import aiomysql
        
        # Get database configuration from environment variables
        db_host = os.getenv('ROLEPLAY_DB_HOST', 'localhost')
        db_port = int(os.getenv('ROLEPLAY_DB_PORT', '3306'))
        db_name = os.getenv('ROLEPLAY_DB_NAME', 'deerflow_roleplay')
        db_user = os.getenv('ROLEPLAY_DB_USER', '')
        db_password = os.getenv('ROLEPLAY_DB_PASSWORD', '')
        
        print(f"Connecting to MySQL database: {db_host}:{db_port}/{db_name}")
        
        # Create connection pool
        pool = await aiomysql.create_pool(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            db=db_name,
            autocommit=True
        )
        
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Add practice_mode field
                try:
                    await cur.execute("""
                        ALTER TABLE pract_scene_set 
                        ADD COLUMN practice_mode VARCHAR(20) DEFAULT '剧本式'
                    """)
                    print("✓ Added practice_mode column")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print("✓ practice_mode column already exists")
                    else:
                        raise
                
                # Add knowledge_base field
                try:
                    await cur.execute("""
                        ALTER TABLE pract_scene_set 
                        ADD COLUMN knowledge_base TEXT
                    """)
                    print("✓ Added knowledge_base column")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print("✓ knowledge_base column already exists")
                    else:
                        raise
                
                # Add summary_text field
                try:
                    await cur.execute("""
                        ALTER TABLE pract_scene_set 
                        ADD COLUMN summary_text TEXT
                    """)
                    print("✓ Added summary_text column")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print("✓ summary_text column already exists")
                    else:
                        raise
                
                # Add exam_categories field
                try:
                    await cur.execute("""
                        ALTER TABLE pract_scene_set 
                        ADD COLUMN exam_categories VARCHAR(200)
                    """)
                    print("✓ Added exam_categories column")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print("✓ exam_categories column already exists")
                    else:
                        raise
                
                # Add scoring_rules field
                try:
                    await cur.execute("""
                        ALTER TABLE pract_scene_set 
                        ADD COLUMN scoring_rules TEXT
                    """)
                    print("✓ Added scoring_rules column")
                except Exception as e:
                    if "Duplicate column name" in str(e):
                        print("✓ scoring_rules column already exists")
                    else:
                        raise
                
                # Update default difficulty value from 'medium' to '简单'
                try:
                    await cur.execute("""
                        UPDATE pract_scene_set SET difficulty = '简单' WHERE difficulty = 'medium'
                    """)
                    print("✓ Updated difficulty default values")
                except Exception as e:
                    print(f"Note: {str(e)}")
        
        pool.close()
        await pool.wait_closed()
        
        print("\n✅ Database migration completed successfully!")
        
    except ImportError:
        print("❌ Please install aiomysql first: pip install aiomysql")
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(migrate_database())