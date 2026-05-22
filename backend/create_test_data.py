import asyncio
from datetime import datetime, UTC
from deerflow.roleplay import init_roleplay_db, get_db
from deerflow.roleplay.models import SceneRow, CourseRow, PracticeRecordRow, DialogDetailRow

async def create_test_data():
    # 使用与服务相同的配置初始化数据库
    init_roleplay_db({
        'type': 'sqlite',
        'database': './data/roleplay.db',
        'host': '',
        'port': 0,
        'username': '',
        'password': ''
    })
    
    async with get_db() as session:
        # 创建测试场景
        scene = SceneRow(
            scene_name="测试场景",
            scene_description="这是一个测试场景，用于自由式对练功能验证。你是一位潜在客户，正在咨询产品信息。",
            dialog_round_limit=3,
            status=1,
            create_time=datetime.now(UTC),
            update_time=datetime.now(UTC),
            model_name="gpt-4o-mini",
            summary_text="产品知识:了解客户需求是销售的第一步\n客户需求分析:产品优势需要与客户痛点相结合\n销售策略:建立信任关系至关重要",
            exam_categories="产品知识,沟通技巧,问题解决",
            scoring_rules="根据学员回复的准确性、完整性和说服力进行评分",
        )
        session.add(scene)
        await session.commit()
        await session.refresh(scene)
        print(f"创建测试场景成功，ID: {scene.scene_id}")
        
        # 创建测试课程
        course = CourseRow(
            course_name="测试课程",
            course_type=1,
            scene_id=scene.scene_id,
            practice_mode="text",
            create_time=datetime.now(UTC),
            status=1,
        )
        session.add(course)
        await session.commit()
        await session.refresh(course)
        print(f"创建测试课程成功，ID: {course.course_id}")

if __name__ == '__main__':
    asyncio.run(create_test_data())