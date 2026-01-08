echo '#### 清理数据库文件和迁移脚本…………  ####'
rm -rf ./src/alembic/versions/*.*

# 备份数据库文件而不是删除
if [ -d "./src/data" ]; then
    for db_file in ./src/data/*.db; do
        if [ -f "$db_file" ]; then
            # 使用可读的时间戳格式：YYYY-MM-DD_HH-MM-SS
            timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
            filename=$(basename "$db_file")
            backup_name="./src/data/${filename}.backup_${timestamp}"
            echo "备份数据库文件: $db_file -> $backup_name"
            mv "$db_file" "$backup_name"
        fi
    done
else
    echo "数据库目录不存在: ./src/data"
fi
