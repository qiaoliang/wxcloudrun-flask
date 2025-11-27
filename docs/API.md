# 安全守护后端API文档

## 概述

安全守护后端API基于Flask框架开发，为独居者安全监护服务提供完整的后端支持。API采用RESTful设计风格，所有响应都遵循统一的JSON格式。

## 基础信息

- **基础URL**: `http://localhost:8080`
- **API版本**: v1
- **数据格式**: JSON
- **字符编码**: UTF-8

## 响应格式

所有API响应都遵循以下统一格式：

### 成功响应
```json
{
  "code": 1,
  "data": {}, 
  "msg": "success"
}
```

### 错误响应
```json
{
  "code": 0,
  "data": {},
  "msg": "error message"
}
```

# API接口列表

## 已实现的API接口

### 1. 计数器接口

#### 1.1 获取计数

**状态**: ✅ 已实现  
**接口地址**: `GET /api/count`  
**接口描述**: 获取当前计数值  
**请求参数**: 无  
**响应示例**:
```json
{
  "code": 1,
  "data": 42,
  "msg": "success"
}
```

#### 1.2 更新计数

**状态**: ✅ 已实现  
**接口地址**: `POST /api/count`  
**接口描述**: 更新计数值（自增或清零）  
**请求参数**:
```json
{
  "action": "inc"  // 或 "clear"
}
```
**响应示例** (自增操作):
```json
{
  "code": 1,
  "data": 43,
  "msg": "success"
}
```

### 2. 用户认证接口

#### 2.1 微信小程序登录

**状态**: ✅ 已实现  
**接口地址**: `POST /api/login`  
**接口描述**: 通过微信小程序code获取用户信息并返回JWT token  
**请求参数**:
```json
{
  "code": "微信小程序登录凭证"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "msg": "success"
}
```

#### 2.2 更新用户信息

**状态**: ✅ 已实现  
**接口地址**: `POST /api/update_user_info`  
**接口描述**: 接收前端传递的用户头像和昵称  
**请求参数**:
```json
{
  "token": "JWT令牌",
  "avatar_url": "用户头像URL",
  "nickname": "用户昵称"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "message": "用户信息更新成功"
  },
  "msg": "success"
}
```

## 待实现的API接口

### 3. 用户管理接口

#### 3.1 手机号登录

**状态**: ❌ 待实现  
**接口地址**: `POST /api/login_phone`  
**接口描述**: 通过手机号和验证码进行登录  
**请求参数**:
```json
{
  "phone": "手机号",
  "code": "验证码"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "token": "JWT令牌"
  },
  "msg": "success"
}
```

#### 3.2 发送短信验证码

**状态**: ❌ 待实现  
**接口地址**: `POST /api/send_sms`  
**接口描述**: 发送手机验证码  
**请求参数**:
```json
{
  "phone": "手机号"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {},
  "msg": "验证码发送成功"
}
```

#### 3.3 角色选择

**状态**: ❌ 待实现  
**接口地址**: `POST /api/select_role`  
**接口描述**: 用户选择角色（独居者/监护人/社区工作人员）  
**请求参数**:
```json
{
  "token": "JWT令牌",
  "role": "solo|supervisor|community"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "role": "solo"
  },
  "msg": "角色选择成功"
}
```

#### 3.4 社区身份验证

**状态**: ❌ 待实现  
**接口地址**: `POST /api/community_auth`  
**接口描述**: 社区工作人员身份验证  
**请求参数**:
```json
{
  "token": "JWT令牌",
  "name": "姓名",
  "work_id": "工号",
  "proof_image": "工作证明图片URL"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "is_verified": true
  },
  "msg": "身份验证成功"
}
```

### 4. 打卡相关接口

#### 4.1 获取今日打卡事项

