# 分享功能域 API 文档

## 概述
分享功能域负责分享链接创建、解析和分享页面渲染功能。

## API 列表

### 1. 创建打卡分享链接
- **端点**: `POST /api/share/checkin/create`
- **描述**: 创建可分享的打卡邀请链接（opaque token，避免暴露敏感参数）
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "rule_id": 1,
    "expire_hours": 168
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "token": "分享token",
      "url": "http://localhost:9999/share/check-in?token=xxx",
      "mini_path": "/pages/supervisor-detail/supervisor-detail?token=xxx",
      "expire_at": "2025-12-26 10:00:00"
    }
  }
  ```

### 2. 解析分享链接
- **端点**: `GET /api/share/checkin/resolve`
- **描述**: 解析分享链接并建立监督关系（已注册用户点击链接后）
- **请求头**: `Authorization: Bearer <token>`
- **查询参数**:
  - `token`: 分享token
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "rule": {
        "rule_id": 1,
        "rule_name": "规则名称",
        "icon_url": "图标URL",
        "frequency_type": 0,
        "time_slot_type": 4,
        "custom_time": "08:00",
        "week_days": 127,
        "custom_start_date": "2025-01-01",
        "custom_end_date": "2025-12-31",
        "status": 1
      },
      "solo_user_id": 123
    }
  }
  ```

### 3. 分享链接Web入口
- **端点**: `GET /share/check-in`
- **描述**: 分享链接的Web入口，记录访问日志，根据User-Agent返回不同内容
- **查询参数**:
  - `token`: 分享token
- **响应**:
  - **微信环境**: 返回小程序路径提示页面
  - **非微信环境**: 返回前端页面链接
  - **携带Authorization头**: 自动解析并返回JSON

## 功能说明

### 1. 链接创建
- 使用opaque token避免暴露敏感参数
- 默认有效期7天（168小时）
- 支持自定义有效期

### 2. 链接解析
- 验证token有效性
- 记录访问日志（IP、User-Agent、访问时间）
- 自动建立监督关系（状态设为已同意）
- 返回完整的规则信息

### 3. Web入口页面
根据User-Agent返回不同内容：

**微信环境** (`MicroMessenger` in User-Agent):
```html
<html>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>打开打卡规则</title>
</head>
<body>
  <p>请在微信小程序中打开以下路径：</p>
  <pre>/pages/supervisor-detail/supervisor-detail?token=xxx</pre>
</body>
</html>
```

**非微信环境**:
```html
<html>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>打开打卡规则</title>
</head>
<body>
  <p>请在前端页面打开规则详情：</p>
  <a href='http://localhost:9999/#/supervisor-detail?token=xxx'>http://localhost:9999/#/supervisor-detail?token=xxx</a>
</body>
</html>
```

**携带Authorization头**:
自动调用解析逻辑，建立监督关系并返回JSON响应。

### 4. 访问日志
每次访问分享链接都会记录：
- token
- IP地址
- User-Agent
- 访问时间
- 监督者用户ID（如果已登录）

## 安全考虑
1. **Token安全性**: 使用opaque token，不暴露规则ID和用户ID
2. **有效期控制**: 链接有过期时间，防止长期有效
3. **访问控制**: 只有规则所有者可以创建分享链接
4. **重复关系处理**: 如果监督关系已存在，更新状态为已同意

## 相关文件
- `backend/src/app/modules/share/routes.py`
- `backend/src/wxcloudrun/user_service.py`
- `backend/src/wxcloudrun/dao.py`