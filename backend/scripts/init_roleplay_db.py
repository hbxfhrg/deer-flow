"""Roleplay module initialization script.

Run this script to initialize the roleplay database tables.
"""

import asyncio
import sys

async def init_roleplay_tables():
    """Initialize roleplay module database tables."""
    from deerflow.config.app_config import get_app_config
    from deerflow.roleplay import init_roleplay_db, create_roleplay_tables, is_roleplay_db_initialized
    
    try:
        config = get_app_config()
        if not is_roleplay_db_initialized():
            init_roleplay_db(config.database)
        await create_roleplay_tables()
        print("✅ Roleplay database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize roleplay tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(init_roleplay_tables())
    sys.exit(0 if success else 1)