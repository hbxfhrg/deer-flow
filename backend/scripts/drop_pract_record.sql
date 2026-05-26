-- =============================================
-- 删除废弃的 pract_record 表
-- pract_course_record 是实际的记录表，报告数据存储到其 summary 字段
-- =============================================

-- 删除废弃的 pract_record 表
DROP TABLE IF EXISTS pract_record;

SELECT 'pract_record 表已删除' AS result;
