# 安全守护后端社区管理API文档

## 概述

安全守护后端社区管理API基于Flask框架开发，为独居者安全监护服务提供社区数据看板和管理功能。API采用RESTful设计风格，所有响应都遵循统一的JSON格式。

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

# 社区管理API接口列表

## 待实现的API接口

### 1. 社区管理接口

#### 1.1 获取社区数据看板

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

#### 1.2 获取未打卡独居者列表

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

#### 1.3 批量发送提醒

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

#### 1.4 标记已联系状态

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

#### 1.5 批量发送提醒（旧版）

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

#### 1.6 标记已联系

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