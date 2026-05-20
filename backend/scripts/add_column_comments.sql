-- =============================================
-- 为已添加的字段补充中文注释
-- 适用于 MySQL 数据库
-- =============================================

-- 为新增字段添加注释
ALTER TABLE pract_scene_set MODIFY COLUMN practice_mode VARCHAR(20) DEFAULT '剧本式' COMMENT '练习模式：剧本式/自由式';

ALTER TABLE pract_scene_set MODIFY COLUMN knowledge_base TEXT COMMENT '知识库内容（纯文本，支持换行）';

ALTER TABLE pract_scene_set MODIFY COLUMN summary_text TEXT COMMENT '摘要信息（格式：分类:要点，每行一个）';

ALTER TABLE pract_scene_set MODIFY COLUMN exam_categories VARCHAR(200) COMMENT '考核范围（中文逗号分隔）';

ALTER TABLE pract_scene_set MODIFY COLUMN scoring_rules TEXT COMMENT '评分规则说明（纯文本）';

-- 查看更新后的表结构（包含注释）
SHOW FULL COLUMNS FROM pract_scene_set;

-- =============================================
-- 注释添加完成！
-- =============================================
