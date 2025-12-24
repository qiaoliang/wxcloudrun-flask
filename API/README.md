# SafeGuard 后端 API 文档

## 概述

本目录包含 SafeGuard 后端服务的 API 文档，按功能域进行组织。每个功能域对应一个独立的 Markdown 文件，详细描述了该域的所有 API 接口。

## 文档结构

### 按功能域划分的 API 文档

| 功能域 | 文档文件 | 描述 |
|--------|----------|------|
| **认证域** | [API_auth.md](API_auth.md) | 用户身份验证、登录、注册、token管理 |
| **用户管理域** | [API_user.md](API_user.md) | 用户信息管理、用户搜索、账号绑定 |
| **社区管理域** | [API_community.md](API_community.md) | 社区CRUD、工作人员管理、申请处理 |
| **打卡功能域** | [API_checkin.md](API_checkin.md) | 打卡规则管理、打卡记录、历史查询 |
| **用户打卡域** | [API_user_checkin.md](API_user_checkin.md) | 用户个人打卡规则、今日计划、统计信息 |
| **短信服务域** | [API_sms.md](API_sms.md) | 验证码发送和验证 |
| **监督功能域** | [API_supervision.md](API_supervision.md) | 监督关系管理、监督邀请、监督记录 |
| **分享功能域** | [API_share.md](API_share.md) | 分享链接创建、解析和页面渲染 |
| **其他功能域** | [API_misc.md](API_misc.md) | 计数器、环境配置、首页等辅助功能 |

### 文档格式规范

每个 API 文档包含以下部分：

1. **概述** - 功能域的简要描述
2. **API 列表** - 所有接口的详细说明，包括：
   - 端点 (Endpoint)
   - HTTP 方法
   - 描述
   - 请求参数（查询参数、请求体）
   - 响应格式
   - 错误码（如果有）
3. **参数说明** - 特殊参数的详细解释
4. **权限说明** - 接口的访问权限要求
5. **相关文件** - 对应的源代码文件

## 通用约定

### 响应格式

所有 API 接口使用统一的响应格式：

```json
{
  "code": 1,        // 1-成功，0-失败
  "msg": "success", // 状态消息
  "data": {...}     // 响应数据
}
```

### 认证方式

需要认证的接口使用 Bearer Token 认证：

```
Authorization: Bearer <token>
```

### 错误处理

- **HTTP 状态码**: 统一返回 200
- **业务状态**: 通过响应体中的 `code` 字段判断（1-成功，0-失败）
- **错误消息**: 在 `msg` 字段中返回具体的错误信息

## 快速导航

### 核心功能

1. **用户认证**
   - 微信登录: `POST /api/auth/login_wechat`
   - 手机号注册: `POST /api/auth/register_phone`
   - Token刷新: `POST /api/refresh_token`

2. **用户管理**
   - 获取用户信息: `GET /api/user/profile`
   - 搜索用户: `GET /api/users/search`
   - 绑定手机号: `POST /api/user/bind_phone`

3. **社区管理**
   - 获取社区列表: `GET /api/community/list`
   - 社区用户管理: `GET /api/communities/{id}/users`
   - 社区申请: `POST /api/community/applications`

4. **打卡功能**
   - 今日打卡事项: `GET /api/checkin/today`
   - 执行打卡: `POST /api/checkin`
   - 打卡规则管理: `GET/POST/PUT/DELETE /api/checkin/rules`

5. **用户打卡功能**
   - 今日打卡计划: `GET /api/user-checkin/today-plan`
   - 用户打卡规则: `GET /api/user-checkin/rules`
   - 打卡统计: `GET /api/user-checkin/statistics`

6. **监督功能**
   - 邀请监督者: `POST /api/rules/supervision/invite`
   - 获取监督邀请: `GET /api/rules/supervision/invitations`
   - 获取监督记录: `GET /api/rules/supervision/records`

### 辅助功能

1. **短信服务**
   - 发送验证码: `POST /api/sms/send_code`

2. **分享功能**
   - 创建分享链接: `POST /api/share/checkin/create`
   - 解析分享链接: `GET /api/share/checkin/resolve`

3. **系统功能**
   - 环境配置: `GET /api/get_envs`
   - 计数器: `GET/POST /api/count`

## 开发指南

### 环境配置

项目支持多环境配置，通过 `ENV_TYPE` 环境变量控制：

- **function**: 开发环境
- **unit**: 单元测试环境（内存数据库）
- **uat**: UAT测试环境
- **prod**: 生产环境

### 本地开发

1. 设置环境变量：
   ```bash
   export ENV_TYPE=function
   ```

2. 启动开发服务器：
   ```bash
   ./localrun.sh
   ```

3. 访问服务：
   - API服务: http://localhost:9999
   - 环境配置查看器: http://localhost:9999/env

### 测试

```bash
# 运行所有测试
make test-all

# 运行单元测试
make ut

# 运行集成测试
make test-integration

# 运行端到端测试
make e2e
```

## 相关资源

- **项目指南**: [../AGENTS.md](../AGENTS.md)
- **源代码**: [../src/app/modules/](../src/app/modules/) (Blueprint 架构)
- **业务服务**: [../src/wxcloudrun/](../src/wxcloudrun/) (服务层)
- **测试目录**: [../tests/](../tests/)
- **部署脚本**: [../scripts/](../scripts/)

## 更新日志

### 2025-12-24
- 更新文档以反映 Blueprint 模块化架构
- 源代码路径从 wxcloudrun/views 迁移到 app/modules
- 更新贡献指南以匹配新的架构
- 新增用户打卡功能域 API 文档 (API_user_checkin.md)
- 更新 API 路径以反映修复后的 Blueprint 路由结构

### 2025-12-19
- 初始版本，按功能域梳理所有 API 接口
- 创建 8 个功能域的详细 API 文档
- 建立统一的文档结构和格式规范

## 贡献指南

如需更新 API 文档，请遵循以下步骤：

1. 修改对应的 Blueprint 路由文件（`backend/src/app/modules/*/routes.py`）
2. 更新对应的业务服务文件（`backend/src/wxcloudrun/*_service.py`）
3. 更新对应的 API 文档文件（`backend/API/API_*.md`）
3. 确保文档格式符合规范
4. 更新本 README 文件中的相关部分

## 联系方式

如有问题或建议，请查看项目文档或联系开发团队。