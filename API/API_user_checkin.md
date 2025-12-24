# 用户打卡功能域 API 文档

## 概述
用户打卡功能域负责用户个人打卡规则管理、今日计划查看、统计信息等功能。

## API 列表

### 1. 获取用户今日打卡计划
- **端点**: `GET /api/user-checkin/today-plan`
- **描述**: 获取用户今日的打卡计划列表
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "date": "2025-12-24",
      "plans": [
        {
          "rule_id": 1,
          "rule_name": "早起打卡",
          "planned_time": "08:00:00",
          "status": "pending",
          "checkin_time": null,
          "icon_url": "https://example.com/icon.png"
        }
      ]
    }
  }
  ```

### 2. 获取用户打卡规则列表
- **端点**: `GET /api/user-checkin/rules`
- **描述**: 获取用户的所有打卡规则
- **请求头**: `Authorization: Bearer <token>`
- **查询参数**:
  - `status` (可选): 规则状态筛选 (active/inactive/all)
  - `page` (可选): 页码，默认1
  - `limit` (可选): 每页数量，默认20
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "rules": [
        {
          "rule_id": 1,
          "rule_name": "早起打卡",
          "frequency_type": 1,
          "week_days": 31,
          "time_slot_type": 1,
          "custom_time": "08:00:00",
          "status": 1,
          "created_at": "2025-12-24T08:00:00Z",
          "updated_at": "2025-12-24T08:00:00Z"
        }
      ],
      "pagination": {
        "page": 1,
        "limit": 20,
        "total": 5,
        "pages": 1
      }
    }
  }
  ```

### 3. 获取用户打卡规则详情
- **端点**: `GET /api/user-checkin/rules/<int:rule_id>`
- **描述**: 获取指定打卡规则的详细信息
- **请求头**: `Authorization: Bearer <token>`
- **路径参数**:
  - `rule_id`: 规则ID
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "rule_id": 1,
      "rule_name": "早起打卡",
      "frequency_type": 1,
      "week_days": 31,
      "time_slot_type": 1,
      "custom_time": "08:00:00",
      "status": 1,
      "created_at": "2025-12-24T08:00:00Z",
      "updated_at": "2025-12-24T08:00:00Z",
      "checkin_records": [
        {
          "record_id": 1,
          "checkin_time": "2025-12-24T08:05:00Z",
          "status": 1,
          "planned_time": "2025-12-24T08:00:00Z"
        }
      ]
    }
  }
  ```

### 4. 获取用户打卡统计信息
- **端点**: `GET /api/user-checkin/statistics`
- **描述**: 获取用户的打卡统计数据
- **请求头**: `Authorization: Bearer <token>`
- **查询参数**:
  - `period` (可选): 统计周期 (week/month/year)，默认month
  - `rule_id` (可选): 特定规则ID的统计
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "period": "month",
      "total_days": 30,
      "checked_days": 25,
      "checkin_rate": 83.3,
      "current_streak": 5,
      "longest_streak": 12,
      "rule_statistics": [
        {
          "rule_id": 1,
          "rule_name": "早起打卡",
          "total_checks": 25,
          "missed_checks": 5,
          "checkin_rate": 83.3
        }
      ]
    }
  }
  ```

### 5. 获取规则来源信息
- **端点**: `POST /api/user-checkin/rules/source-info`
- **描述**: 获取多个规则的来源和创建信息
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "rule_ids": [1, 2, 3]
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "rules": [
        {
          "rule_id": 1,
          "rule_name": "早起打卡",
          "source": "community",
          "creator_name": "社区管理员",
          "community_name": "安卡大家庭",
          "created_at": "2025-12-24T08:00:00Z"
        }
      ]
    }
  }
  ```

## 参数说明

### 频率类型 (frequency_type)
- `1`: 按周重复
- `2`: 工作日重复
- `3`: 自定义日期范围
- `4`: 每日重复

### 时间段类型 (time_slot_type)
- `1`: 早晨 (09:00)
- `2`: 下午 (14:00)
- `3`: 晚上 (20:00)
- `4`: 自定义时间

### 规则状态 (status)
- `1`: 启用
- `2`: 禁用
- `3`: 已删除

### 星期位掩码 (week_days)
使用位掩码表示星期，每位对应一天：
- 第0位: 星期一
- 第1位: 星期二
- 第2位: 星期三
- 第3位: 星期四
- 第4位: 星期五
- 第5位: 星期六
- 第6位: 星期日

例如：`31` (二进制 `11111`) 表示周一到周五

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 0 | 请求失败 |
| 1 | 请求成功 |

## 相关资源

- **源代码**: [../src/app/modules/user_checkin/routes.py](../src/app/modules/user_checkin/routes.py)
- **业务服务**: [../src/wxcloudrun/user_checkin_rule_service.py](../src/wxcloudrun/user_checkin_rule_service.py)

## 更新日志

### 2025-12-24
- 创建用户打卡功能域 API 文档
- 更新路由路径为 `/api/user-checkin/*` 格式
- 完善API参数说明和错误码说明