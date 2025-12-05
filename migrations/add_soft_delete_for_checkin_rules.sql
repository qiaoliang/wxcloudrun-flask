-- 添加打卡规则软删除支持
-- 创建时间: 2025-12-05
-- 描述: 为 checkin_rules 表添加 deleted_at 字段，支持软删除功能

-- 添加 deleted_at 字段
ALTER TABLE checkin_rules ADD COLUMN deleted_at DATETIME NULL COMMENT '删除时间';

-- 添加状态字段索引，优化查询性能
CREATE INDEX idx_checkin_rules_status ON checkin_rules(status);

-- 更新表注释
ALTER TABLE checkin_rules COMMENT='打卡规则表，支持软删除（status=2表示已删除）';

-- 回滚脚本（如果需要回滚）：
-- DROP INDEX idx_checkin_rules_status ON checkin_rules;
-- ALTER TABLE checkin_rules DROP COLUMN deleted_at;