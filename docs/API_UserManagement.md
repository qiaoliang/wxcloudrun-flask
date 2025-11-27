# 安全守护后端用户管理API文档

## 概述

安全守护后端用户管理API基于Flask框架开发，为独居者安全监护服务提供完整的用户管理功能。API采用RESTful设计风格，所有响应都遵循统一的JSON格式。

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

# 用户管理API接口列表

## 待实现的API接口

### 1. 用户管理接口

#### 1.1 手机号登录

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

#### 1.2 发送短信验证码

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

#### 1.3 设置用户角色

**状态**: ❌ 待实现  
**接口地址**: `POST /api/user/role`  
**接口描述**: 设置用户角色（独居者/监护人/社区工作人员）  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
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
  "msg": "角色设置成功"
}
```

#### 1.4 获取用户信息

**状态**: ❌ 待实现  
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
    "community_id": 1,
    "status": "active"
  },
  "msg": "success"
}
```

#### 1.5 社区工作人员身份验证

**状态**: ❌ 待实现  
**接口地址**: `POST /api/community/verify`  
**接口描述**: 社区工作人员身份验证  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
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