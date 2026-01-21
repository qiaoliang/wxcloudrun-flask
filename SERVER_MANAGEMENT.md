# 服务器日志输出修复说明

## 问题
执行 `./localrun.sh` 后，服务器没有 log 输出到日志文件。

## 根本原因
1. 原脚本使用前台运行方式，日志直接输出到终端
2. 没有将标准输出和标准错误重定向到日志文件
3. 没有创建日志目录和日志文件

## 修复方案

### 修改的文件
- `localrun.sh` - 主启动脚本

### 新增的文件
- `stop.sh` - 停止服务脚本
- `viewlog.sh` - 查看日志脚本

## 使用方法

### 启动服务
```bash
cd backend
./localrun.sh
```

启动后会显示：
- 服务访问地址
- 日志文件路径
- 查看实时日志的命令
- 停止服务的命令

### 查看实时日志
```bash
# 查看最新的日志文件
./viewlog.sh

# 或直接使用 tail 命令
tail -f src/logs/server_YYYYMMDD_HHMMSS.log
```

### 停止服务
```bash
# 使用停止脚本
./stop.sh

# 或手动停止
kill $(cat src/logs/server.pid)

# 或根据端口停止
./stop.sh 9999
```

## 日志文件位置
- 路径: `backend/src/logs/`
- 命名格式: `server_YYYYMMDD_HHMMSS.log`
- 进程ID文件: `backend/src/logs/server.pid`

## 日志文件类型
应用会生成多个日志文件：
1. `server_*.log` - 服务器主日志（由 localrun.sh 创建）
2. `migration_*.log` - 数据库迁移日志（由 run.py 创建）
3. `app.log` - 应用日志（由 Flask 应用创建）
4. `app_service.log` - 应用服务日志
5. `scheduler.log` - 定时任务日志

## 技术细节

### localrun.sh 的改进
1. **创建日志目录**: `mkdir -p logs`
2. **生成带时间戳的日志文件名**: `server_YYYYMMDD_HHMMSS.log`
3. **后台运行**: 使用 `nohup ... &` 在后台运行服务
4. **重定向输出**: `> "${LOG_FILE}" 2>&1` 将标准输出和标准错误都重定向到日志文件
5. **保存进程ID**: `echo $! > logs/server.pid` 保存进程ID以便后续管理
6. **启动检查**: 检查进程是否成功启动并给出反馈

### 进程管理
- 使用 `nohup` 确保服务在终端关闭后继续运行
- 保存进程ID到 `server.pid` 文件
- 启动后等待3秒检查服务状态
- 提供清晰的启动成功/失败反馈

## 故障排查

### 服务启动失败
1. 查看日志文件: `cat src/logs/server_*.log`
2. 检查端口占用: `lsof -i:9999`
3. 检查虚拟环境: `source venv_py312/bin/activate`

### 日志文件未生成
1. 检查 logs 目录权限: `ls -la src/logs/`
2. 手动创建目录: `mkdir -p src/logs`

### 无法停止服务
1. 检查进程ID: `cat src/logs/server.pid`
2. 强制停止: `kill -9 $(cat src/logs/server.pid)`
3. 根据端口查找: `lsof -ti:9999 | xargs kill`