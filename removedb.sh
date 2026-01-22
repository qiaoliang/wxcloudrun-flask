#!/bin/bash
# 删除数据库文件、迁移脚本和日志文件

echo "正在删除数据库文件..."
rm -f src/data/*.*
echo "✅ 数据库文件已删除"

echo "正在删除迁移脚本..."
rm -f src/alembic/versions/*.*
echo "✅ 迁移脚本已删除"

echo "正在删除当前目录下的 logs 子目录文件..."
rm -f logs/*.*
echo "✅ 当前目录下的 logs 子目录文件已删除"

echo "正在删除 src/logs 子目录文件..."
rm -f src/logs/*.*
echo "✅ src/logs 子目录文件已删除"

echo "清理完成！"