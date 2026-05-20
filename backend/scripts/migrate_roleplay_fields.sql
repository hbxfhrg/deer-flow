-- =============================================
-- 自由对练功能数据库迁移脚本
-- 适用于 MySQL 数据库
-- =============================================

-- =============================================
-- 第一部分：添加模型中新增的字段（数据库中不存在的）
-- =============================================

-- 1. 添加难度字段
ALTER TABLE pract_scene_set 
ADD COLUMN difficulty VARCHAR(20) DEFAULT '简单' COMMENT '难度等级（简单/中等/困难）';

-- 2. 添加练习轮数字段
ALTER TABLE pract_scene_set 
ADD COLUMN rounds INT DEFAULT 5 COMMENT '练习轮数';

-- 3. 添加每轮时间限制字段
ALTER TABLE pract_scene_set 
ADD COLUMN time_per_round INT DEFAULT 120 COMMENT '每轮时间限制（秒）';

-- 4. 添加总时长限制字段
ALTER TABLE pract_scene_set 
ADD COLUMN total_time_limit INT DEFAULT 600 COMMENT '总时长限制（秒）';

-- 5. 添加模型名字段
ALTER TABLE pract_scene_set 
ADD COLUMN model_name VARCHAR(128) DEFAULT 'gpt-4o-mini' COMMENT '模型名称';

-- 6. 添加系统提示词字段
ALTER TABLE pract_scene_set 
ADD COLUMN system_prompt TEXT COMMENT '系统提示词';

-- 7. 添加用户提示词模板字段
ALTER TABLE pract_scene_set 
ADD COLUMN user_prompt_template TEXT COMMENT '用户提示词模板';

-- 8. 添加元数据JSON字段
ALTER TABLE pract_scene_set 
ADD COLUMN metadata_json TEXT COMMENT '元数据JSON';

-- =============================================
-- 第二部分：添加自由对练功能所需的新字段
-- =============================================

-- 9. 添加练习模式字段
ALTER TABLE pract_scene_set 
ADD COLUMN practice_mode VARCHAR(20) DEFAULT '剧本式' COMMENT '练习模式：剧本式/自由式';

-- 10. 添加知识库内容字段
ALTER TABLE pract_scene_set 
ADD COLUMN knowledge_base TEXT COMMENT '知识库内容（纯文本，支持换行）';

-- 11. 添加摘要信息字段
ALTER TABLE pract_scene_set 
ADD COLUMN summary_text TEXT COMMENT '摘要信息（格式：分类:要点，每行一个）';

-- 12. 添加考核范围字段
ALTER TABLE pract_scene_set 
ADD COLUMN exam_categories VARCHAR(200) COMMENT '考核范围（中文逗号分隔）';

-- 13. 添加评分规则字段
ALTER TABLE pract_scene_set 
ADD COLUMN scoring_rules TEXT COMMENT '评分规则说明（纯文本）';

-- =============================================
-- 第三部分：数据初始化
-- =============================================

-- 更新原有的 difficulty 字段默认值（如果存在旧数据）
UPDATE pract_scene_set SET difficulty = '简单' WHERE difficulty IS NULL;

-- =============================================
-- 查看更新后的表结构
-- =============================================
SHOW FULL COLUMNS FROM pract_scene_set;

-- =============================================
-- 迁移完成！
-- =============================================
