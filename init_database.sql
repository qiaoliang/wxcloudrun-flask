-- 安全守护项目数据库初始化脚本
-- 创建数据库和所有表结构

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS flask_demo 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE flask_demo;

-- 删除已存在的表（谨慎使用，仅用于完全重建）
-- DROP TABLE IF EXISTS checkin_records;
-- DROP TABLE IF EXISTS checkin_rules;
-- DROP TABLE IF EXISTS users;
-- DROP TABLE IF EXISTS Counters;

-- 1. 创建计数器表
CREATE TABLE IF NOT EXISTS Counters (
    id INT PRIMARY KEY AUTO_INCREMENT,
    count INT DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='计数器表';

-- 2. 创建用户表
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    wechat_openid VARCHAR(128) NOT NULL UNIQUE COMMENT '微信OpenID，唯一标识用户',
    phone_number VARCHAR(20) UNIQUE COMMENT '手机号码，可用于登录和联系',
    nickname VARCHAR(100) COMMENT '用户昵称',
    avatar_url VARCHAR(500) COMMENT '用户头像URL',
    name VARCHAR(100) COMMENT '真实姓名',
    work_id VARCHAR(50) COMMENT '工号或身份证号',
    
    -- 用户权限字段，支持多身份组合
    is_solo_user BOOLEAN DEFAULT TRUE COMMENT '是否为独居者（有打卡规则和记录）',
    is_supervisor BOOLEAN DEFAULT FALSE COMMENT '是否为监护人（有关联的监护关系）',
    is_community_worker BOOLEAN DEFAULT FALSE COMMENT '是否为社区工作人员（需要身份验证）',
    
    -- 兼容性字段，暂时保留
    role INT DEFAULT 1 COMMENT '兼容性字段：1-独居者/2-监护人/3-社区工作人员',
    
    -- 状态: 1-正常, 2-禁用
    status INT DEFAULT 1 COMMENT '用户状态：1-正常/2-禁用',
    
    -- 验证状态: 0-未申请, 1-待审核, 2-已通过, 3-已拒绝
    verification_status INT DEFAULT 0 COMMENT '验证状态：0-未申请/1-待审核/2-已通过/3-已拒绝',
    verification_materials TEXT COMMENT '验证材料URL',
    
    community_id INT COMMENT '所属社区ID，仅社区工作人员需要',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 3. 创建打卡规则表
CREATE TABLE IF NOT EXISTS checkin_rules (
    rule_id INT PRIMARY KEY AUTO_INCREMENT,
    solo_user_id INT NOT NULL COMMENT '独居者用户ID',
    rule_name VARCHAR(100) NOT NULL COMMENT '打卡规则名称，如：起床打卡、早餐打卡等',
    icon_url VARCHAR(500) COMMENT '打卡事项图标URL',
    
    -- 频率类型: 0-每天, 1-每周, 2-工作日, 3-自定义
    frequency_type INT NOT NULL DEFAULT 0 COMMENT '打卡频率类型：0-每天/1-每周/2-工作日/3-自定义',
    
    -- 时间段类型: 1-上午, 2-下午, 3-晚上, 4-自定义时间
    time_slot_type INT NOT NULL DEFAULT 4 COMMENT '时间段类型：1-上午/2-下午/3-晚上/4-自定义时间',
    
    -- 自定义时间（当time_slot_type为4时使用）
    custom_time TIME COMMENT '自定义打卡时间',
    
    -- 一周中的天（当frequency_type为1时使用，使用位掩码表示周几）
    week_days INT DEFAULT 127 COMMENT '一周中的天（位掩码表示）：默认127表示周一到周日',
    
    -- 规则状态：1-启用, 0-禁用
    status INT DEFAULT 1 COMMENT '规则状态：1-启用/0-禁用',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (solo_user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='打卡规则表';

-- 4. 创建打卡记录表
CREATE TABLE IF NOT EXISTS checkin_records (
    record_id INT PRIMARY KEY AUTO_INCREMENT,
    rule_id INT NOT NULL COMMENT '打卡规则ID',
    solo_user_id INT NOT NULL COMMENT '独居者用户ID',
    checkin_time DATETIME COMMENT '实际打卡时间',
    
    -- 状态: 1-checked(已打卡), 0-missed(未打卡), 2-revoked(已撤销)
    status INT DEFAULT 0 COMMENT '状态：0-未打卡/1-已打卡/2-已撤销',
    
    planned_time DATETIME NOT NULL COMMENT '计划打卡时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    FOREIGN KEY (rule_id) REFERENCES checkin_rules(rule_id) ON DELETE CASCADE,
    FOREIGN KEY (solo_user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='打卡记录表';

-- 创建索引以提高查询性能

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_openid ON users(wechat_openid);
CREATE INDEX IF NOT EXISTS idx_phone ON users(phone_number);
CREATE INDEX IF NOT EXISTS idx_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_verification_status ON users(verification_status);

-- 打卡规则表索引
CREATE INDEX IF NOT EXISTS idx_solo_user_rules ON checkin_rules(solo_user_id);
CREATE INDEX IF NOT EXISTS idx_frequency_type ON checkin_rules(frequency_type);
CREATE INDEX IF NOT EXISTS idx_time_slot_type ON checkin_rules(time_slot_type);
CREATE INDEX IF NOT EXISTS idx_rule_status ON checkin_rules(status);

-- 打卡记录表索引
CREATE INDEX IF NOT EXISTS idx_rule_records ON checkin_records(rule_id);
CREATE INDEX IF NOT EXISTS idx_solo_user_records ON checkin_records(solo_user_id);
CREATE INDEX IF NOT EXISTS idx_planned_time ON checkin_records(planned_time);
CREATE INDEX IF NOT EXISTS idx_checkin_time ON checkin_records(checkin_time);
CREATE INDEX IF NOT EXISTS idx_record_status ON checkin_records(status);

-- 插入初始数据

-- 初始化计数器
INSERT INTO Counters (count) VALUES (1) ON DUPLICATE KEY UPDATE count = 1;

-- 插入示例用户（可选）
-- INSERT INTO users (wechat_openid, nickname, is_solo_user, role, status) 
-- VALUES ('test_openid_123', '测试用户', TRUE, 1, 1);

-- 插入默认打卡规则示例（可选）
-- INSERT INTO checkin_rules (solo_user_id, rule_name, frequency_type, time_slot_type, custom_time, status)
-- VALUES (1, '起床打卡', 0, 4, '08:00:00', 1);

-- 显示创建的表
SHOW TABLES;

-- 显示表结构
DESCRIBE Counters;
DESCRIBE users;
DESCRIBE checkin_rules;
DESCRIBE checkin_records;

-- 完成提示
SELECT '数据库和表结构创建完成！' AS message;