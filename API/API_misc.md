# 其他功能域 API 文档

## 概述
其他功能域包含计数器、环境配置、首页等辅助功能。

## API 列表

### 1. 首页
- **端点**: `GET /`
- **描述**: 返回index页面
- **响应**: HTML页面

### 2. 环境配置查看器
- **端点**: `GET /env`
- **描述**: 返回环境配置查看器页面
- **响应**: HTML页面

### 3. 计数器操作
- **端点**: `POST /api/count`
- **描述**: 计数器操作（自增、清零、清理用户数据）
- **请求体**:
  ```json
  {
    "action": "inc"  // inc/clear/clear_users
  }
  ```
- **响应**:
  - **自增操作**:
    ```json
    {
      "code": 1,
      "msg": "success",
      "data": 5
    }
    ```
  - **清零操作**:
    ```json
    {
      "code": 1,
      "msg": "success",
      "data": {}
    }
    ```
  - **清理用户数据**:
    ```json
    {
      "code": 1,
      "msg": "success",
      "data": {}
    }
    ```

- **端点**: `GET /api/count`
- **描述**: 获取计数器的值
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": 5
  }
  ```

### 4. 获取环境配置信息
- **端点**: `GET /api/get_envs`
- **描述**: 获取环境配置详细信息（支持JSON和TOML格式）
- **查询参数**:
  - `format`: 返回格式（txt/toml/json，默认json）
- **响应格式**:
  - **JSON格式（默认）**:
    ```json
    {
      "code": 1,
      "msg": "success",
      "data": {
        "environment": "function",
        "config_source": ".env.function",
        "variables": {
          "ENV_TYPE": {
            "effective_value": "function",
            "data_type": "string",
            "is_sensitive": false
          }
        },
        "timestamp": "2025-12-19T10:00:00Z",
        "external_systems": {
          "sms": {
            "name": "短信服务",
            "is_mock": true,
            "status": "mock",
            "config": {
              "provider": "mock"
            }
          }
        }
      }
    }
    ```
  - **TOML格式** (`format=txt` 或 `format=toml`):
    ```toml
    # 安全守护应用环境配置信息
    # 生成时间: 2025-12-19 10:00:00
    
    [基础信息]
    环境类型 = "function"
    配置文件 = ".env.function"
    
    [环境变量]
    ENV_TYPE = "function"  # 数据类型: string
    
    [外部系统状态]
    # 短信服务
    sms.is_mock = true
    sms.status = "mock"
    sms.配置 = {
      provider = "mock"
    }
    
    # 配置信息结束
    ```

## 功能说明

### 1. 计数器功能
主要用于演示和测试：
- `inc`: 计数器自增
- `clear`: 计数器清零
- `clear_users`: 清理所有用户数据（仅测试环境使用）

### 2. 环境配置查看器
提供可视化界面查看当前环境配置：
- 环境变量值
- 数据类型
- 敏感信息标记
- 外部系统状态

### 3. 环境配置信息API
支持多种格式返回配置信息：
- **JSON格式**: 结构化数据，便于程序处理
- **TOML格式**: 易于阅读的文本格式

### 4. 外部系统状态检测
自动检测外部系统状态：
- **短信服务**: 检测是否使用真实短信服务
- **数据库**: 检测数据库连接状态
- **缓存服务**: 检测缓存服务状态

## 配置分析
配置管理器会分析所有环境配置文件：
1. 确定当前环境类型（function/unit/uat/prod）
2. 加载对应的配置文件
3. 分析环境变量数据类型
4. 标记敏感信息
5. 检测外部系统状态

## 相关文件
- `backend/src/app/modules/misc/routes.py`
- `backend/src/config_manager.py`
- `backend/src/wxcloudrun/dao.py`