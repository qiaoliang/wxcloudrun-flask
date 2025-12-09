# API 名称：获取/更新用户信息
- 路径：GET/POST /api/user/profile
- 认证：Bearer Token
- 请求参数：
  - GET：无参数
  - POST：
    - nickname（可选，string，昵称）
    - avatar_url（可选，string，头像URL）
    - phone_number（可选，string，手机号）
    - role（可选，int/string，角色：1-独居者，2-监护人，3-社区工作者）
    - community_id（可选，int，社区ID）
    - status（可选，int/string，状态：1-正常，2-禁用）
    - is_solo_user（可选，bool，是否为独居者）
    - is_supervisor（可选，bool，是否为监护人）
    - is_community_worker（可选，bool，是否为社区工作者）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "user_id": 1,
    "wechat_openid": "ox1234567890abcdef",
    "phone_number": "138****5678",
    "nickname": "张三",
    "avatar_url": "https://example.com/avatar.jpg",
    "role": "独居者",
    "community_id": 1001,
    "status": "正常",
    "is_solo_user": true,
    "is_supervisor": false,
    "is_community_worker": false
  }
}
```
- 错误：401（token无效/过期/格式错误）、404（用户不存在）、500（服务器错误）
- 示例代码：
```python
import requests

# 获取用户信息
url = "http://localhost:8080/api/user/profile"
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, headers=headers)
print(response.json())

# 更新用户信息
update_data = {
    "nickname": "新昵称",
    "avatar_url": "https://example.com/new_avatar.jpg"
}
response = requests.post(url, json=update_data, headers=headers)
print(response.json())
```

---

# API 名称：搜索用户
- 路径：GET /api/users/search
- 认证：Bearer Token
- 请求参数：
  - nickname（必填，string，昵称关键词）
  - limit（可选，int，返回数量限制，默认10）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "users": [
      {
        "user_id": 2,
        "nickname": "李四",
        "avatar_url": "https://example.com/avatar2.jpg",
        "is_supervisor": true
      },
      {
        "user_id": 3,
        "nickname": "王五",
        "avatar_url": "https://example.com/avatar3.jpg",
        "is_supervisor": false
      }
    ]
  }
}
```
- 错误：400（缺少nickname参数）、401（token无效）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/users/search"
params = {
    "nickname": "张",
    "limit": 5
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.get(url, params=params, headers=headers)
print(response.json())
```

---

# API 名称：绑定手机号
- 路径：POST /api/user/bind_phone
- 认证：Bearer Token
- 请求参数：
  - phone（必填，string，手机号）
  - code（必填，string，验证码）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "message": "绑定手机号成功"
  }
}
```
或（账号合并时）
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "message": "绑定手机号成功，账号已合并"
  }
}
```
- 错误：400（参数缺失、验证码无效）、401（token无效）、409（手机号已被其他账号绑定）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/user/bind_phone"
data = {
    "phone": "13812345678",
    "code": "123456"
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：绑定微信
- 路径：POST /api/user/bind_wechat
- 认证：Bearer Token
- 请求参数：
  - code（必填，string，微信授权码）
  - phone（可选，string，手机号，用于验证）
  - phone_code（可选，string，手机验证码）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "message": "绑定微信成功"
  }
}
```
或（账号合并时）
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "message": "绑定微信成功，账号已合并"
  }
}
```
- 错误：400（缺少code参数）、401（token无效、手机验证码无效）、409（微信已被其他账号绑定）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/user/bind_wechat"
data = {
    "code": "wx_auth_code_here",
    "phone": "13812345678",
    "phone_code": "123456"
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```

---

# API 名称：社区工作人员身份验证
- 路径：POST /api/community/verify
- 认证：Bearer Token
- 请求参数：
  - name（必填，string，真实姓名）
  - workId（必填，string，工号或身份证号）
  - workProof（必填，string，工作证明照片URL或base64）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "message": "身份验证申请已提交，请耐心等待审核",
    "verification_status": "pending"
  }
}
```
- 错误：400（参数缺失）、401（token无效）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/community/verify"
data = {
    "name": "张三",
    "workId": "123456789",
    "workProof": "https://example.com/work_proof.jpg"
}
headers = {
    "Authorization": "Bearer your_access_token_here"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```