# 安全守护后端打卡管理API文档

## 概述

安全守护后端打卡管理API基于Flask框架开发，为独居者安全监护服务提供完整的打卡功能。API采用RESTful设计风格，所有响应都遵循统一的JSON格式。

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

# 打卡管理API接口列表

## 待实现的API接口

### 1. 打卡相关接口

#### 1.1 获取今日打卡事项

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

#### 1.2 执行打卡

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

#### 1.3 撤销打卡

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

#### 1.4 获取打卡历史

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

#### 1.5 离线打卡数据同步

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

### 2. 打卡规则接口

#### 2.1 获取打卡规则

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

#### 2.2 创建打卡规则

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

#### 2.3 更新打卡规则

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

#### 2.4 删除打卡规则

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

#### 2.5 获取默认打卡规则

**状态**: ❌ 待实现  
**接口地址**: `GET /api/rules/default`  
**接口描述**: 获取默认打卡规则  
**请求头**: `Authorization: Bearer {token}`  
**响应示例**:
```json
{
  "code": 1,
  "data": {
    "default_rules": [
      {
        "rule_name": "起床",
        "icon_url": "icons/get_up.png",
        "frequency_type": "daily",
        "time_slot_type": "period"
      }
    ]
  },
  "msg": "success"
}
```