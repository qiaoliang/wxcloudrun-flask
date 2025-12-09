# API 名称：发送短信验证码
- 路径：POST /api/sms/send_code
- 认证：无需认证
- 请求参数：
  - phone（必填，string，手机号）
  - purpose（可选，string，验证码用途：register-注册，login-登录，bind_phone-绑定手机，bind_wechat-绑定微信，默认register）
- 响应：200 OK + 示例 JSON
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "message": "验证码已发送"
  }
}
```
或（调试模式下）
```json
{
  "code": 1,
  "msg": "success",
  "data": {
    "message": "验证码已发送",
    "debug_code": "123456"
  }
}
```
- 错误：400（缺少phone参数）、429（请求过于频繁，60秒内只能发送一次）、500（服务器错误）
- 示例代码：
```python
import requests

url = "http://localhost:8080/api/sms/send_code"
data = {
    "phone": "13812345678",
    "purpose": "register"
}
response = requests.post(url, json=data)
print(response.json())

# 调试模式获取验证码
headers = {
    "X-Debug-Code": "1"
}
response = requests.post(url, json=data, headers=headers)
print(response.json())
```