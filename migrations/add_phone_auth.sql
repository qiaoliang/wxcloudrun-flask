-- 手机认证功能数据库迁移脚本
-- 添加PhoneAuth表和User表的扩展字段

-- 创建手机认证表
CREATE TABLE IF NOT EXISTS `phone_auth` (
  `phone_auth_id` int NOT NULL AUTO_INCREMENT COMMENT '手机认证ID',
  `user_id` int NOT NULL COMMENT '关联的用户ID',
  `phone_number` varchar(20) NOT NULL COMMENT '加密后的手机号码',
  `password_hash` varchar(255) DEFAULT NULL COMMENT '密码哈希值',
  `auth_methods` enum('password','sms','both') NOT NULL DEFAULT 'sms' COMMENT '认证方式：password/sms/both',
  `is_verified` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否已验证',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否激活',
  `failed_attempts` int NOT NULL DEFAULT '0' COMMENT '连续失败次数',
  `locked_until` datetime DEFAULT NULL COMMENT '锁定到期时间',
  `last_login_at` datetime DEFAULT NULL COMMENT '最后登录时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`phone_auth_id`),
  UNIQUE KEY `phone_number` (`phone_number`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_is_verified` (`is_verified`),
  CONSTRAINT `fk_phone_auth_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='手机认证表';

-- 为users表添加认证类型字段
ALTER TABLE `users` 
ADD COLUMN IF NOT EXISTS `auth_type` enum('wechat','phone','both') NOT NULL DEFAULT 'wechat' COMMENT '认证类型：wechat/phone/both',
ADD COLUMN IF NOT EXISTS `linked_accounts` text DEFAULT NULL COMMENT '关联账户信息（JSON格式）';

-- 添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS `idx_users_auth_type` ON `users` (`auth_type`);

-- 创建触发器：自动更新updated_at字段
DELIMITER //
CREATE TRIGGER IF NOT EXISTS `phone_auth_before_update` 
BEFORE UPDATE ON `phone_auth` 
FOR EACH ROW 
BEGIN
    SET NEW.updated_at = CURRENT_TIMESTAMP;
END//
DELIMITER ;

-- 创建视图：用户认证信息视图
CREATE OR REPLACE VIEW `user_auth_view` AS
SELECT 
    u.user_id,
    u.wechat_openid,
    u.phone_number,
    u.nickname,
    u.auth_type,
    u.is_solo_user,
    u.is_supervisor,
    u.is_community_worker,
    u.status,
    pa.phone_auth_id,
    pa.auth_methods,
    pa.is_verified as phone_verified,
    pa.is_active as phone_active,
    pa.last_login_at,
    u.created_at,
    u.updated_at
FROM users u
LEFT JOIN phone_auth pa ON u.user_id = pa.user_id;

-- 插入一些示例数据（仅用于开发环境）
-- 注意：生产环境应该删除这些插入语句
INSERT IGNORE INTO `users` (`wechat_openid`, `nickname`, `auth_type`, `is_solo_user`, `status`) VALUES 
('phone_test_user_1', '测试用户1', 'phone', 1, 1),
('phone_test_user_2', '测试用户2', 'both', 0, 1);

-- 为测试用户创建手机认证记录（仅用于开发环境）
INSERT IGNORE INTO `phone_auth` (`user_id`, `phone_number`, `auth_methods`, `is_verified`) 
SELECT 
    user_id, 
    -- 这里使用加密的手机号，实际应用中应该使用真实的加密手机号
    'encrypted_13800138000', 
    'both', 
    1 
FROM users 
WHERE wechat_openid LIKE 'phone_test_user_%' 
AND user_id NOT IN (SELECT user_id FROM phone_auth);