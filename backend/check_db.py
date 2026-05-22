import asyncio
from deerflow.roleplay import get_db, init_roleplay_db
from deerflow.roleplay.models import CourseRow, SceneRow

async def check():
    # 初始化数据库
    init_roleplay_db({
        'type': 'sqlite',
        'database': ':memory:',
        'host': '',
        'port': 0,
        'username': '',
        'password': ''
    })
    
    async with get_db() as session:
        # 检查课程
        result = await session.execute(CourseRow.__table__.select())
        courses = result.all()
        print(f'课程数量: {len(courses)}')
        for c in courses:
            print(f'{c.course_id}: {c.course_name} - 场景ID: {c.scene_id}')
        
        # 检查场景
        result = await session.execute(SceneRow.__table__.select())
        scenes = result.all()
        print(f'\n场景数量: {len(scenes)}')
        for s in scenes:
            print(f'{s.scene_id}: {s.scene_name}')

if __name__ == '__main__':
    asyncio.run(check())