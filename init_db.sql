-- 数据库表结构更新脚本
-- 添加时间戳字段到 Counters 表

-- 检查并添加 created_at 字段
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'Counters' AND column_name = 'created_at' 
     AND table_schema = DATABASE()) > 0,
    "SELECT 1",
    "ALTER TABLE `Counters` ADD COLUMN `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP"
));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加 updated_at 字段
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'Counters' AND column_name = 'updated_at' 
     AND table_schema = DATABASE()) > 0,
    "SELECT 1",
    "ALTER TABLE `Counters` ADD COLUMN `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;