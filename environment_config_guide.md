# 环境配置指南

## 📋 配置层级结构

```
配置读取流程:
├── 1. ENV_TYPE环境变量 (Docker控制)
└── 2. config.py: 加载.env.{ENV_TYPE}文件
```

## 🔧 环境配置详情

### 🏭 生产环境 (prod)
- **Docker配置**: `ENV_TYPE=prod`
- **环境文件**: `.env.prod`
- **数据库**: 外部MySQL服务
  - 地址: `10.18.105.216:3306`
  - 用户名: `root`
  - 密码: `4tAF2rTC`
  - 数据库名: `flask_demo`

### 🧪 功能测试环境 (function)
- **Docker配置**: `ENV_TYPE=function`
- **环境文件**: `.env.function`
- **数据库**: Docker内部MySQL
  - 地址: `mysql-db:3306`
  - 用户名: `root`
  - 密码: `rootpassword`
  - 数据库名: `flask_demo`

### 🧪 单元测试环境 (unit)
- **Docker配置**: 不需要（本地运行）
- **环境文件**: `.env.unit`
- **数据库**: SQLite内存数据库
  - 地址: `memory`
  - 用于快速测试，无需外部依赖

## 🚀 使用方法

### 启动生产环境（使用外部MySQL）
```bash
# 启动完整服务（包含Docker MySQL）
docker-compose up --build -d

# 仅启动应用（使用外部MySQL）
docker-compose up --build app redis
```

### 启动功能测试环境（使用Docker MySQL）
```bash
# 启动完整测试环境
docker-compose -f docker-compose.dev.yml up --build -d
```

### 本地单元测试
```bash
# 运行单元测试
ENV_TYPE=unit python -m pytest tests/
```

## ⚠️ 注意事项

1. **外部MySQL**: 确保`10.18.105.216:3306`上的MySQL服务可访问
2. **Docker网络**: 生产环境下Docker容器可以访问外部MySQL
3. **环境变量**: 只有`ENV_TYPE`由Docker控制，其他配置来自`.env`文件
4. **配置覆盖**: Docker环境变量优先级高于`.env`文件

## 🔍 验证配置

```bash
# 检查当前环境
echo $ENV_TYPE

# 验证数据库连接
python3 final_sqlite_diagnosis.py

# 测试API功能
curl http://localhost:8080/api/count
```

## 📊 SQLite错误解决状态

✅ **问题根源**: ENV_TYPE未设置，导致使用`.env.unit`（SQLite配置）
✅ **解决方案**: 正确设置环境变量，应用自动加载对应配置
✅ **生产环境**: 使用外部MySQL (`10.18.105.216:3306`)
✅ **测试环境**: 使用Docker MySQL (`mysql-db:3306`)

不再会有SQLite配置错误！🎉