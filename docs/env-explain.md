# SafeGuard 后端环境变量说明文档

## 1. 环境概述

SafeGuard 后端支持4种环境：

| 环境 | ENV_TYPE | 用途 | 数据库 | 调试模式 |
|------|----------|------|--------|----------|
| 单元测试 | unit | 单元测试 | 内存数据库 | 开启 |
| 功能测试 | function | 功能测试 | SQLite文件 | 开启 |
| UAT测试 | uat | 用户验收测试 | SQLite文件 | 开启 |
| 生产环境 | prod | 生产部署 | SQLite文件 | 关闭 |

## 2. 核心配置变量

### 2.1 环境类型（必需）

```bash
ENV_TYPE=unit|function|uat|prod
```

**用途**：决定应用的运行环境和配置加载策略

**影响**：
- 数据库类型和路径
- 调试模式开关
- 外部服务（微信、短信）使用真实或模拟模式
- 后台任务是否启动

**默认值**：unit

**配置文件位置**：`src/config_manager.py:16`

**使用位置**：全局配置管理

---

### 2.2 JWT Token密钥（生产环境必需）

```bash
TOKEN_SECRET=<your-secret-key>
```

**用途**：JWT Token签名和验证

**影响范围**：
- 用户登录认证
- API请求鉴权
- Token刷新机制

**必需性**：
- unit/function/uat：有默认值用于测试
- prod：必须配置，否则抛出异常

**默认值**：
- 测试环境：`42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f`

**使用位置**：
- `src/config_manager.py:155`
- `src/app/shared/utils/auth.py`

---

### 2.3 微信小程序配置（生产环境必需）

```bash
WX_APPID=<your-wechat-appid>
WX_SECRET=<your-wechat-secret>
```

**用途**：微信小程序登录认证

**影响范围**：
- 微信code换取openid
- 用户身份验证
- 账号绑定

**必需性**：
- unit/function/uat：使用Mock API，可配置虚假值
- prod：必须配置真实值

**默认值**：
- 测试环境：`test_appid`, `test_secret`
- UAT环境：`wx55a59cbcd4156ce4`, `33b5b2062d2f93c87e9a9eed9e7c952f`

**使用位置**：
- `src/config.py:21-22`
- `src/wxcloudrun/wxchat_api.py`

---

## 3. 数据库配置变量

### 3.1 SQLite数据库路径（可选）

```bash
SQLITE_DB_PATH=/path/to/database.db
```

**用途**：自定义SQLite数据库文件路径

**默认行为**：
- unit：内存数据库 `sqlite:///:memory:`
- function：`src/data/function.db`
- uat：`src/data/uat.db`
- prod：`/app/data/prod.db`

**使用位置**：`src/config_manager.py:67`

---

### 3.2 SQL调试模式（可选）

```bash
SQL_DEBUG=true|false
```

**用途**：启用SQL语句日志输出

**默认值**：False

**使用位置**：`src/config.py:17`

---

### 3.3 数据库连接池配置（可选）

```bash
DB_POOL_SIZE=10
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true
```

**用途**：配置数据库连接池参数

**默认值**：
- function：5, 3600, true
- uat/prod：10, 3600, true

**注意**：这些变量在配置文件中定义，但未在代码中实际使用

---

### 3.4 数据库重试配置（可选）

```bash
DB_RETRY_COUNT=5
DB_RETRY_DELAY=2.0
```

**用途**：数据库操作失败时的重试策略

**默认值**：
- function：3, 1.0
- uat/prod：5, 2.0

**注意**：这些变量在配置文件中定义，但未在代码中实际使用

---

## 4. Redis配置变量

### 4.1 Redis连接配置（可选）

