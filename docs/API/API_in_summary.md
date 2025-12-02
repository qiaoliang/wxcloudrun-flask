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

# API接口分类

## [API_Authentication.md](./API_Authentication.md)
- 计数器接口
- 微信小程序登录
- 更新用户信息

## [API_UserManagement.md](./API_UserManagement.md)
- 手机号登录
- 发送短信验证码
- 设置用户角色
- 获取用户信息
- 社区工作人员身份验证

## [API_CheckinManagement.md](./API_CheckinManagement.md)
- 获取今日打卡事项
- 执行打卡
- 撤销打卡
- 获取打卡历史
- 离线打卡数据同步
- 打卡规则管理

## [API_SupervisorManagement.md](./API_SupervisorManagement.md)
- 邀请监护人
- 申请成为监护人
- 同意/拒绝监护人申请
- 获取监护人列表
- 监护人首页数据
- 获取被监护人详情
- 获取被监护人打卡记录
- 监护人通知设置

## [API_CommunityManagement.md](./API_CommunityManagement.md)
- 获取社区数据看板
- 获取未打卡独居者列表
- 批量发送提醒
- 标记已联系状态

## [API_NotificationSystem.md](./API_NotificationSystem.md)
- 获取通知列表
- 标记通知已读
- 发送系统通知
- 通知设置管理

## 已实现的API接口

### 1. 认证接口

#### 1.1 计数器接口

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

#### 1.2 微信小程序登录

**状态**: ✅ 已实现  
**接口地址**: `POST /api/login`  
**接口描述**: 通过微信小程序code获取用户信息并返回JWT token  
**首次登录请求参数**:
```json
{
  "code": "微信小程序登录凭证",
  "avatar_url": "用户头像URL",
  "nickname": "用户昵称"
}
```
**非首次登录请求参数**:
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
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "refresh_token_string",
    "user_id": 123,
    "is_new_user": true,
    "role": "solo",
    "is_verified": false,
    "expires_in": 7200
  },
  "msg": "success"
}
```

#### 1.3 获取或更新用户信息

**状态**: ✅ 已实现  
**接口地址**: `GET /api/user/profile`  
**接口描述**: 获取用户信息  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "user_id": 123,
    "wechat_openid": "oabcdef123456789",
    "phone_number": "13800138000",
    "nickname": "用户昵称",
    "avatar_url": "头像URL",
    "role": 1,
    "role_name": "solo",
    "community_id": 1,
    "status": 1,
    "status_name": "normal",
    "is_verified": false
  },
  "msg": "success"
}
```

**接口地址**: `POST /api/user/profile`  
**接口描述**: 更新用户信息（昵称、头像、角色等）  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "nickname": "用户昵称",
  "avatar_url": "用户头像URL",
  "role": "solo|supervisor|community",
  "phone_number": "手机号码",
  "community_id": 1,
  "status": "active|disabled"
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

#### 1.4 刷新Token

**状态**: ✅ 已实现  
**接口地址**: `POST /api/refresh_token`  
**接口描述**: 使用refresh token获取新的access token  
**请求参数**:
```json
{
  "refresh_token": "refresh token"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "token": "new_access_token",
    "refresh_token": "new_refresh_token",
    "expires_in": 7200
  },
  "msg": "success"
}
```

#### 1.5 用户登出

**状态**: ✅ 已实现  
**接口地址**: `POST /api/logout`  
**接口描述**: 用户登出，清除refresh token  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "message": "登出成功"
  },
  "msg": "success"
}
```

### 2. 用户管理接口

#### 2.1 社区工作人员身份验证

**状态**: ✅ 已实现  
**接口地址**: `POST /api/community/verify`  
**接口描述**: 社区工作人员身份验证  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "name": "姓名",
  "workId": "工号",
  "workProof": "工作证明图片URL"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "message": "身份验证申请已提交，请耐心等待审核",
    "verification_status": "pending"
  },
  "msg": "success"
}
```

### 3. 打卡相关接口

#### 3.1 获取今日打卡事项

**状态**: ✅ 已实现  
**接口地址**: `GET /api/checkin/today`  
**接口描述**: 获取用户今日需要打卡的事项列表  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "date": "2023-12-01",
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

#### 3.2 执行打卡

**状态**: ✅ 已实现  
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

#### 3.3 撤销打卡

**状态**: ✅ 已实现  
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

#### 3.4 获取打卡历史

