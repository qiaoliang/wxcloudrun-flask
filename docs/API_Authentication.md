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

**状态**: ✅ 已实现（待完善）  
**接口地址**: `POST /api/user/profile`  
**接口描述**: 更新用户信息（头像、昵称等）  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
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