**状态**: ❌ 待实现  
**接口地址**: `GET /api/checkin/today`  
**接口描述**: 获取用户今日需要打卡的事项列表  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "checkin_items": [
      {
        "rule_id": 1,
        "rule_name": "起床",
        "icon_url": "icon_url",
        "planned_time": "08:00",
        "grace_period": 30,
        "is_checked": false,
        "checkin_time": null
      }
    ]
  },
  "msg": "success"
}
```

#### 4.2 执行打卡

**状态**: ❌ 待实现  
**接口地址**: `POST /api/checkin`  
**接口描述**: 用户执行打卡操作  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "rule_id": 1
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "record_id": 123,
    "checkin_time": "2023-12-01 08:15:00"
  },
  "msg": "打卡成功"
}
```

#### 4.3 撤销打卡

**状态**: ❌ 待实现  
**接口地址**: `POST /api/checkin/cancel`  
**接口描述**: 撤销30分钟内的打卡记录  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "record_id": 123
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {},
  "msg": "撤销成功"
}
```

#### 4.4 获取打卡历史

**状态**: ❌ 待实现  
**接口地址**: `GET /api/checkin/history`  
**接口描述**: 获取用户打卡历史记录  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
- `user_id`: 用户ID（监护人查看时使用）
- `date_range`: 时间范围（today|yesterday|7days|30days|custom）
- `start_date`: 开始日期（custom时使用）
- `end_date`: 结束日期（custom时使用）

**响应示例**:
```json
{
  "code": 1,
  "data": {
    "records": [
      {
        "date": "2023-12-01",
        "items": [
          {
            "rule_name": "起床",
            "planned_time": "08:00",
            "checkin_time": "08:15",
            "status": "checked"
          }
        ]
      }
    ]
  },
  "msg": "success"
}
```

### 5. 打卡规则接口

#### 5.1 获取打卡规则

**状态**: ❌ 待实现  
**接口地址**: `GET /api/rules`  
**接口描述**: 获取用户的打卡规则列表  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "rules": [
      {
        "rule_id": 1,
        "rule_name": "起床",
        "icon_url": "icon_url",
        "frequency_type": "daily",
        "time_slot_type": "exact",
        "time_slot_details": "08:00-08:30",
        "is_active": true
      }
    ]
  },
  "msg": "success"
}
```

#### 5.2 创建打卡规则

**状态**: ❌ 待实现  
**接口地址**: `POST /api/rules`  
**接口描述**: 创建新的打卡规则  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "rule_name": "起床",
  "icon_url": "icon_url",
  "frequency_type": "daily",
  "time_slot_type": "exact",
  "time_slot_details": "08:00-08:30"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "rule_id": 1
  },
  "msg": "创建成功"
}
```

#### 5.3 更新打卡规则

**状态**: ❌ 待实现  
**接口地址**: `PUT /api/rules/{rule_id}`  
**接口描述**: 更新打卡规则  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "rule_name": "起床",
  "icon_url": "icon_url",
  "frequency_type": "daily",
  "time_slot_type": "exact",
  "time_slot_details": "08:00-08:30"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {},
  "msg": "更新成功"
}
```

#### 5.4 删除打卡规则

**状态**: ❌ 待实现  
**接口地址**: `DELETE /api/rules/{rule_id}`  
**接口描述**: 删除打卡规则  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {},
  "msg": "删除成功"
}
```

### 6. 监护关系接口

#### 6.1 邀请监护人

**状态**: ❌ 待实现  
**接口地址**: `POST /api/supervision/invite`  
**接口描述**: 独居者邀请监护人  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "invite_type": "phone|wechat",
  "phone": "手机号",
  "wechat_id": "微信号"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "invitation_id": 123
  },
  "msg": "邀请发送成功"
}
```

#### 6.2 申请成为监护人

**状态**: ❌ 待实现  
**接口地址**: `POST /api/supervision/apply`  
**接口描述**: 主动申请成为监护人  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "solo_user_phone": "独居者手机号"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "application_id": 456
  },
  "msg": "申请提交成功"
}
```

#### 6.3 处理监护申请

**状态**: ❌ 待实现  
**接口地址**: `POST /api/supervision/handle`  
**接口描述**: 处理监护申请（同意/拒绝）  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "application_id": 456,
  "action": "approve|reject"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {},
  "msg": "处理成功"
}
```

#### 6.4 获取监护关系列表

