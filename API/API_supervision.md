# API 名称：邀请监督者
- 路径：POST /api/rules/supervision/invite
- 认证：Bearer Token
- 请求参数：
  - invite_type（可选，string，邀请类型，默认wechat）
  - rule_ids（可选，array，要监督的规则ID列表，空数组表示监督所有规则）
  - target_openid（必填，string，被邀请用户的openid）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "message": "邀请发送成功"
  }
}
```
- 错误：400（缺少target_openid参数、规则不存在或不属于当前用户）、401（token无效）、404（被邀请用户不存在）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/rules/supervision/invite"
data = {
    "invite_type": "wechat",
    "rule_ids": [1, 2],
    "target_openid": "ox1234567890abcdef"
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())

# 监督所有规则
data_all = {
    "target_openid": "ox1234567890abcdef",
    "rule_ids": []
}
response = requests.post(url, json=data_all, headers=headers)
print(response.json())
```

---

# API 名称：生成监督邀请链接
- 路径：POST /api/rules/supervision/invite_link
- 认证：Bearer Token
- 请求参数：
  - rule_ids（可选，array，要监督的规则ID列表，空数组表示监督所有规则）
  - expire_hours（可选，int，链接有效期小时数，默认72小时）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "invite_token": "abc123def456...",
    "mini_path": "/pages/supervisor-invite/supervisor-invite?token=abc123def456...",
    "expire_at": "2025-12-12 10:30:00"
  }
}
```
- 错误：401（token无效）、404（规则不存在或不属于当前用户）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/rules/supervision/invite_link"
data = {
    "rule_ids": [1, 2],
    "expire_hours": 48
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：解析监督邀请链接
- 路径：GET /api/rules/supervision/invite/resolve
- 认证：Bearer Token
- 请求参数：
  - token（必填，string，邀请令牌）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "relation_id": 123,
    "status": "待同意",
    "solo_user_id": 1,
    "rule_id": 1
  }
}
```
- 错误：400（缺少token参数）、401（token无效）、404（邀请链接无效或已过期）、409（邀请已被其他用户处理）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/rules/supervision/invite/resolve"
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

# API 名称：获取监督邀请列表
- 路径：GET /api/rules/supervision/invitations
- 认证：Bearer Token
- 请求参数：
  - type（可选，string，类型：received-收到的邀请，sent-发出的邀请，默认received）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "type": "received",
    "invitations": [
      {
        "relation_id": 123,
        "solo_user": {
          "user_id": 1,
          "nickname": "张三",
          "avatar_url": "https://example.com/avatar1.jpg"
        },
        "rule": {
          "rule_id": 1,
          "rule_name": "晨练"
        },
        "status": "待同意",
        "created_at": "2025-12-09 10:30:00"
      }
    ]
  }
}
```
- 错误：401（token无效）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/rules/supervision/invitations"
params = {
    "type": "received"
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, params=params, headers=headers)
print(response.json())
```

---

# API 名称：接受监督邀请
- 路径：POST /api/rules/supervision/accept
- 认证：Bearer Token
- 请求参数：
  - relation_id（必填，int，邀请关系ID）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "message": "接受邀请成功"
  }
}
```
- 错误：400（缺少relation_id参数、邀请已接受）、401（token无效）、404（邀请关系不存在或无权限）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/rules/supervision/accept"
data = {
    "relation_id": 123
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：拒绝监督邀请
- 路径：POST /api/rules/supervision/reject
- 认证：Bearer Token
- 请求参数：
  - relation_id（必填，int，邀请关系ID）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "message": "拒绝邀请成功"
  }
}
```
- 错误：400（缺少relation_id参数）、401（token无效）、404（邀请关系不存在或无权限）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/rules/supervision/reject"
data = {
    "relation_id": 123
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：获取我监督的用户列表
- 路径：GET /api/rules/supervision/my_supervised
- 认证：Bearer Token
- 请求参数：无
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "supervised_users": [
      {
        "user_id": 1,
        "nickname": "张三",
        "avatar_url": "https://example.com/avatar1.jpg",
        "rules": [
          {
            "rule_id": 1,
            "rule_name": "晨练",
            "icon_url": "https://example.com/exercise.png"
          },
          {
            "rule_id": 2,
            "rule_name": "服药",
            "icon_url": "https://example.com/medicine.png"
          }
        ],
        "today_checkin_status": [
          {
            "rule_id": 1,
            "rule_name": "晨练",
            "status": "checked",
            "checkin_time": "08:45:30"
          },
          {
            "rule_id": 2,
            "rule_name": "服药",
            "status": "unchecked",
            "checkin_time": null
          }
        ]
      }
    ]
  }
}
```
- 错误：401（token无效）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/rules/supervision/my_supervised"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())
```

---

# API 名称：获取我的监护人列表
- 路径：GET /api/rules/supervision/my_guardians
- 认证：Bearer Token
- 请求参数：无
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "guardians": [
      {
        "user_id": 2,
        "nickname": "李四",
        "avatar_url": "https://example.com/avatar2.jpg"
      },
      {
        "user_id": 3,
        "nickname": "王五",
        "avatar_url": "https://example.com/avatar3.jpg"
      }
    ]
  }
}
```
- 错误：401（token无效）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/rules/supervision/my_guardians"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())
```

---

# API 名称：获取被监督用户打卡记录
- 路径：GET /api/rules/supervision/records
- 认证：Bearer Token
- 请求参数：
  - solo_user_id（必填，int，被监督用户ID）
  - rule_id（可选，int，特定规则ID）
  - start_date（可选，string，开始日期，默认7天前，格式：YYYY-MM-DD）
  - end_date（可选，string，结束日期，默认今天，格式：YYYY-MM-DD）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "start_date": "2025-12-02",
    "end_date": "2025-12-09",
    "history": [
      {
        "record_id": 120,
        "rule_id": 1,
        "rule_name": "晨练",
        "icon_url": "https://example.com/exercise.png",
        "planned_time": "2025-12-09 09:00:00",
        "checkin_time": "2025-12-09 08:45:30",
        "status": "已打卡",
        "created_at": "2025-12-09 08:45:30"
      }
    ]
  }
}
```
- 错误：400（缺少solo_user_id参数、日期格式错误）、401（token无效）、403（无权限监督该用户或规则）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/rules/supervision/records"
params = {
    "solo_user_id": 1,
    "rule_id": 1,
    "start_date": "2025-12-01",
    "end_date": "2025-12-09"
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, params=params, headers=headers)
print(response.json())
```