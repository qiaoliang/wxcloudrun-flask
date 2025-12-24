# 打卡功能域 API 文档

## 概述
打卡功能域负责打卡规则管理、打卡记录、历史查询等功能。

## API 列表

### 1. 今日打卡事项
- **端点**: `GET /api/checkin/today`
- **描述**: 获取用户今日打卡事项列表
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "checkin_items": [
        {
          "rule_id": 1,
          "rule_name": "规则名称",
          "icon_url": "图标URL",
          "time_slot": "morning",
          "status": "unchecked",
          "checkin_time": null,
          "planned_time": "2025-12-19 08:00:00"
        }
      ],
      "date": "2025-12-19"
    }
  }
  ```

### 2. 执行打卡
- **端点**: `POST /api/checkin`
- **描述**: 执行打卡操作
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "rule_id": 1
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "record_id": 123,
      "rule_id": 1,
      "status": "checked",
      "checkin_time": "2025-12-19 08:05:00",
      "message": "打卡成功"
    }
  }
  ```

### 3. 标记missed
- **端点**: `POST /api/checkin/miss`
- **描述**: 标记当天规则为missed
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "rule_id": 1
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "record_id": 123,
      "rule_id": 1,
      "status": "missed",
      "message": "标记miss成功"
    }
  }
  ```

### 4. 撤销打卡
- **端点**: `POST /api/checkin/cancel`
- **描述**: 撤销打卡操作
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "record_id": 123
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "record_id": 123,
      "status": "unchecked",
      "message": "撤销打卡成功"
    }
  }
  ```

### 5. 打卡历史记录
- **端点**: `GET /api/checkin/history`
- **描述**: 获取打卡历史记录
- **请求头**: `Authorization: Bearer <token>`
- **查询参数**:
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
          "status": "checked",
          "created_at": "2025-12-19 08:05:00"
        }
      ]
    }
  }
  ```

### 6. 打卡规则管理
- **端点**: `GET /api/checkin/rules`
- **描述**: 获取打卡规则列表
- **请求头**: `Authorization: Bearer <token>`
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "rules": [
        {
          "rule_id": 1,
          "rule_name": "规则名称",
          "icon_url": "图标URL",
          "frequency_type": 0,
          "time_slot_type": 4,
          "custom_time": "08:00",
          "week_days": 127,
          "custom_start_date": "2025-01-01",
          "custom_end_date": "2025-12-31",
          "status": 1,
          "created_at": "2025-01-01 00:00:00",
          "updated_at": "2025-01-01 00:00:00"
        }
      ]
    }
  }
  ```

- **端点**: `POST /api/checkin/rules`
- **描述**: 创建打卡规则
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "rule_name": "规则名称",
    "icon_url": "图标URL",
    "frequency_type": 0,
    "time_slot_type": 4,
    "custom_time": "08:00",
    "week_days": 127,
    "custom_start_date": "2025-01-01",
    "custom_end_date": "2025-12-31",
    "status": 1
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "rule_id": 1,
      "message": "创建打卡规则成功"
    }
  }
  ```

- **端点**: `PUT /api/checkin/rules`
- **描述**: 更新打卡规则
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "rule_id": 1,
    "rule_name": "新规则名称",
    "icon_url": "新图标URL",
    "frequency_type": 1,
    "time_slot_type": 1,
    "custom_time": "09:00",
    "week_days": 65,
    "custom_start_date": "2025-02-01",
    "custom_end_date": "2025-11-30",
    "status": 1
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "rule_id": 1,
      "message": "更新打卡规则成功"
    }
  }
  ```

- **端点**: `DELETE /api/checkin/rules`
- **描述**: 删除打卡规则
- **请求头**: `Authorization: Bearer <token>`
- **请求体**:
  ```json
  {
    "rule_id": 1
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "rule_id": 1,
      "message": "删除打卡规则成功"
    }
  }
  ```

## 参数说明

### 频率类型 (frequency_type)
- `0`: 每天
- `1`: 每周
- `2`: 每月
- `3`: 自定义

### 时间段类型 (time_slot_type)
- `1`: 早晨 (06:00-09:00)
- `2`: 上午 (09:00-12:00)
- `3`: 中午 (12:00-14:00)
- `4`: 下午 (14:00-18:00)
- `5`: 晚上 (18:00-22:00)
- `6`: 自定义时间

### 星期位掩码 (week_days)
- 使用7位二进制表示一周7天（从周一开始）
- 例如：127 (0b1111111) 表示每天
- 例如：65 (0b1000001) 表示周一和周日

## 相关文件
- `backend/src/app/modules/checkin/routes.py`
- `backend/src/wxcloudrun/checkin_rule_service.py`
- `backend/src/wxcloudrun/checkin_record_service.py`