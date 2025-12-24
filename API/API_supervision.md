# 监督功能域 API 文档

## 概述
监督功能域负责监督关系管理、监督邀请、监督记录查看等功能。

## API 列表

### 1. 邀请监督者
- **端点**: `POST /api/rules/supervision/invite`
- **描述**: 邀请特定用户监督特定规则
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "invite_type": "wechat",
    "rule_ids": [1, 2],
    "target_openid": "被邀请用户的openid"
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "邀请发送成功"
    }
  }
  ```

### 2. 生成监督邀请链接
- **端点**: `POST /api/rules/supervision/invite_link`
- **描述**: 生成监督邀请链接（无需目标openid）
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "rule_ids": [1, 2],
    "expire_hours": 72
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "invite_token": "邀请token",
      "mini_path": "/pages/supervisor-invite/supervisor-invite?token=xxx",
      "expire_at": "2025-12-22 10:00:00"
    }
  }
  ```

### 3. 解析邀请链接
- **端点**: `GET /api/rules/supervision/invite/resolve`
- **描述**: 解析邀请链接，将当前登录用户绑定为supervisor
- **请求头**: `Authorization: Bearer <token>`
- **查询参数**:
  - `token`: 邀请token
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "relation_id": 1,
      "status": "待同意",
      "solo_user_id": 123,
      "rule_id": 1
    }
  }
  ```

### 4. 获取监督邀请列表
- **端点**: `GET /api/rules/supervision/invitations`
- **描述**: 获取监督邀请列表
- **请求头**: `Authorization: Bearer <token>`
- **查询参数**:
  - `type`: 邀请类型（received/sent，默认received）
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "type": "received",
      "invitations": [
        {
          "relation_id": 1,
          "solo_user": {
            "user_id": 123,
            "nickname": "独居者昵称",
            "avatar_url": "头像URL"
          },
          "rule": {
            "rule_id": 1,
            "rule_name": "规则名称"
          },
          "status": "待同意",
          "created_at": "2025-12-19 10:00:00"
        }
      ]
    }
  }
  ```

### 5. 接受监督邀请
- **端点**: `POST /api/rules/supervision/accept`
- **描述**: 接受监督邀请
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "relation_id": 1
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "接受邀请成功"
    }
  }
  ```

### 6. 拒绝监督邀请
- **端点**: `POST /api/rules/supervision/reject`
- **描述**: 拒绝监督邀请
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "relation_id": 1
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "拒绝邀请成功"
    }
  }
  ```

### 7. 获取我监督的用户列表
- **端点**: `GET /api/rules/supervision/my_supervised`
- **描述**: 获取我监督的用户列表
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "supervised_users": [
        {
          "user_id": 123,
          "nickname": "被监督用户昵称",
          "avatar_url": "头像URL",
          "rules": [
            {
              "rule_id": 1,
              "rule_name": "规则名称",
              "icon_url": "图标URL"
            }
          ],
          "today_checkin_status": [
            {
              "rule_id": 1,
              "rule_name": "规则名称",
              "status": "checked",
              "checkin_time": "08:05:00"
            }
          ]
        }
      ]
    }
  }
  ```

### 8. 获取我的监护人列表
- **端点**: `GET /api/rules/supervision/my_guardians`
- **描述**: 获取我的监护人列表
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "guardians": [
        {
          "user_id": 456,
          "nickname": "监护人昵称",
          "avatar_url": "头像URL"
        }
      ]
    }
  }
  ```

### 9. 获取被监督用户的打卡记录
- **端点**: `GET /api/rules/supervision/records`
- **描述**: 获取被监督用户的打卡记录
- **请求头**: `Authorization: Bearer <token>`
- **查询参数**:
  - `solo_user_id`: 被监督用户ID（必需）
  - `rule_id`: 规则ID（可选）
  - `start_date`: 开始日期（格式：YYYY-MM-DD，默认7天前）
  - `end_date`: 结束日期（格式：YYYY-MM-DD，默认今天）
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "start_date": "2025-12-12",
      "end_date": "2025-12-19",
      "history": [
        {
          "record_id": 123,
          "rule_id": 1,
          "rule_name": "规则名称",
          "icon_url": "图标URL",
          "planned_time": "2025-12-19 08:00:00",
          "checkin_time": "2025-12-19 08:05:00",
          "status": "已打卡",
          "created_at": "2025-12-19 08:05:00"
        }
      ]
    }
  }
  ```

## 监督关系状态
- `1`: 待同意
- `2`: 已同意
- `3`: 已拒绝

## 权限说明
- 只有被监督用户（solo_user）可以邀请监督者
- 只有监督者（supervisor）可以接受/拒绝邀请
- 监督者只能查看自己有权限监督的规则和用户的打卡记录

## 相关文件
- `backend/src/app/modules/supervision/routes.py`
- `backend/src/wxcloudrun/user_service.py`
- `backend/src/wxcloudrun/dao.py`