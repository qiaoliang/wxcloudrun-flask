# 安全守护后端通知系统API文档

## 概述

安全守护后端通知系统API基于Flask框架开发，为独居者安全监护服务提供完整的通知管理功能。API采用RESTful设计风格，所有响应都遵循统一的JSON格式。

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

# 通知系统API接口列表

## 待实现的API接口

### 1. 通知接口

#### 1.1 获取通知列表

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

#### 1.2 标记通知已读

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

#### 1.3 发送系统通知

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

#### 1.4 通知设置管理

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

## 数据模型

### 待实现的数据模型

#### User (用户表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| user_id | Integer | 用户ID | 主键，自增 |
| wechat_openid | String(128) | 微信OpenID，唯一标识用户 | 唯一，非空 |
| phone_number | String(20) | 手机号码，可用于登录和联系 | 唯一 |
| nickname | String(100) | 用户昵称 | |
| avatar_url | String(500) | 用户头像URL | |
| role | String(20) | 用户角色：独居者/监护人/社区工作人员 | 非空，枚举值：solo/supervisor/community |
| community_id | Integer | 所属社区ID，仅社区工作人员需要 | 外键，关联communities表 |
| status | String(20) | 用户状态：正常/禁用 | 默认值：active，枚举值：active/disabled |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 默认当前时间，自动更新 |

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

#### CheckinRule (打卡规则表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| rule_id | Integer | 规则ID | 主键，自增 |
| solo_user_id | Integer | 独居者用户ID | 非空，外键，关联users表 |
| rule_name | String(100) | 规则名称 | 非空 |
| icon_url | String(500) | 规则图标URL | |
| frequency_type | String(20) | 频率类型：每天/每周/自定义 | 默认值：daily，枚举值：daily/weekly/custom |
| frequency_details | JSON | 频率详情，如具体的星期几 | |
| time_slot_type | String(20) | 时间段类型：时段/精确时间 | 默认值：period，枚举值：period/exact |
| time_slot_details | JSON | 时间段详情，如上午/下午/晚上或具体时间段 | |
| grace_period_minutes | Integer | 宽限期（分钟），默认30分钟 | 默认值：30 |
| is_active | Boolean | 是否启用 | 默认值：true |
| created_at | TIMESTAMP | 创建时间 | 默认当前时间 |
| updated_at | TIMESTAMP | 更新时间 | 默认当前时间，自动更新 |

#### CheckinRecord (打卡记录表)

| 字段名 | 类型 | 描述 | 约束 |
|--------|------|------|------|
| record_id | Integer | 记录ID | 主键，自增 |
| solo_user_id | Integer | 独居者用户ID | 非空，外键，关联users表 |
| rule_id | Integer | 打卡规则ID | 非空，外键，关联checkin_rules表 |
| checkin_time | TIMESTAMP | 实际打卡时间 | |
| status | String(20) | 状态：已打卡/未打卡/已撤销 | 默认值：missed，枚举值：checked/missed/revoked |
| planned_time | TIMESTAMP | 计划打卡时间 | 非空 |
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