```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

**用途**：Redis缓存服务连接配置

**默认值**：
- unit：使用 fakeredis（内存模拟）
- 其他：localhost:6379, 无密码

**使用位置**：`src/config_manager.py:195-198`

**注意**：Redis配置存在但项目中未完全使用

---

## 5. 短信服务配置变量

### 5.1 短信服务提供商（可选）

```bash
SMS_PROVIDER=real|mock|simulation
```

**用途**：选择短信服务模式

**行为**：
- `real`：使用真实短信服务
- `mock`：使用模拟短信服务
- `simulation`：使用模拟短信服务（与mock相同）
- 未设置：根据环境判断（uat/prod用真实，其他用模拟）

**默认值**：
- unit：simulation
- function：simulation
- uat：real
- prod：mock

**大小写**：不区分大小写（mock/Mock/MOCK 都有效）

**使用位置**：
- `src/config_manager.py:137`
- `src/wxcloudrun/sms_service.py`

---

### 5.2 短信API配置（真实模式必需）

```bash
SMS_API_KEY=<your-sms-api-key>
SMS_API_SECRET=<your-sms-api-secret>
SMS_API_URL=https://api.sms-service.com/send
```

**用途**：真实短信服务API配置

**必需性**：仅当 `SMS_PROVIDER=real` 时必需

**使用位置**：`src/wxcloudrun/sms_service.py:26-28`

---

## 6. 安全配置变量

### 6.1 手机号加密密钥（可选）

```bash
PHONE_ENC_SECRET=<your-phone-encryption-secret>
```

**用途**：手机号哈希加密

**影响范围**：
- 手机号存储
- 手机号查询
- 隐私保护

**默认值**：default_secret

**使用位置**：
- `src/wxcloudrun/user_service.py:34`
- `src/wxcloudrun/utils/validators.py:144`
- `src/database/initialization.py:42`
- `src/app/modules/user/routes.py:37`
- `src/app/modules/community/routes.py:32`
- `src/app/modules/auth/routes.py:444,523,597,691`

---

### 6.2 Flask会话密钥（可选）

```bash
SECRET_KEY=<your-flask-secret-key>
```

**用途**：Flask会话加密

**默认值**：dev_secret_key

**使用位置**：`src/app/__init__.py:63`

---

## 7. 应用配置变量

### 7.1 Flask调试模式（自动设置）

```bash
DEBUG=true|false
```

**用途**：Flask调试模式开关

**默认行为**：
- unit/function/uat：true
- prod：false

**注意**：此变量由 `ENV_TYPE` 自动设置，不建议手动修改

---

## 8. 业务配置变量

### 8.1 验证码过期时间（可选）

```bash
CONFIG_VERIFICATION_CODE_EXPIRY=5
```

**用途**：短信验证码有效期（分钟）

**默认值**：5

**使用位置**：`src/wxcloudrun/utils/validators.py:44`

---

### 8.2 打卡宽限期（可选）

```bash
MISS_GRACE_MINUTES=0
```

**用途**：打卡超时后的宽限期（分钟）

**默认值**：0

**使用位置**：
- `src/wxcloudrun/background_tasks.py:63,119`

---

### 8.3 未打卡检查间隔（可选）

```bash
MISS_CHECK_INTERVAL_MINUTES=5
```

**用途**：后台检查未打卡任务的间隔（分钟）

**默认值**：5

**使用位置**：`src/wxcloudrun/background_tasks.py:211`

---

## 9. 邮件服务配置变量（可选）

```bash
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=user@example.com
MAIL_PASSWORD=password
MAIL_USE_TLS=true
```

**用途**：邮件服务配置

**状态**：配置存在但未在代码中实际使用

---

## 10. 系统内部变量

### 10.1 Flask重启检测（系统自动设置）

```bash
WERKZEUG_RUN_MAIN=true|false
```

**用途**：Flask调试器重启检测

**说明**：由Flask自动设置，用于区分主进程和重启进程

**使用位置**：
- `src/run.py:58,96`
- `src/app/__init__.py:125,189,192`

---

## 11. 环境配置文件位置

| 环境 | 配置文件 | 位置 |
|------|----------|------|
| 单元测试 | .env.unit | `src/.env.unit` |
| 功能测试 | .env.function | `src/.env.function` |
| UAT测试 | .env.uat | `src/.env.uat` |
| 生产环境 | .env.prod | `src/.env.prod` |

---

## 12. Docker部署环境变量

### 12.1 Function环境

```bash
docker run -d \
  --name s-function \
  -p 9999:9999 \
  -e ENV_TYPE=function \
  safeguard-function-img
