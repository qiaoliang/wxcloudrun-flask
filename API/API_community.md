# 社区管理域 API 文档

## 概述
社区管理域负责社区CRUD操作、工作人员管理、用户管理、申请处理等功能。

## API 列表

### 1. 社区列表获取
- **端点**: `GET /api/communities`
- **描述**: 获取所有社区列表（超级管理员专用）
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": [
      {
        "community_id": 1,
        "name": "社区名称",
        "description": "社区描述",
        "status": 1,
        "status_name": "状态名称",
        "location": "社区位置",
        "is_default": true,
        "is_blackhouse": false,
        "created_at": "创建时间",
        "updated_at": "更新时间",
        "creator": {
          "user_id": 123,
          "nickname": "创建者昵称"
        },
        "admin_count": 2,
        "user_count": 50
      }
    ]
  }
  ```

- **端点**: `GET /api/community/list`
- **描述**: 获取社区列表（新版API，支持分页和筛选）
- **请求头**: `Authorization: Bearer <token>`
- **查询参数**:
  - `page`: 页码（默认1）
  - `page_size`: 每页数量（默认20）
  - `status`: 状态筛选（all/active/inactive）
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "communities": [
        {
          "id": "1",
          "name": "社区名称",
          "location": "社区位置",
          "status": "active",
          "manager_id": "123",
          "manager_name": "主管姓名",
          "description": "社区描述",
          "created_at": "创建时间",
          "updated_at": "更新时间"
        }
      ],
      "total": 100,
      "has_more": true,
      "current_page": 1
    }
  }
  ```

### 2. 社区用户管理
- **端点**: `GET /api/communities/{community_id}/users`
- **描述**: 获取社区用户列表（非管理员）
- **请求头**: `Authorization: Bearer <token>`
- **查询参数**:
  - `page`: 页码（默认1）
  - `per_page`: 每页数量（默认20）
  - `keyword`: 搜索关键词
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
          "avatar_url": "头像URL",
          "phone_number": "手机号",
          "role": 1,
          "role_name": "角色名称",
          "verification_status": 1,
          "created_at": "创建时间"
        }
      ],
      "total": 50,
      "pages": 3,
      "current_page": 1,
      "per_page": 20
    }
  }
  ```

- **端点**: `DELETE /api/communities/{community_id}/users/{target_user_id}`
- **描述**: 从社区中移除用户（超级管理员专用）
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "移除成功"
    }
  }
  ```

### 3. 社区申请管理
- **端点**: `GET /api/community/applications`
- **描述**: 获取社区申请列表（管理员专用）
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": [
      {
        "application_id": 1,
        "user": {
          "user_id": 123,
          "nickname": "申请人昵称",
          "avatar_url": "头像URL",
          "phone_number": "手机号",
          "role": 1,
          "role_name": "角色名称"
        },
        "community": {
          "community_id": 1,
          "name": "社区名称",
          "description": "社区描述"
        },
        "reason": "申请理由",
        "status": 1,
        "status_name": "状态名称",
        "created_at": "申请时间"
      }
    ]
  }
  ```

- **端点**: `POST /api/community/applications`
- **描述**: 提交社区申请
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "community_id": 1,
    "reason": "申请理由"
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "申请已提交"
    }
  }
  ```

- **端点**: `PUT /api/community/applications/{application_id}/approve`
- **描述**: 批准社区申请
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "批准成功"
    }
  }
  ```

- **端点**: `PUT /api/community/applications/{application_id}/reject`
- **描述**: 拒绝社区申请
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "rejection_reason": "拒绝理由"
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "拒绝成功"
    }
  }
  ```

### 4. 用户社区信息
- **端点**: `GET /api/user/community`
- **描述**: 获取当前用户的社区信息
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "community": {
        "community_id": 1,
        "name": "社区名称",
        "description": "社区描述",
        "is_default": true
      },
      "is_admin": true,
      "is_primary_admin": false
    }
  }
  ```

### 5. 用户管理的社区
- **端点**: `GET /api/user/managed-communities`
- **描述**: 获取当前用户管理的社区列表
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "communities": [
        {
          "community_id": 1,
          "name": "社区名称",
          "description": "社区描述",
          "location": "社区位置",
          "is_default": true,
          "staff_count": 2,
          "user_count": 50,
          "user_role": "super_admin",
          "created_at": "创建时间"
        }
      ],
      "total": 1,
      "user_role": "super_admin"
    }
  }
  ```

### 6. 可申请的社区
- **端点**: `GET /api/communities/available`
- **描述**: 获取可申请的社区列表
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": [
      {
        "community_id": 1,
        "name": "社区名称",
        "description": "社区描述",
        "location": "社区位置",
        "user_count": 50
      }
    ]
  }
  ```

### 7. 工作人员管理
- **端点**: `GET /api/community/staff/list`
- **描述**: 获取社区工作人员列表
- **请求头**: `Authorization: Bearer <token>`
- **查询参数**:
  - `community_id`: 社区ID（必需）
  - `role`: 角色筛选（all/manager/staff）
  - `sort_by`: 排序方式（name/role/time）
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "staff_members": [
        {
          "user_id": "123",
          "nickname": "工作人员昵称",
          "avatar_url": "头像URL",
          "phone_number": "手机号",
          "role": "manager",
          "communities": [
            {
              "id": "1",
              "name": "社区名称",
              "location": "社区位置"
            }
          ],
          "added_time": "添加时间"
        }
      ]
    }
  }
  ```

- **端点**: `POST /api/community/add-staff`
- **描述**: 添加社区工作人员
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "community_id": 1,
    "user_ids": [123, 456],
    "role": "staff"
  }
  ```
- **响应**: 成功消息

## 权限说明
- **超级管理员 (role=4)**: 可访问所有社区
- **社区主管 (role=3)**: 可访问主管的社区
- **社区专员 (role=2)**: 可访问专员的社区
- **普通用户 (role=1)**: 仅可访问所属社区

## 相关文件
- `backend/src/wxcloudrun/views/community.py`
- `backend/src/wxcloudrun/community_service.py`
- `backend/src/wxcloudrun/community_staff_service.py`