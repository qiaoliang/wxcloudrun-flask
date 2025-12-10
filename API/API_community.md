# API 名称：获取社区列表
- 路径：GET /api/communities
- 认证：Bearer Token（超级管理员权限）
- 请求参数：无
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": [
    {
      "community_id": 1,
      "name": "安卡大家庭",
      "description": "系统默认社区，新注册用户自动加入",
      "status": 1,
      "status_name": "enabled",
      "location": null,
      "is_default": true,
      "created_at": "2025-12-10T10:00:00Z",
      "updated_at": "2025-12-10T10:00:00Z",
      "creator": {
        "user_id": 1,
        "nickname": "系统超级管理员"
      },
      "admin_count": 1,
      "user_count": 50
    },
    {
      "community_id": 2,
      "name": "测试社区",
      "description": "用于测试的社区",
      "status": 1,
      "status_name": "enabled",
      "location": "北京市",
      "is_default": false,
      "created_at": "2025-12-10T11:00:00Z",
      "updated_at": "2025-12-10T11:00:00Z",
      "creator": {
        "user_id": 1,
        "nickname": "系统超级管理员"
      },
      "admin_count": 2,
      "user_count": 10
    }
  ]
}
```
- 错误：401（token无效）、403（权限不足，需要超级管理员权限）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/communities"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())
```

---

# API 名称：获取社区详情
- 路径：GET /api/communities/{community_id}
- 认证：Bearer Token（社区管理员或超级管理员）
- 请求参数：
  - community_id（必填，int，社区ID）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "community_id": 2,
    "name": "测试社区",
    "description": "用于测试的社区",
    "status": 1,
    "status_name": "enabled",
    "location": "北京市",
    "is_default": false,
    "created_at": "2025-12-10T11:00:00Z",
    "updated_at": "2025-12-10T11:00:00Z",
    "creator": {
      "user_id": 1,
      "nickname": "系统超级管理员"
    },
    "admin_count": 2,
    "user_count": 10,
    "admins": [
      {
        "user_id": 2,
        "nickname": "社区管理员",
        "avatar_url": "https://example.com/avatar.jpg",
        "role": 1,
        "role_name": "primary",
        "created_at": "2025-12-10T11:00:00Z"
      },
      {
        "user_id": 3,
        "nickname": "管理员助理",
        "avatar_url": "https://example.com/avatar2.jpg",
        "role": 2,
        "role_name": "normal",
        "created_at": "2025-12-10T12:00:00Z"
      }
    ]
  }
}
```
- 错误：401（token无效）、403（权限不足）、404（社区不存在）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/communities/2"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())
```

---

# API 名称：获取社区管理员列表
- 路径：GET /api/communities/{community_id}/admins
- 认证：Bearer Token（社区管理员或超级管理员）
- 请求参数：
  - community_id（必填，int，社区ID）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": [
    {
      "user_id": 2,
      "nickname": "社区管理员",
      "avatar_url": "https://example.com/avatar.jpg",
      "phone_number": "138****5678",
      "role": 1,
      "role_name": "primary",
      "created_at": "2025-12-10T11:00:00Z"
    },
    {
      "user_id": 3,
      "nickname": "管理员助理",
      "avatar_url": "https://example.com/avatar2.jpg",
      "phone_number": "139****1234",
      "role": 2,
      "role_name": "normal",
      "created_at": "2025-12-10T12:00:00Z"
    }
  ]
}
```
- 错误：401（token无效）、403（权限不足）、404（社区不存在）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/communities/2/admins"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())
```

---

# API 名称：添加社区管理员
- 路径：POST /api/communities/{community_id}/admins
- 认证：Bearer Token（社区管理员或超级管理员）
- 请求参数：
  - community_id（必填，int，社区ID，路径参数）
  - user_ids（必填，array，用户ID列表）
  - role（可选，int，管理员角色：1-主管理员，2-普通管理员，默认2）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": [
    {
      "user_id": 4,
      "success": true,
      "message": "添加成功"
    },
    {
      "user_id": 5,
      "success": false,
      "message": "用户已经是该社区的管理员"
    }
  ]
}
```
- 错误：401（token无效）、403（权限不足）、404（社区不存在）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/communities/2/admins"
data = {
    "user_ids": [4, 5],
    "role": 2
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：移除社区管理员
- 路径：DELETE /api/communities/{community_id}/admins/{user_id}
- 认证：Bearer Token（社区管理员或超级管理员）
- 请求参数：
  - community_id（必填，int，社区ID，路径参数）
  - user_id（必填，int，用户ID，路径参数）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "message": "移除成功"
  }
}
```
- 错误：401（token无效）、403（权限不足）、404（社区或管理员不存在）、400（不能移除唯一的主管理员）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/communities/2/admins/4"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.delete(url, headers=headers)
print(response.json())
```

---

# API 名称：获取社区用户列表
- 路径：GET /api/communities/{community_id}/users
- 认证：Bearer Token（社区管理员或超级管理员）
- 请求参数：
  - community_id（必填，int，社区ID，路径参数）
  - keyword（可选，string，搜索关键词：昵称或手机号）
  - page（可选，int，页码，默认1）
  - per_page（可选，int，每页数量，默认20）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "users": [
      {
        "user_id": 6,
        "nickname": "普通用户",
        "avatar_url": "https://example.com/avatar3.jpg",
        "phone_number": "137****9876",
        "role": 1,
        "role_name": "solo",
        "verification_status": 2,
        "created_at": "2025-12-10T13:00:00Z"
      }
    ],
    "total": 1,
    "pages": 1,
    "current_page": 1,
    "per_page": 20
  }
}
```
- 错误：401（token无效）、403（权限不足）、404（社区不存在）、500（服务器错误）
- 示例代码：
```python
import requests

# 获取用户列表
url = "http://localhost:8080/api/communities/2/users"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())

# 搜索用户
params = {
    "keyword": "普通",
    "page": 1,
    "per_page": 10
}
response = requests.get(url, params=params, headers=headers)
print(response.json())
```

