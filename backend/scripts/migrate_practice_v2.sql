-- =============================================
-- 自由式对练引擎：新建对话详情表
-- =============================================
-- 注意：pract_record 表已包含 course_id、report_data、total_score 等字段，无需修改

CREATE TABLE IF NOT EXISTS pract_dialog_detail (
    dialog_id    BIGINT      NOT NULL AUTO_INCREMENT  COMMENT '对话 ID，主键',
    record_id    INT         NOT NULL                 COMMENT '所属对练记录 ID（关联 pract_record.record_id）',
    speaker      TINYINT     NOT NULL                 COMMENT '发言者（1: 学员，2: AI/客户）',
    content_type TINYINT     NOT NULL DEFAULT 1       COMMENT '内容类型（1: 文本，2: 音频 URL）',
    content      TEXT         NOT NULL                COMMENT '发言内容（文本或音频 OSS 地址）',
    round_number INT         NOT NULL DEFAULT 0       COMMENT '所属轮次编号（从1开始）',
    score        DECIMAL(5,2) DEFAULT NULL            COMMENT '该句得分（仅学员发言有值）',
    feedback     TEXT         DEFAULT NULL            COMMENT 'AI 对该句的即时反馈（仅学员发言有值）',
    create_time  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '发言时间',
    PRIMARY KEY (dialog_id),
    INDEX idx_record_id (record_id),
    INDEX idx_round (record_id, round_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='对话详情表';