**状态**: ❌ 待实现  
**接口地址**: `GET /api/supervision/relations`  
**接口描述**: 获取用户的监护关系列表  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "supervisors": [
      {
        "user_id": 123,
        "nickname": "监护人昵称",
        "avatar_url": "头像URL",
        "status": "active"
      }
    ],
    "supervised_users": [
      {
        "user_id": 456,
        "nickname": "被监护人昵称",
        "avatar_url": "头像URL",
        "status": "active"
      }
    ]
  },
  "msg": "success"
}
```

### 7. 社区管理接口

#### 7.1 获取社区数据看板

**状态**: ❌ 待实现  
**接口地址**: `GET /api/community/dashboard`  
**接口描述**: 获取社区数据看板信息  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "total_solo_users": 150,
    "today_checkin_rate": 0.85,
    "unchecked_count": 23,
    "overdue_items": [
      {
        "rule_name": "起床",
        "overdue_count": 15
      }
    ]
  },
  "msg": "success"
}
```

#### 7.2 获取未打卡独居者详情

**状态**: ❌ 待实现  
**接口地址**: `GET /api/community/unchecked`  
**接口描述**: 获取未打卡独居者详细信息  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "unchecked_users": [
      {
        "user_id": 123,
        "nickname": "用户昵称",
        "phone": "手机号",
        "unchecked_items": [
          {
            "rule_name": "起床",
            "planned_time": "08:00"
          }
        ]
      }
    ]
  },
  "msg": "success"
}
```

#### 7.3 批量发送提醒

**状态**: ❌ 待实现  
**接口地址**: `POST /api/community/remind`  
**接口描述**: 批量发送提醒给未打卡用户  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "user_ids": [123, 456]
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "sent_count": 2
  },
  "msg": "提醒发送成功"
}
```

#### 7.4 标记已联系

**状态**: ❌ 待实现  
**接口地址**: `POST /api/community/mark_contacted`  
**接口描述**: 标记已联系独居者  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "user_id": 123
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {},
  "msg": "标记成功"
}
```

### 8. 通知接口

#### 8.1 获取通知列表

**状态**: ❌ 待实现  
**接口地址**: `GET /api/notifications`  
**接口描述**: 获取用户通知列表  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "notifications": [
      {
        "notification_id": 1,
        "type": "checkin_reminder",
        "content": "您有未完成的打卡事项",
        "is_read": false,
        "created_at": "2023-12-01 18:00:00"
      }
    ]
  },
  "msg": "success"
}
```

#### 8.2 标记通知已读

**状态**: ❌ 待实现  
**接口地址**: `POST /api/notifications/read`  
**接口描述**: 标记通知为已读  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "notification_id": 1
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {},
  "msg": "标记成功"
}
```

#### 8.3 更新通知设置

**状态**: ❌ 待实现  
**接口地址**: `POST /api/notifications/settings`  
**接口描述**: 更新用户通知设置  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "checkin_notification": true,
  "supervision_notification": true
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {},
  "msg": "设置更新成功"
}
```

## 数据模型

### 已实现的数据模型

#### Counters (计数器表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| id | Integer | 计数器ID | 主键 |
| count | Integer | 计数值 | 默认值: 1 |
| created_at | TIMESTAMP | 创建时间 | 非空，默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 非空，默认当前时间 |

### 待实现的数据模型

#### User (用户表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| user_id | Integer | 用户ID | 主键 |
| wechat_openid | String | 微信OpenID | 唯一 |
| phone_number | String | 手机号 | 唯一 |
| nickname | String | 用户昵称 | |
| avatar_url | String | 头像URL | |
| role | String | 用户角色 | solo/supervisor/community |
| community_id | Integer | 所属社区ID | 外键 |
| status | String | 用户状态 | active/inactive |
| created_at | TIMESTAMP | 创建时间 | 非空 |
| updated_at | TIMESTAMP | 更新时间 | 非空 |

#### Community (社区表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| community_id | Integer | 社区ID | 主键 |
| community_name | String | 社区名称 | |
| address | String | 社区地址 | |
| contact_person | String | 联系人 | |
| contact_phone | String | 联系电话 | |
| created_at | TIMESTAMP | 创建时间 | 非空 |
| updated_at | TIMESTAMP | 更新时间 | 非空 |

