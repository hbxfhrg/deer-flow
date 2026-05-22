import asyncio
from datetime import datetime, UTC
from deerflow.roleplay import get_db, init_roleplay_db
from deerflow.roleplay.models import SceneRow, CourseRow

async def init_test_data():
    # 初始化数据库（使用服务已初始化的连接）
    from deerflow.roleplay import is_roleplay_db_initialized
    
    if not is_roleplay_db_initialized():
        print("数据库未初始化，跳过测试数据初始化")
        return
    
    async with get_db() as session:
        # 检查是否已有测试场景
        result = await session.execute(SceneRow.__table__.select().where(SceneRow.scene_name == "测试场景"))
        existing_scene = result.scalar_one_or_none()
        
        if existing_scene:
            scene_id = existing_scene.scene_id
            print(f"测试场景已存在，ID: {scene_id}")
        else:
            # 创建测试场景
            scene = SceneRow(
                scene_name="测试场景",
                scene_description="这是一个测试场景，用于自由式对练功能验证",
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
            scene_id = scene.scene_id
            print(f"创建测试场景成功，ID: {scene_id}")
        
        # 检查是否已有测试课程
        result = await session.execute(CourseRow.__table__.select().where(CourseRow.course_name == "测试课程"))
        existing_course = result.scalar_one_or_none()
        
        if existing_course:
            print(f"测试课程已存在，ID: {existing_course.course_id}")
        else:
            # 创建测试课程
            course = CourseRow(
                course_name="测试课程",
                course_type=1,
                scene_id=scene_id,
                practice_mode="text",
                create_time=datetime.now(UTC),
                status=1,
            )
            session.add(course)
            await session.commit()
            await session.refresh(course)
            print(f"创建测试课程成功，ID: {course.course_id}")

if __name__ == '__main__':
    asyncio.run(init_test_data())