---

# API 名称：将用户设为社区管理员
- 路径：POST /api/communities/{community_id}/users/{user_id}/set-admin
- 认证：Bearer Token（社区管理员或超级管理员）
- 请求参数：
  - community_id（必填，int，社区ID，路径参数）
  - user_id（必填，int，用户ID，路径参数）
  - role（可选，int，管理员角色：1-主管理员，2-普通管理员，默认2）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "message": "设置成功"
  }
}
```
- 错误：401（token无效）、403（权限不足）、404（社区或用户不存在）、400（用户已经是管理员）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/communities/2/users/6/set-admin"
data = {
    "role": 2
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：提交社区加入申请
- 路径：POST /api/community/applications
- 认证：Bearer Token
- 请求参数：
  - community_id（必填，int，目标社区ID）
  - reason（可选，string，申请理由）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "message": "申请已提交"
  }
}
```
- 错误：401（token无效）、400（社区不存在、用户已是社区成员、已有待处理申请）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/community/applications"
data = {
    "community_id": 2,
    "reason": "我想加入这个社区"
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：获取社区申请列表
- 路径：GET /api/community/applications
- 认证：Bearer Token（社区管理员或超级管理员）
- 请求参数：无
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": [
    {
      "application_id": 1,
      "user": {
        "user_id": 6,
        "nickname": "普通用户",
        "avatar_url": "https://example.com/avatar3.jpg",
        "phone_number": "137****9876",
        "role": 1,
        "role_name": "solo"
      },
      "community": {
        "community_id": 2,
        "name": "测试社区",
        "description": "用于测试的社区"
      },
      "reason": "我想加入这个社区",
      "status": 1,
      "status_name": "pending",
      "created_at": "2025-12-10T14:00:00Z"
    }
  ]
}
```
- 错误：401（token无效）、403（权限不足）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/community/applications"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())
```

---

# API 名称：批准社区申请
- 路径：PUT /api/community/applications/{application_id}/approve
- 认证：Bearer Token（社区管理员或超级管理员）
- 请求参数：
  - application_id（必填，int，申请ID，路径参数）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "message": "批准成功"
  }
}
```
- 错误：401（token无效）、403（权限不足）、404（申请不存在）、400（申请已被处理）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/community/applications/1/approve"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.put(url, headers=headers)
print(response.json())
```

---

# API 名称：拒绝社区申请
- 路径：PUT /api/community/applications/{application_id}/reject
- 认证：Bearer Token（社区管理员或超级管理员）
- 请求参数：
  - application_id（必填，int，申请ID，路径参数）
  - rejection_reason（必填，string，拒绝理由）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "message": "拒绝成功"
  }
}
```
- 错误：401（token无效）、403（权限不足）、404（申请不存在）、400（申请已被处理、缺少拒绝理由）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/community/applications/1/reject"
data = {
    "rejection_reason": "不符合社区要求"
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.put(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：获取用户社区信息
- 路径：GET /api/user/community
- 认证：Bearer Token
- 请求参数：无
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "community": {
      "community_id": 1,
      "name": "安卡大家庭",
      "description": "系统默认社区，新注册用户自动加入",
      "is_default": true
    },
    "is_admin": false,
    "is_primary_admin": false
  }
}
```
或（用户未加入社区）
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "community": null
  }
}
```
- 错误：401（token无效）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/user/community"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())
```

---

# API 名称：获取可申请的社区列表
- 路径：GET /api/communities/available
- 认证：Bearer Token
- 请求参数：无
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": [
    {
      "community_id": 2,
      "name": "测试社区",
      "description": "用于测试的社区",
      "location": "北京市",
      "user_count": 10
    },
    {
      "community_id": 3,
      "name": "阳光社区",
      "description": "充满阳光的社区",
      "location": "上海市",
      "user_count": 25
    }
  ]
}
```
- 错误：401（token无效）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/communities/available"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())
```