**状态**: ✅ 已实现  
**接口地址**: `GET /api/checkin/history`  
**接口描述**: 获取用户打卡历史记录  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
- `start_date`: 开始日期（格式：YYYY-MM-DD，默认为7天前）
- `end_date`: 结束日期（格式：YYYY-MM-DD，默认为今天）

**响应示例**:
```json
{
  "code": 1,
  "data": {
    "start_date": "2023-11-24",
    "end_date": "2023-12-01",
    "history": [
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

### 4. 打卡规则接口

#### 4.1 获取打卡规则

**状态**: ✅ 已实现  
**接口地址**: `GET /api/checkin/rules`  
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
        "rule_name": "起床打卡",
        "icon_url": "🌅",
        "frequency_type": 0,
        "time_slot_type": 4,
        "custom_time": "08:00:00",
        "week_days": 127,
        "status": 1,
        "created_at": "2023-12-01 10:30:00",
        "updated_at": "2023-12-01 10:30:00"
      }
    ]
  },
  "msg": "success"
}
```

#### 4.2 创建打卡规则

**状态**: ✅ 已实现  
**接口地址**: `POST /api/checkin/rules`  
**接口描述**: 创建新的打卡规则  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "rule_name": "起床打卡",
  "icon_url": "🌅",
  "frequency_type": 0,
  "time_slot_type": 4,
  "custom_time": "08:00:00",
  "week_days": 127,
  "status": 1
}
```
**参数说明**:
- `rule_name` (string, required): 打卡规则名称，如：起床打卡、早餐打卡等
- `icon_url` (string, optional): 打卡事项图标，如：🌅、💊 等
- `frequency_type` (integer, optional): 打卡频率类型：0-每天/1-每周/2-工作日/3-自定义，默认为0
- `time_slot_type` (integer, optional): 时间段类型：1-上午/2-下午/3-晚上/4-自定义时间，默认为4
- `custom_time` (string, optional): 自定义打卡时间（HH:MM:SS格式），当time_slot_type为4时使用
- `week_days` (integer, optional): 一周中的天（位掩码表示），默认127表示周一到周日
- `status` (integer, optional): 规则状态：1-启用/0-禁用，默认为1

**响应示例**:
```json
{
  "code": 1,
  "data": {
    "rule_id": 1,
    "message": "创建打卡规则成功"
  },
  "msg": "success"
}
```

#### 4.3 更新打卡规则

**状态**: ✅ 已实现  
**接口地址**: `PUT /api/checkin/rules`  
**接口描述**: 更新打卡规则  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "rule_id": 1,
  "rule_name": "起床打卡",
  "icon_url": "🌅",
  "frequency_type": 0,
  "time_slot_type": 4,
  "custom_time": "08:00:00",
  "week_days": 127,
  "status": 1
}
```
**参数说明**:
- `rule_id` (integer, required): 规则ID
- 其他参数与创建接口相同，只传递需要更新的字段

**响应示例**:
```json
{
  "code": 1,
  "data": {
    "rule_id": 1,
    "message": "更新打卡规则成功"
  },
  "msg": "success"
}
```

#### 4.4 删除打卡规则

**状态**: ✅ 已实现  
**接口地址**: `DELETE /api/checkin/rules`  
**接口描述**: 删除打卡规则  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "rule_id": 1
}
```
**参数说明**:
- `rule_id` (integer, required): 规则ID

**响应示例**:
```json
{
  "code": 1,
  "data": {
    "rule_id": 1,
    "message": "删除打卡规则成功"
  },
  "msg": "success"
}
```

## 待实现的API接口

### 5. 用户管理接口

#### 5.1 手机号登录

**状态**: ✅ 已实现  
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

#### 5.2 发送短信验证码

**状态**: ✅ 已实现  
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

#### 5.3 用户搜索

**状态**: ✅ 已实现  
**接口地址**: `GET /api/users/search`  
**接口描述**: 根据昵称搜索用户  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
- `nickname`: 搜索关键词
- `limit`: 返回结果数量限制（默认10，最大50）

**响应示例**:
```json
{
  "code": 1,
  "data": {
    "users": [
      {
        "user_id": 123,
        "nickname": "用户昵称",
        "avatar_url": "头像URL",
        "is_supervisor": true
      }
    ]
  },
  "msg": "success"
}
```

#### 5.4 手机号注册

**状态**: ✅ 已实现  
**接口地址**: `POST /api/register_phone`  
**接口描述**: 手机号注册接口  
**请求参数**:
```json
{
  "phone": "手机号码",
  "code": "短信验证码",
  "nickname": "用户昵称（可选）",
  "avatar_url": "用户头像URL（可选）"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "user_id": 123,
    "token": "JWT令牌"
  },
  "msg": "success"
}
```

#### 5.5 设置密码

**状态**: ✅ 已实现  
**接口地址**: `POST /api/set_password`  
**接口描述**: 设置密码接口  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "password": "新密码"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "message": "密码设置成功"
  },
  "msg": "success"
}
```