```

### 12.2 UAT环境

```bash
docker run -d \
  --name s-uat \
  -p 8081:8081 \
  -e ENV_TYPE=uat \
  -e WX_APPID=<your-appid> \
  -e WX_SECRET=<your-secret> \
  -e TOKEN_SECRET=<your-token-secret> \
  safeguard-uat-img
```

### 12.3 生产环境

```bash
docker run -d \
  --name s-prod \
  -p 8080:8080 \
  -e ENV_TYPE=prod \
  -e WX_APPID=<your-appid> \
  -e WX_SECRET=<your-secret> \
  -e TOKEN_SECRET=<your-token-secret> \
  safeguard-prod-img
```

---

## 13. 环境变量优先级

1. **系统环境变量**（Docker传入或export设置）
2. **环境特定配置文件**（`.env.{ENV_TYPE}`）
3. **默认值**（代码中的默认值）

**注意**：`config_manager.py` 使用 `override=False`，不会覆盖已存在的环境变量

---

## 14. 安全建议

1. **生产环境必须配置**：
   - `TOKEN_SECRET`：使用强随机密钥
   - `WX_APPID` 和 `WX_SECRET`：使用真实微信配置
   - `PHONE_ENC_SECRET`：使用强随机密钥

2. **敏感变量保护**：
   - 不要将 `.env.prod` 提交到版本控制
   - 使用 Docker secrets 或环境变量管理工具
   - 定期轮换密钥

3. **测试环境隔离**：
   - 测试环境使用独立的微信小程序配置
   - 测试环境使用模拟短信服务
   - 测试数据库与生产数据库完全隔离

---

## 15. 常见问题

### 15.1 ENV_TYPE未设置

**错误**：启动时提示 "ENV_TYPE 环境变量未设置"

**解决**：
```bash
export ENV_TYPE=function
# 或
docker run -e ENV_TYPE=function ...
```

### 15.2 TOKEN_SECRET未设置

**错误**：生产环境启动失败，提示 "TOKEN_SECRET 环境变量未设置或为空"

**解决**：
```bash
export TOKEN_SECRET=$(openssl rand -hex 32)
# 或
docker run -e TOKEN_SECRET=$(openssl rand -hex 32) ...
```

### 15.3 微信API调用失败

**错误**：微信登录返回错误

**解决**：
- 检查 `WX_APPID` 和 `WX_SECRET` 是否正确
- 检查网络连接
- 检查微信小程序配置是否匹配

### 15.4 短信发送失败

**错误**：短信发送失败

**解决**：
- 检查 `SMS_PROVIDER` 配置
- 如果使用真实短信，检查 `SMS_API_KEY` 和 `SMS_API_SECRET`
- 测试环境可以使用 `SMS_PROVIDER=mock`

---

## 16. 配置验证

项目提供了配置验证工具：

```bash
# 查看当前环境配置
curl http://localhost:9999/api/env

# 查看外部系统状态
curl http://localhost:9999/api/external-systems-status
```

---

## 17. 环境变量关联关系图

```
ENV_TYPE (环境类型)
    ├── 数据库配置
    │   ├── unit → 内存数据库
    │   ├── function → src/data/function.db
    │   ├── uat → src/data/uat.db
    │   └── prod → /app/data/prod.db
    │
    ├── DEBUG模式
    │   ├── unit → true
    │   ├── function → true
    │   ├── uat → true
    │   └── prod → false
    │
    ├── 微信API模式
    │   ├── unit → Mock
    │   ├── function → Mock
    │   ├── uat → Mock
    │   └── prod → Real (需配置WX_APPID, WX_SECRET)
    │
    ├── 短信服务模式
    │   ├── SMS_PROVIDER=real → 真实服务
    │   ├── SMS_PROVIDER=mock → 模拟服务
    │   └── 默认 → uat/prod用真实，其他用模拟
    │
    └── 后台任务
        ├── unit → 不启动
        └── 其他 → 启动 (依赖MISS_GRACE_MINUTES, MISS_CHECK_INTERVAL_MINUTES)
