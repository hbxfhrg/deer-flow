import asyncio
from deerflow.roleplay import init_roleplay_db, get_db, create_roleplay_tables
from deerflow.roleplay.models import CourseRow, SceneRow, DialogDetailRow
from deerflow.roleplay.practice_service import PracticeService
from deerflow.config.app_config import get_app_config

async def debug_practice():
    try:
        # 初始化数据库（与服务相同的配置）
        config = get_app_config()
        init_roleplay_db(config.database)
        
        print("1. 检查课程是否存在...")
        async with get_db() as session:
            result = await session.execute(CourseRow.__table__.select().where(CourseRow.course_id == 3))
            course = result.scalar_one_or_none()
            print(f"找到课程: {course}")
            
            if course:
                print(f"课程ID: {course.course_id}, 场景ID: {course.scene_id}")
                
                # 检查场景
                result = await session.execute(SceneRow.__table__.select().where(SceneRow.scene_id == course.scene_id))
                scene = result.scalar_one_or_none()
                print(f"找到场景: {scene}")
        
        print("\n2. 尝试调用PracticeService.start...")
        result = await PracticeService.start(3, "testuser")
        print(f"成功! 结果: {result}")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_practice())