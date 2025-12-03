# 安全守护后端监护关系管理API文档

## 概述

安全守护后端监护关系管理API基于Flask框架开发，为独居者安全监护服务提供完整的监护关系管理功能。API采用RESTful设计风格，所有响应都遵循统一的JSON格式。

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

# 监护关系管理API接口列表

## 已实现的API接口

### 1. 监护关系接口

#### 1.1 邀请监护人

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

#### 1.2 获取邀请列表

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
        "rule_supervision_id": 123,
        "status": "pending",
        "status_name": "待确认",
        "invitation_message": "请监督我起床",
        "created_at": "2023-12-01T10:00:00.000000",
        "responded_at": null,
        "rule": {
          "rule_id": 1,
          "rule_name": "起床打卡",
          "icon_url": "🌅",
          "solo_user": {
            "user_id": 456,
            "nickname": "被监护人昵称",
            "avatar_url": "头像URL"
          }
        },
        "invited_by": {
          "user_id": 123,
          "nickname": "邀请人昵称",
          "avatar_url": "头像URL"
        }
      }
    ]
  },
  "msg": "success"
}
```

#### 1.3 响应邀请

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

#### 1.4 获取监护规则列表

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

#### 1.5 获取监护人规则

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

## 待实现的API接口

### 2. 监护关系接口

#### 2.1 申请成为监护人

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

#### 2.2 同意监护人申请

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

#### 2.3 拒绝监护人申请

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

#### 2.4 获取监护人列表

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

#### 2.5 移除监护人关系

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

#### 2.6 监护人首页数据

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

#### 2.7 获取被监护人详情

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

#### 2.8 获取被监护人打卡记录

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

#### 2.9 监护人通知设置

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

#### 2.10 获取监护关系列表

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