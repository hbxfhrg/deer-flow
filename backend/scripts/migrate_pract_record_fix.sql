-- =============================================
-- 修复 pract_record 表结构：record_id 不应自增
-- 应存储 pract_course_record 的 id 字段
-- =============================================

-- 1. 创建临时表存储当前数据
CREATE TABLE IF NOT EXISTS pract_record_temp AS SELECT * FROM pract_record;

-- 2. 删除原表
DROP TABLE IF EXISTS pract_record;

-- 3. 重新创建表结构：
--    - id: 自增主键
--    - record_id: 存储 pract_course_record 的 id（非自增）
CREATE TABLE pract_record (
    id            INT         NOT NULL AUTO_INCREMENT  COMMENT '主键，自增',
    record_id     INT         NOT NULL                 COMMENT '关联 pract_course_record.id，非自增',
    course_id     INT         NOT NULL                 COMMENT '课程 ID',
    user_name     VARCHAR(50)                         COMMENT '用户名',
    total_score   DECIMAL(5,2) DEFAULT NULL            COMMENT '总分',
    duration      INT         DEFAULT NULL             COMMENT '对练总时长（秒）',
    dialog_rounds INT         DEFAULT NULL             COMMENT '实际对话轮数',
    report_data   JSON        DEFAULT NULL             COMMENT '报告数据',
    start_time    DATETIME    DEFAULT NULL             COMMENT '开始时间',
    end_time      DATETIME    DEFAULT NULL             COMMENT '结束时间',
    PRIMARY KEY (id),
    INDEX idx_record_id (record_id),
    INDEX idx_course_id (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对练记录表';

-- 4. 将数据迁移到新表
--    注意：现有数据的 record_id 可能不正确，需要后续手动修正或通过业务逻辑更新
INSERT INTO pract_record (
    record_id,
    course_id,
    user_name,
    total_score,
    duration,
    dialog_rounds,
    report_data,
    start_time,
    end_time
) SELECT
    record_id AS record_id,
    course_id,
    user_name,
    total_score,
    duration,
    dialog_rounds,
    report_data,
    start_time,
    end_time
FROM pract_record_temp;

-- 5. 删除临时表
DROP TABLE IF EXISTS pract_record_temp;

-- 6. 更新现有数据的 record_id 为对应的 pract_course_record.id
--    这里假设 record_id 应该与 pract_course_record.id 对应
--    如果无法自动对应，需要根据业务逻辑处理
UPDATE pract_record pr
JOIN pract_course_record pcr ON pr.course_id = pcr.course_id AND pr.user_name = pcr.user_name
SET pr.record_id = pcr.id
WHERE pr.record_id != pcr.id;

SELECT 'pract_record 表结构修复完成' AS result;