#### SupervisionRelation (监护关系表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| relation_id | Integer | 关系ID | 主键 |
| solo_user_id | Integer | 独居者ID | 外键 |
| supervisor_user_id | Integer | 监护人ID | 外键 |
| status | String | 关系状态 | pending/approved/rejected |
| created_at | TIMESTAMP | 创建时间 | 非空 |
| updated_at | TIMESTAMP | 更新时间 | 非空 |

#### CheckinRule (打卡规则表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| rule_id | Integer | 规则ID | 主键 |
| solo_user_id | Integer | 独居者ID | 外键 |
| rule_name | String | 规则名称 | |
| icon_url | String | 图标URL | |
| frequency_type | String | 频率类型 | daily/weekly/custom |
| frequency_details | JSON | 频率详情 | |
| time_slot_type | String | 时间段类型 | period/exact |
| time_slot_details | JSON | 时间段详情 | |
| grace_period_minutes | Integer | 宽限期(分钟) | 默认30 |
| is_active | Boolean | 是否启用 | 默认true |
| created_at | TIMESTAMP | 创建时间 | 非空 |
| updated_at | TIMESTAMP | 更新时间 | 非空 |

#### CheckinRecord (打卡记录表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| record_id | Integer | 记录ID | 主键 |
| solo_user_id | Integer | 独居者ID | 外键 |
| rule_id | Integer | 规则ID | 外键 |
| checkin_time | TIMESTAMP | 打卡时间 | |
| status | String | 状态 | checked/unchecked/cancelled |
| created_at | TIMESTAMP | 创建时间 | 非空 |
| updated_at | TIMESTAMP | 更新时间 | 非空 |

#### Notification (通知表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| notification_id | Integer | 通知ID | 主键 |
| user_id | Integer | 接收用户ID | 外键 |
| type | String | 通知类型 | |
| content | String | 通知内容 | |
| related_id | Integer | 关联记录ID | |
| is_read | Boolean | 是否已读 | 默认false |
| created_at | TIMESTAMP | 创建时间 | 非空 |

## 环境变量配置

后端服务依赖以下环境变量：

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| MYSQL_USERNAME | MySQL用户名 | root |
| MYSQL_PASSWORD | MySQL密码 | root |
| MYSQL_ADDRESS | MySQL地址 | 127.0.0.1:3306 |
| WX_APPID | 微信小程序AppID | (空字符串) |
| WX_SECRET | 微信小程序Secret | (空字符串) |
| TOKEN_SECRET | JWT签名密钥 | your-secret-key |
| SMS_API_KEY | 短信服务API密钥 | (待配置) |
| SMS_API_SECRET | 短信服务API密钥 | (待配置) |

## 错误码说明

| 错误码 | 描述 |
|--------|------|
| 1 | 成功 |
| 0 | 失败 |
| 1001 | 参数错误 |
| 1002 | 用户不存在 |
| 1003 | 密码错误 |
| 1004 | Token无效 |
| 1005 | Token过期 |
| 1006 | 权限不足 |
| 2001 | 打卡规则不存在 |
| 2002 | 打卡时间已过 |
| 2003 | 重复打卡 |
| 3001 | 监护关系不存在 |
| 3002 | 监护关系已存在 |
| 4001 | 社区身份未验证 |
| 4002 | 社区权限不足 |

## 安全说明

1. **身份验证**: 使用JWT进行身份验证，Token有效期为7天
2. **数据传输**: 所有敏感数据传输应使用HTTPS
3. **权限控制**: API接口应进行适当的权限验证，不同角色有不同权限
4. **数据验证**: 所有输入参数都应进行验证和过滤
5. **数据加密**: 用户敏感信息（手机号、微信OpenID）需加密存储
6. **API限流**: 实施API调用频率限制，防止恶意攻击

## 部署说明

