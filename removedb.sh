#!/bin/bash
# 删除数据库文件和迁移脚本

echo "正在删除数据库文件..."
rm -f src/data/*.*
echo "✅ 数据库文件已删除"

echo "正在删除迁移脚本..."
rm -f src/alembic/versions/*.*
echo "✅ 迁移脚本已删除"

echo "清理完成！"