### 6. 监护关系接口

#### 6.1 邀请监护人

**状态**: ✅ 已实现  
**接口地址**: `POST /api/rules/supervision/invite`  
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

#### 6.2 获取邀请列表

**状态**: ✅ 已实现  
**接口地址**: `GET /api/supervision/invitations`  
**接口描述**: 获取监护邀请列表  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
- `type`: 邀请类型（sent-发送的，received-收到的）

**响应示例**:
```json
{
  "code": 1,
  "data": {
    "invitations": [
      {
        "invitation_id": 123,
        "inviter_nickname": "邀请人昵称",
        "inviter_avatar": "头像URL",
        "rule_name": "规则名称",
        "status": "pending",
        "created_at": "2023-12-01 10:00:00"
      }
    ]
  },
  "msg": "success"
}
```

#### 6.3 响应邀请

**状态**: ✅ 已实现  
**接口地址**: `POST /api/supervision/respond`  
**接口描述**: 同意或拒绝监护邀请  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "invitation_id": 123,
  "action": "accept|reject"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "message": "邀请已处理"
  },
  "msg": "success"
}
```

#### 6.4 获取监护规则列表

**状态**: ✅ 已实现  
**接口地址**: `GET /api/rules/supervision/list`  
**接口描述**: 获取监护规则列表  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "rules": [
      {
        "rule_id": 1,
        "rule_name": "起床打卡",
        "supervisor_count": 2,
        "supervisors": [
          {
            "user_id": 123,
            "nickname": "监护人昵称",
            "avatar_url": "头像URL"
          }
        ]
      }
    ]
  },
  "msg": "success"
}
```

#### 6.5 获取监护人规则

**状态**: ✅ 已实现  
**接口地址**: `GET /api/supervisor/rules`  
**接口描述**: 获取监护人的监护规则列表  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "supervision_rules": [
      {
        "rule_id": 1,
        "rule_name": "起床打卡",
        "solo_user": {
          "user_id": 456,
          "nickname": "被监护人昵称",
          "avatar_url": "头像URL"
        },
        "status": "active"
      }
    ]
  },
  "msg": "success"
}
```

#### 6.6 申请成为监护人

**状态**: ❌ 待实现  
**接口地址**: `POST /api/supervisor/apply`  
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

#### 6.4 同意监护人申请

**状态**: ❌ 待实现  
**接口地址**: `POST /api/supervisor/accept`  
**接口描述**: 同意监护人申请  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "application_id": 456
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {},
  "msg": "同意成功"
}
```

#### 6.5 拒绝监护人申请

**状态**: ❌ 待实现  
**接口地址**: `POST /api/supervisor/reject`  
**接口描述**: 拒绝监护人申请  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "application_id": 456
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {},
  "msg": "拒绝成功"
}
```

#### 6.6 获取监护人列表

**状态**: ❌ 待实现  
**接口地址**: `GET /api/supervisor/list`  
**接口描述**: 获取监护人列表  
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
    ]
  },
  "msg": "success"
}
```

#### 6.7 移除监护人关系

**状态**: ❌ 待实现  
**接口地址**: `DELETE /api/supervisor/remove`  
**接口描述**: 移除监护人关系  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "supervisor_user_id": 123
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {},
  "msg": "移除成功"
}
```

#### 6.8 监护人首页数据

**状态**: ❌ 待实现  
**接口地址**: `GET /api/supervisor/dashboard`  
**接口描述**: 监护人首页数据  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "supervised_users": [
      {
        "user_id": 123,
        "nickname": "被监护人昵称",
        "avatar_url": "头像URL",
        "today_checkin_status": "checked|unchecked",
        "last_checkin_time": "2023-12-01 08:15:00"
      }
    ]
  },
  "msg": "success"
}
```

#### 6.9 获取被监护人详情

**状态**: ❌ 待实现  
**接口地址**: `GET /api/supervisor/detail`  
**接口描述**: 获取被监护人详情  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
- `user_id`: 被监护人用户ID

