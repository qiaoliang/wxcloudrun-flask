# 认证域 API 文档

## 概述
认证域负责用户身份验证、登录、注册和token管理等功能。

## API 列表

### 1. 微信登录
- **端点**: `POST /api/auth/login_wechat`
- **描述**: 通过微信code获取用户信息并返回token
- **请求体**:
  ```json
  {
    "code": "微信登录code",
    "nickname": "用户昵称（可选）",
    "avatar_url": "用户头像URL（可选）"
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "token": "JWT token",
      "refresh_token": "刷新token",
      "user_id": 123,
      "wechat_openid": "微信openid",
      "phone_number": "手机号",
      "nickname": "用户昵称",
      "name": "真实姓名",
      "avatar_url": "头像URL",
      "role": "用户角色",
      "login_type": "new_user 或 existing_user"
    }
  }
  ```

### 2. 手机号注册
- **端点**: `POST /api/auth/register_phone`
- **描述**: 通过手机号和验证码注册新用户
- **请求体**:
  ```json
  {
    "phone": "手机号",
    "code": "验证码",
    "nickname": "昵称（可选）",
    "avatar_url": "头像URL（可选）",
    "password": "密码（可选）"
  }
  ```
- **响应**: 同微信登录响应格式

### 3. 验证码登录
- **端点**: `POST /api/auth/login_phone_code`
- **描述**: 通过手机号和验证码登录
- **请求体**:
  ```json
  {
    "phone": "手机号",
    "code": "验证码"
  }
  ```
- **响应**: 返回token和refresh_token

### 4. 密码登录
- **端点**: `POST /api/auth/login_phone_password`
- **描述**: 通过手机号和密码登录
- **请求体**:
  ```json
  {
    "phone": "手机号",
    "password": "密码"
  }
  ```
- **响应**: 返回token和refresh_token

### 5. 手机号登录（验证码+密码）
- **端点**: `POST /api/auth/login_phone`
- **描述**: 同时验证验证码和密码进行登录
- **请求体**:
  ```json
  {
    "phone": "手机号",
    "code": "验证码",
    "password": "密码"
  }
  ```
- **响应**: 同微信登录响应格式

### 6. 刷新Token
- **端点**: `POST /api/refresh_token`
- **描述**: 使用refresh token获取新的access token
- **请求体**:
  ```json
  {
    "refresh_token": "刷新token"
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "token": "新的JWT token",
      "refresh_token": "新的刷新token",
      "expires_in": 7200
    }
  }
  ```

### 7. 用户登出
- **端点**: `POST /api/logout`
- **描述**: 清除用户的refresh token
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "登出成功"
    }
  }
  ```

## 认证方式
- **Bearer Token**: 在请求头中添加 `Authorization: Bearer <token>`
- **Token有效期**: 2小时
- **Refresh Token有效期**: 7天

## 错误码
- `PHONE_EXISTS`: 手机号已注册
- `USER_NOT_FOUND`: 用户不存在

## 相关文件
- `backend/src/app/modules/auth/routes.py`
- `backend/src/wxcloudrun/utils/auth.py`
- `backend/src/wxcloudrun/user_service.py`