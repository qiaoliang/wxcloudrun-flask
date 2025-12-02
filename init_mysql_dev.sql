-- MySQL 8.4.3 开发环境初始化脚本
-- 解决 root 用户认证问题

-- 创建用户并设置密码（如果不存在）
CREATE USER IF NOT EXISTS 'root'@'%' IDENTIFIED BY '${MYSQL_PASSWORD:-rootpassword}';

-- 授予权限
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

-- 刷新权限
FLUSH PRIVILEGES;