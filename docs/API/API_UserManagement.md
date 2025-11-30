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

#### 1.3 获取用户信息

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
    "status_name": "normal"
  },
  "msg": "success"
}
```

#### 1.4 更新用户信息

**状态**: ✅ 已实现  
**接口地址**: `POST /api/user/profile`  
**接口描述**: 更新用户信息（昵称、头像、角色等）  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "nickname": "用户昵称",
  "avatar_url": "用户头像URL",
  "role": "solo|supervisor|community",
  "phone_number": "手机号码"
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

#### 1.5 社区工作人员身份验证

**状态**: ✅ 已实现  
**接口地址**: `POST /api/community/verify`  
**接口描述**: 社区工作人员身份验证  
**请求头**: `Authorization: Bearer {token}`  
**请求参数**:
```json
{
  "name": "姓名",
  "work_id": "工号",
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

#### 1.6 手机号登录

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

#### 1.7 发送短信验证码

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