# API 名称：计数器操作
- 路径：POST /api/count
- 认证：无需认证
- 请求参数：
  - action（必填，string，操作类型：inc-递增，clear-清零）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": 5
}
```
或（清零操作）
```json
{
  "code": 0,
  "msg": "success",
  "data": null
}
```
- 错误：400（缺少action参数、action参数错误）、500（服务器错误）
- 示例代码：
```python
import requests

# 递增操作
url = "http://localhost:8080/api/count"
data = {
    "action": "inc"
}
response = requests.post(url, json=data)
print(response.json())

# 清零操作
data = {
    "action": "clear"
}
response = requests.post(url, json=data)
print(response.json())
```

---

# API 名称：获取计数器值
- 路径：GET /api/count
- 认证：无需认证
- 请求参数：无
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": 5
}
```
- 错误：500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/count"
response = requests.get(url)
print(response.json())
```

---

# API 名称：获取环境配置信息
- 路径：GET /api/get_envs
- 认证：无需认证
- 请求参数：
  - format（可选，string，返回格式：txt/toml-返回TOML格式文本，默认JSON）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "environment": "development",
    "config_source": ".env.unit",
    "variables": {
      "ENV_TYPE": {
        "value": "unit",
        "effective_value": "unit",
        "source": ".env.unit",
        "data_type": "string",
        "is_sensitive": false
      },
      "DEBUG": {
        "value": "true",
        "effective_value": "true",
        "source": ".env.unit",
        "data_type": "boolean",
        "is_sensitive": false
      }
    },
    "timestamp": "2025-12-09T10:30:00Z",
    "external_systems": {
      "sms": {
        "name": "短信服务",
        "is_mock": true,
        "status": "模拟模式",
        "config": {
          "provider": "mock",
          "debug_mode": true
        }
      },
      "wechat": {
        "name": "微信API",
        "is_mock": true,
        "status": "模拟模式",
        "config": {
          "app_id": "mock_app_id",
          "mock_mode": true
        }
      }
    }
  }
}
```
或（TOML格式）
```
# 安全守护应用环境配置信息
# 生成时间: 2025-12-09 10:30:00

[基础信息]
环境类型 = "development"
配置文件 = ".env.unit"

[环境变量]
DEBUG = "true"  # 数据类型: boolean
ENV_TYPE = "unit"  # 数据类型: string

[外部系统状态]
# 短信服务
sms.is_mock = true
sms.status = "模拟模式"
sms.配置 = {
  debug_mode = true
  provider = "mock"
}

# 微信API
wechat.is_mock = true
wechat.status = "模拟模式"
wechat.配置 = {
  app_id = "mock_app_id"
  mock_mode = true
}

# 配置信息结束
```
- 错误：500（服务器错误）
- 示例代码：
```python
import requests

# 获取JSON格式
url = "http://localhost:8080/api/get_envs"
response = requests.get(url)
print(response.json())

# 获取TOML格式
params = {
    "format": "toml"
}
response = requests.get(url, params=params)
print(response.text)  # 返回TOML格式文本
```

---

# API 名称：主页
- 路径：GET /
- 认证：无需认证
- 请求参数：无
- 响应：200 OK + HTML页面
- 错误：404（页面不存在）
- 示例代码：
```python
import requests

url = "http://localhost:8080/"
response = requests.get(url)
print(response.text)  # 返回HTML页面
```

---

# API 名称：环境配置查看器
- 路径：GET /env
- 认证：无需认证
- 请求参数：无
- 响应：200 OK + HTML页面
- 错误：404（页面不存在）
- 示例代码：
```python
import requests

url = "http://localhost:8080/env"
response = requests.get(url)
print(response.text)  # 返回HTML页面
```