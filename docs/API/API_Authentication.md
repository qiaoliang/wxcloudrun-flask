# 安全守护后端认证API文档

## 概述

安全守护后端认证API基于Flask框架开发，为独居者安全监护服务提供用户认证和授权支持。API采用RESTful设计风格，所有响应都遵循统一的JSON格式。

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

# 认证API接口列表

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

#### 2.2 获取或更新用户信息

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
    "role": "solo",
    "role_name": "solo",
    "community_id": 1,
    "status": "active",
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

#### 2.3 刷新Token

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

#### 2.4 用户登出

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