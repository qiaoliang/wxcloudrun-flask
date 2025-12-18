# 用户管理域 API 文档

## 概述
用户管理域负责用户信息管理、用户搜索、账号绑定、身份验证等功能。

## API 列表

### 1. 用户信息管理
- **端点**: `GET /api/user/profile`
- **描述**: 获取当前用户信息
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "user_id": 123,
      "wechat_openid": "微信openid",
      "phone_number": "手机号",
      "nickname": "用户昵称",
      "avatar_url": "头像URL",
      "role": "用户角色",
      "community_id": 1,
      "status": "用户状态",
      "is_community_worker": false
    }
  }
  ```

- **端点**: `POST /api/user/profile`
- **描述**: 更新用户信息
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "nickname": "新昵称",
    "avatar_url": "新头像URL",
    "phone_number": "新手机号",
    "role": "新角色",
    "community_id": 1,
    "status": "新状态",
    "is_community_worker": true
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "用户信息更新成功"
    }
  }
  ```

### 2. 用户搜索
- **端点**: `GET /api/users/search`
- **描述**: 根据关键词搜索用户（支持昵称和手机号）
- **请求头**: `Authorization: Bearer <token>`
- **查询参数**:
  - `keyword`: 搜索关键词（昵称或手机号）
  - `scope`: 搜索范围（all/community，默认all）
  - `community_id`: 社区ID（scope=community时必需）
  - `limit`: 返回数量限制（默认10）
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "users": [
        {
          "user_id": 123,
          "nickname": "用户昵称",
          "phone_number": "手机号",
          "avatar_url": "头像URL",
          "is_supervisor": true
        }
      ]
    }
  }
  ```

### 3. 绑定手机号
- **端点**: `POST /api/user/bind_phone`
- **描述**: 绑定手机号到当前用户账号
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "phone": "手机号",
    "code": "验证码"
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "绑定手机号成功"
    }
  }
  ```

### 4. 绑定微信
- **端点**: `POST /api/user/bind_wechat`
- **描述**: 绑定微信到当前用户账号
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "code": "微信登录code",
    "phone": "手机号（可选）",
    "phone_code": "手机验证码（可选）"
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "绑定微信成功"
    }
  }
  ```

### 5. 社区工作人员身份验证
- **端点**: `POST /api/community/verify`
- **描述**: 社区工作人员身份验证申请
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "name": "真实姓名",
    "workId": "工号",
    "workProof": "工作证明照片URL或base64"
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "身份验证申请已提交，请耐心等待审核",
      "verification_status": "pending"
    }
  }
  ```

## 权限说明
- **用户搜索**:
  - `scope=all`: 仅超级管理员可访问
  - `scope=community`: 需要该社区的管理权限
- **账号绑定**: 仅登录用户可访问
- **身份验证**: 仅登录用户可访问

## 账号合并机制
当绑定手机号或微信时，如果目标账号已存在，系统会自动合并账号：
- 按注册时间保留较早的账号
- 迁移用户数据（打卡规则、打卡记录、监护关系）
- 禁用次要账号

## 相关文件
- `backend/src/wxcloudrun/views/user.py`
- `backend/src/wxcloudrun/user_service.py`
- `backend/src/wxcloudrun/decorators.py`