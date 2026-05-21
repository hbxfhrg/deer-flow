-- ============================================
-- 给 pract_course 表添加 create_by 列
-- 数据库: demo_dev_gp (阿里云 RDS)
-- ============================================

USE demo_dev_gp;

-- 添加创建人列（与 Scene 表的 create_by 保持一致）
ALTER TABLE pract_course 
  ADD COLUMN create_by VARCHAR(50) NOT NULL DEFAULT '';