```

---

## 18. 环境变量完整列表

| 变量名 | 用途 | 默认值 | 必需 | 影响范围 |
|--------|------|--------|------|----------|
| `ENV_TYPE` | 环境类型 | unit | 否 | 全局配置 |
| `TOKEN_SECRET` | JWT Token密钥 | 测试密钥 | 是（生产） | 认证系统 |
| `WX_APPID` | 微信小程序AppID | test_appid | 是（生产） | 微信登录 |
| `WX_SECRET` | 微信小程序Secret | test_secret | 是（生产） | 微信登录 |
| `SQLITE_DB_PATH` | SQLite数据库路径 | 自动设置 | 否 | 数据库 |
| `SQL_DEBUG` | SQL调试模式 | False | 否 | 数据库日志 |
| `DB_POOL_SIZE` | 数据库连接池大小 | 5-10 | 否 | 数据库 |
| `DB_POOL_RECYCLE` | 连接池回收时间 | 3600 | 否 | 数据库 |
| `DB_POOL_PRE_PING` | 连接池预检测 | true | 否 | 数据库 |
| `DB_RETRY_COUNT` | 数据库重试次数 | 3-5 | 否 | 数据库 |
| `DB_RETRY_DELAY` | 数据库重试延迟 | 1.0-2.0 | 否 | 数据库 |
| `REDIS_HOST` | Redis主机地址 | localhost | 否 | 缓存服务 |
| `REDIS_PORT` | Redis端口 | 6379 | 否 | 缓存服务 |
| `REDIS_PASSWORD` | Redis密码 | 空 | 否 | 缓存服务 |
| `REDIS_DB` | Redis数据库编号 | 0 | 否 | 缓存服务 |
| `SMS_PROVIDER` | 短信服务提供商 | simulation | 否 | 短信服务 |
| `SMS_API_KEY` | 短信API密钥 | 空 | 否（真实模式） | 短信服务 |
| `SMS_API_SECRET` | 短信API密钥 | 空 | 否（真实模式） | 短信服务 |
| `SMS_API_URL` | 短信API地址 | 默认URL | 否（真实模式） | 短信服务 |
| `PHONE_ENC_SECRET` | 手机号加密密钥 | default_secret | 否 | 手机号加密 |
| `SECRET_KEY` | Flask会话密钥 | dev_secret_key | 否 | 会话管理 |
| `CONFIG_VERIFICATION_CODE_EXPIRY` | 验证码过期时间 | 5 | 否 | 验证码 |
| `MISS_GRACE_MINUTES` | 打卡宽限期 | 0 | 否 | 打卡任务 |
| `MISS_CHECK_INTERVAL_MINUTES` | 未打卡检查间隔 | 5 | 否 | 打卡任务 |
| `MAIL_SERVER` | 邮件服务器 | 空 | 否 | 邮件服务 |
| `MAIL_PORT` | 邮件端口 | 空 | 否 | 邮件服务 |
| `MAIL_USERNAME` | 邮件用户名 | 空 | 否 | 邮件服务 |
| `MAIL_PASSWORD` | 邮件密码 | 空 | 否 | 邮件服务 |
| `MAIL_USE_TLS` | 是否使用TLS | false | 否 | 邮件服务 |
| `WERKZEUG_RUN_MAIN` | Flask重启检测 | 系统设置 | 否 | Flask调试 |

---

**文档版本**：1.0  
**最后更新**：2025-12-31  
**维护者**：SafeGuard 开发团队