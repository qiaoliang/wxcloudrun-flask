# API 名称：创建打卡分享链接
- 路径：POST /api/share/checkin/create
- 认证：Bearer Token
- 请求参数：
  - rule_id（必填，int，打卡规则ID）
  - expire_hours（可选，int，链接有效期小时数，默认168小时/7天）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "token": "abc123def456...",
    "url": "http://localhost:8080/share/check-in?token=abc123def456...",
    "mini_path": "/pages/supervisor-detail/supervisor-detail?token=abc123def456...",
    "expire_at": "2025-12-16 10:30:00"
  }
}
```
- 错误：400（缺少rule_id参数）、401（token无效）、404（打卡规则不存在或无权限）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/share/checkin/create"
data = {
    "rule_id": 1,
    "expire_hours": 72
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：解析分享链接
- 路径：GET /api/share/checkin/resolve
- 认证：Bearer Token
- 请求参数：
  - token（必填，string，分享令牌）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "rule": {
      "rule_id": 1,
      "rule_name": "晨练",
      "icon_url": "https://example.com/exercise.png",
      "frequency_type": 0,
      "time_slot_type": 1,
      "custom_time": null,
      "week_days": 127,
      "custom_start_date": null,
      "custom_end_date": null,
      "status": 1
    },
    "solo_user_id": 1
  }
}
```
- 错误：400（缺少token参数）、401（token无效）、404（链接无效或已过期）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/share/checkin/resolve"
params = {
    "token": "abc123def456..."
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, params=params, headers=headers)
print(response.json())
```

---

# API 名称：分享页面入口
- 路径：GET /share/check-in
- 认证：可选（可通过Authorization头自动建立监督关系）
- 请求参数：
  - token（必填，string，分享令牌）
- 响应：200 OK + HTML页面或JSON
- 错误：400（缺少token参数）、404（链接无效或已过期）、500（服务器错误）
- 示例代码：
```python
import requests

# 直接访问分享页面
url = "http://localhost:8080/share/check-in"
params = {
    "token": "abc123def456..."
}
response = requests.get(url, params=params)
print(response.text)  # 返回HTML页面

# 携带Authorization自动建立监督关系
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, params=params, headers=headers)
print(response.json())  # 返回JSON响应
```