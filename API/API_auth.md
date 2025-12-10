# API 名称：微信登录
- 路径：POST /api/login
- 认证：无需认证
- 请求参数：
  - code（必填，string，微信授权码）
  - nickname（必填，string，用户昵称）
  - avatar_url（必填，string，用户头像URL）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "abc123def456...",
    "user_id": 1,
    "wechat_openid": "ox1234567890abcdef",
    "phone_number": "138****5678",
    "nickname": "张三",
    "avatar_url": "https://example.com/avatar.jpg",
    "role": "独居者",
    "login_type": "new_user"
  }
}
```
- 错误：400（缺少code、nickname或avatar_url参数）、401（微信API错误）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/login"
data = {
    "code": "wx_auth_code_here",
    "nickname": "张三",
    "avatar_url": "https://example.com/avatar.jpg"
}
response = requests.post(url, json=data)
print(response.json())
```

---

# API 名称：刷新Token
- 路径：POST /api/refresh_token
- 认证：无需认证（使用refresh_token）
- 请求参数：
  - refresh_token（必填，string，刷新令牌）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "new_refresh_token_here...",
    "expires_in": 7200
  }
}
```
- 错误：400（缺少refresh_token）、401（refresh_token无效或过期）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/refresh_token"
data = {
    "refresh_token": "your_refresh_token_here"
}
response = requests.post(url, json=data)
print(response.json())
```

---

# API 名称：用户登出
- 路径：POST /api/logout
- 认证：Bearer Token
- 请求参数：无
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "message": "登出成功"
  }
}
```
- 错误：401（token无效）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/logout"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, headers=headers)
print(response.json())
```

---

# API 名称：手机号注册
- 路径：POST /api/auth/register_phone
- 认证：无需认证
- 请求参数：
  - phone（必填，string，手机号）
  - code（必填，string，验证码）
  - nickname（可选，string，昵称）
  - avatar_url（可选，string，头像URL）
  - password（可选，string，密码，至少8位且包含字母和数字）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "abc123def456...",
    "user_id": 1,
    "wechat_openid": "phone_13812345678",
    "phone_number": "138****5678",
    "nickname": "张三",
    "avatar_url": "https://example.com/avatar.jpg",
    "role": "独居者",
    "login_type": "new_user"
  }
}
```
- 错误：400（参数缺失、验证码无效、密码强度不足）、409（手机号已注册）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/auth/register_phone"
data = {
    "phone": "13812345678",
    "code": "123456",
    "nickname": "张三",
    "password": "password123"
}
response = requests.post(url, json=data)
print(response.json())
```

---

# API 名称：手机号验证码登录
- 路径：POST /api/auth/login_phone_code
- 认证：无需认证
- 请求参数：
  - phone（必填，string，手机号）
  - code（必填，string，验证码）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "abc123def456...",
    "user_id": 1
  }
}
```
- 错误：400（参数缺失、验证码无效）、404（用户不存在）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/auth/login_phone_code"
data = {
    "phone": "13812345678",
    "code": "123456"
}
response = requests.post(url, json=data)
print(response.json())
```

---

# API 名称：手机号密码登录
- 路径：POST /api/auth/login_phone_password
- 认证：无需认证
- 请求参数：
  - phone（必填，string，手机号）
  - password（必填，string，密码）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "abc123def456...",
    "user_id": 1
  }
}
```
- 错误：400（参数缺失）、404（账号不存在）、401（密码不正确、账号未设置密码）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/auth/login_phone_password"
data = {
    "phone": "13812345678",
    "password": "password123"
}
response = requests.post(url, json=data)
print(response.json())
```

---

# API 名称：手机号验证码+密码登录
- 路径：POST /api/auth/login_phone
- 认证：无需认证
- 请求参数：
  - phone（必填，string，手机号）
  - code（必填，string，验证码）
  - password（必填，string，密码）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "abc123def456...",
    "user_id": 1,
    "wechat_openid": "phone_13812345678",
    "phone_number": "138****5678",
    "nickname": "张三",
    "avatar_url": "https://example.com/avatar.jpg",
    "role": "独居者",
    "login_type": "existing_user"
  }
}
```
- 错误：400（参数缺失、验证码无效）、404（账号不存在）、401（密码不正确、账号未设置密码）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/auth/login_phone"
data = {
    "phone": "13812345678",
    "code": "123456",
    "password": "password123"
}
response = requests.post(url, json=data)
print(response.json())
```