**响应示例**:
```json
{
  "code": 1,
  "data": {
    "user_info": {
      "user_id": 123,
      "nickname": "被监护人昵称",
      "avatar_url": "头像URL"
    },
    "checkin_rules": [
      {
        "rule_id": 1,
        "rule_name": "起床",
        "icon_url": "图标URL"
      }
    ],
    "today_checkin_status": [
      {
        "rule_name": "起床",
        "status": "checked|unchecked",
        "checkin_time": "08:15"
      }
    ]
  },
  "msg": "success"
}
```

#### 6.10 获取被监护人打卡记录

**状态**: ❌ 待实现  
**接口地址**: `GET /api/supervisor/records`  
**接口描述**: 获取被监护人打卡记录  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
- `user_id`: 被监护人用户ID
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

#### 6.11 监护人通知设置

**状态**: ❌ 待实现  
**接口地址**: `POST /api/supervisor/settings`  
**接口描述**: 监护人通知设置  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "notification_settings": {
    "checkin_reminder": true,
    "emergency_contact": true
  }
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

#### 6.12 获取监护关系列表

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

#### 7.2 获取未打卡独居者列表

**状态**: ❌ 待实现  
**接口地址**: `GET /api/community/unchecked`  
**接口描述**: 获取未打卡独居者列表  
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
**接口地址**: `POST /api/community/notify`  
**接口描述**: 批量发送提醒  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "user_ids": [123, 456],
  "message": "提醒内容"
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

#### 7.4 标记已联系状态

**状态**: ❌ 待实现  
**接口地址**: `POST /api/community/mark_contacted`  
**接口描述**: 标记已联系状态  
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

#### 7.5 批量发送提醒（旧版）

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

#### 8.3 发送系统通知

**状态**: ❌ 待实现  
**接口地址**: `POST /api/notifications/send`  
**接口描述**: 发送系统通知  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "user_ids": [123, 456],
  "type": "missed_checkin|rule_update|supervisor_request|system",
  "title": "通知标题",
  "content": "通知内容"
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "sent_count": 2
  },
  "msg": "通知发送成功"
}
```

#### 8.4 通知设置管理

**状态**: ❌ 待实现  
**接口地址**: `POST /api/notifications/settings`  
**接口描述**: 通知设置管理  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "notification_settings": {
    "checkin_reminder": true,
    "supervision_notification": true,
    "community_alert": true
  }
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

### 9. 打卡相关接口

#### 9.1 离线打卡数据同步

**状态**: ❌ 待实现  
**接口地址**: `POST /api/checkin/sync`  
**接口描述**: 离线打卡数据同步  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "sync_data": [
    {
      "rule_id": 1,
      "planned_time": "2023-12-01 08:00:00",
      "checkin_time": "2023-12-01 08:15:00",
      "status": "checked"
    }
  ]
}
```
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "synced_count": 1,
    "failed_count": 0
  },
  "msg": "同步成功"
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

#### User (用户表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| user_id | Integer | 用户ID | 主键，自增 |
| wechat_openid | String(128) | 微信OpenID，唯一标识用户 | 唯一，非空 |
| phone_number | String(500) | 手机号码，可用于登录和联系（加密存储） | 唯一 |
| nickname | String(100) | 用户昵称 | |
| avatar_url | String(500) | 用户头像URL | |
| name | String(100) | 真实姓名 | |
| work_id | String(50) | 工号或身份证号 | |
| is_solo_user | Boolean | 是否为独居者（有打卡规则和记录） | 默认值：true |
| is_supervisor | Boolean | 是否为监护人（有关联的监护关系） | 默认值：false |
| is_community_worker | Boolean | 是否为社区工作人员（需要身份验证） | 默认值：false |
| role | Integer | 兼容性字段：1-独居者/2-监护人/3-社区工作人员 | 默认值：1 |
| status | Integer | 用户状态：1-正常/2-禁用 | 默认值：1 |
| verification_status | Integer | 验证状态：0-未申请/1-待审核/2-已通过/3-已拒绝 | 默认值：0 |
| verification_materials | Text | 验证材料URL | |
| community_id | Integer | 所属社区ID，仅社区工作人员需要 | |
| auth_type | Enum | 认证类型：wechat/phone/both | 默认值：wechat |
| linked_accounts | Text | 关联账户信息（JSON格式） | |
| refresh_token | String(255) | 刷新令牌 | |
| refresh_token_expire | DateTime | 刷新令牌过期时间 | |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 默认当前时间，自动更新 |