### 本地开发环境

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量:
   ```bash
   export MYSQL_USERNAME=your_mysql_username
   export MYSQL_PASSWORD=your_mysql_password
   export MYSQL_ADDRESS=127.0.0.1:3306
   export WX_APPID=your_wechat_appid
   export WX_SECRET=your_wechat_secret
   export TOKEN_SECRET=your_jwt_secret
   ```

3. 创建数据库:
   ```sql
   CREATE DATABASE flask_demo;
   ```

4. 运行应用:
   ```bash
   python run.py 0.0.0.0 8080
   ```

### Docker部署

1. 构建镜像:
   ```bash
   docker build -t py-safeclockin .
   ```

2. 运行容器:
   ```bash
   docker run -p 8080:8080 \
     -e MYSQL_USERNAME=your_mysql_username \
     -e MYSQL_PASSWORD=your_mysql_password \
     -e MYSQL_ADDRESS=127.0.0.1:3306 \
     -e WX_APPID=your_wechat_appid \
     -e WX_SECRET=your_wechat_secret \
     -e TOKEN_SECRET=your_jwt_secret \
     py-safeclockin
   ```

## 开发优先级

### 第一阶段 (P0 - 核心功能)
- [x] 微信小程序登录
- [x] 用户信息更新
- [ ] 用户角色选择
- [ ] 打卡规则管理
- [ ] 每日打卡功能
- [ ] 监护关系管理
- [ ] 社区数据看板

### 第二阶段 (P1 - 重要功能)
- [ ] 手机号登录
- [ ] 社区身份验证
- [ ] 未打卡提醒
- [ ] 误操作撤销
- [ ] 离线打卡同步
- [ ] 通知设置

### 第三阶段 (P2 - 优化功能)
- [ ] 数据统计分析
- [ ] 高级筛选功能
- [ ] 批量操作优化
- [ ] 性能优化
- [ ] 安全加固

## 注意事项

1. **数据库连接**: 确保数据库服务正在运行，并且连接参数正确
2. **微信小程序配置**: 需要在微信小程序后台配置服务器域名
3. **安全配置**: 生产环境中应使用强密码和安全的JWT密钥
4. **容器端口**: 应用默认运行在8080端口，确保端口可用
5. **API版本控制**: 考虑实现API版本控制，便于后续升级
6. **日志记录**: 完善日志记录系统，便于问题排查
7. **监控告警**: 建立系统监控和告警机制

## 更新日志

### v1.0.0 (当前版本)
- ✅ 实现基础计数器功能
- ✅ 实现微信小程序登录功能
- ✅ 实现用户信息更新功能

### v1.1.0 (计划中)
- 🔄 用户角色选择功能
- 🔄 打卡规则管理
- 🔄 每日打卡功能
- 🔄 监护关系管理

### v1.2.0 (计划中)
- 🔄 社区数据看板
- 🔄 未打卡提醒系统
- 🔄 手机号登录
- 🔄 社区身份验证

## 接口测试

### 已实现接口测试

#### 微信登录测试
```bash
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"code": "test_code"}'
```

#### 获取计数测试
```bash
curl -X GET http://localhost:8080/api/count
```

#### 更新计数测试
```bash
curl -X POST http://localhost:8080/api/count \
  -H "Content-Type: application/json" \
  -d '{"action": "inc"}'
```

### 待实现接口设计说明

所有待实现接口都遵循RESTful设计原则，使用统一的响应格式，并包含完整的错误处理机制。接口设计考虑了不同用户角色的权限控制，确保数据安全和访问控制。

## 前端集成说明

### 前端API调用示例
```javascript
// 登录
const loginResponse = await authApi.login(code)

// 获取打卡规则
const rulesResponse = await request({
  url: '/api/rules',
  method: 'GET',
  header: {
    'Authorization': `Bearer ${token}`
  }
})

// 执行打卡
const checkinResponse = await request({
  url: '/api/checkin',
  method: 'POST',
  data: { rule_id: 1 },
  header: {
    'Authorization': `Bearer ${token}`
  }
})
```

### 认证机制
- 使用JWT Bearer Token进行身份认证
- Token在请求头中传递：`Authorization: Bearer {token}`
- Token过期时间为7天
- 前端需处理Token过期情况，引导用户重新登录