#### CheckinRule (打卡规则表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| rule_id | Integer | 规则ID | 主键，自增 |
| solo_user_id | Integer | 独居者用户ID | 非空，外键，关联users表 |
| rule_name | String(100) | 规则名称 | 非空 |
| icon_url | String(500) | 规则图标URL | |
| frequency_type | Integer | 频率类型：0-每天/1-每周/2-工作日/3-自定义 | 默认值：0 |
| time_slot_type | Integer | 时间段类型：1-上午/2-下午/3-晚上/4-自定义时间 | 默认值：4 |
| custom_time | Time | 自定义打卡时间 | |
| week_days | Integer | 一周中的天（位掩码表示）：默认127表示周一到周日 | 默认值：127 |
| status | Integer | 规则状态：1-启用/0-禁用 | 默认值：1 |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 默认当前时间，自动更新 |

#### CheckinRecord (打卡记录表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| record_id | Integer | 记录ID | 主键，自增 |
| rule_id | Integer | 打卡规则ID | 非空，外键，关联checkin_rules表 |
| solo_user_id | Integer | 独居者用户ID | 非空，外键，关联users表 |
| checkin_time | TIMESTAMP | 实际打卡时间 | |
| status | Integer | 状态：0-未打卡/1-已打卡/2-已撤销 | 默认值：0 |
| planned_time | TIMESTAMP | 计划打卡时间 | 非空 |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 默认当前时间，自动更新 |

#### RuleSupervision (规则监护关系表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| supervision_id | Integer | 监护关系ID | 主键，自增 |
| rule_id | Integer | 打卡规则ID | 非空，外键，关联checkin_rules表 |
| supervisor_user_id | Integer | 监护人用户ID | 非空，外键，关联users表 |
| solo_user_id | Integer | 独居者用户ID | 非空，外键，关联users表 |
| status | String(20) | 关系状态：pending/approved/rejected | 默认值：pending |
| invitation_token | String(255) | 邀请令牌 | |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 默认当前时间，自动更新 |

#### PhoneAuth (手机认证表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| auth_id | Integer | 认证ID | 主键，自增 |
| phone_number | String(20) | 手机号码 | 唯一，非空 |
| user_id | Integer | 用户ID | 外键，关联users表 |
| password_hash | String(255) | 密码哈希 | |
| is_active | Boolean | 是否激活 | 默认值：true |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 默认当前时间，自动更新 |

#### SMSVerificationCode (短信验证码表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| code_id | Integer | 验证码ID | 主键，自增 |
| phone_number | String(20) | 手机号码 | 非空 |
| code | String(10) | 验证码 | 非空 |
| type | String(20) | 验证码类型：login/register/reset_password | 非空 |
| is_used | Boolean | 是否已使用 | 默认值：false |
| expires_at | TIMESTAMP | 过期时间 | 非空 |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |

### 待实现的数据模型

#### Community (社区表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| community_id | Integer | 社区ID | 主键，自增 |
| community_name | String(200) | 社区名称 | 非空 |
| address | String(500) | 社区地址 | |
| contact_person | String(100) | 社区联系人 | |
| contact_phone | String(20) | 社区联系电话 | |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 默认当前时间，自动更新 |

#### SupervisionRelation (监督关系表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| relation_id | Integer | 关系ID | 主键，自增 |
| solo_user_id | Integer | 独居者用户ID | 非空，外键，关联users表 |
| supervisor_user_id | Integer | 监护人用户ID | 非空，外键，关联users表 |
| status | String(20) | 关系状态：待同意/已同意/已拒绝 | 默认值：pending，枚举值：pending/approved/rejected |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 默认当前时间，自动更新 |

#### Notification (通知表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| notification_id | Integer | 通知ID | 主键，自增 |
| user_id | Integer | 接收通知的用户ID | 非空，外键，关联users表 |
| type | String(50) | 通知类型 | 非空，枚举值：missed_checkin/rule_update/supervisor_request/system |
| title | String(200) | 通知标题 | |
| content | TEXT | 通知内容 | |
| related_id | Integer | 关联记录ID，如打卡记录ID、规则ID、监督关系ID | |
| related_type | String(50) | 关联记录类型 | |
| is_read | Boolean | 是否已读 | 默认值：false |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |

#### SystemConfigs (系统配置表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| config_id | Integer | 配置ID | 主键，自增 |
| config_key | String(100) | 配置键名 | 唯一，非空 |
| config_value | TEXT | 配置值 | |
| description | String(500) | 配置描述 | |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 默认当前时间，自动更新 |

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
  url: '/api/checkin/rules',
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
