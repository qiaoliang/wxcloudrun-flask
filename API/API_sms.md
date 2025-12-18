# 短信服务域 API 文档

## 概述
短信服务域负责验证码发送和验证功能，支持多种验证码用途。

## API 列表

### 1. 发送验证码
- **端点**: `POST /api/sms/send_code`
- **描述**: 发送短信验证码到指定手机号
- **请求体**:
  ```json
  {
    "phone": "手机号",
    "purpose": "验证码用途"
  }
  ```
- **响应**:
  ```json
  {
    "code": 1,
    "msg": "success",
    "data": {
      "message": "验证码已发送"
    }
  }
  ```

## 参数说明

### 验证码用途 (purpose)
支持以下验证码用途：
- `register`: 注册
- `login`: 登录
- `bind_phone`: 绑定手机号
- `bind_wechat`: 绑定微信

### 验证码有效期
- 默认有效期：5分钟
- 可通过环境变量 `SMS_CODE_EXPIRY_MINUTES` 配置

### 频率限制
- 同一手机号同一用途的验证码发送间隔至少60秒
- 在mock环境下跳过频率限制检查

## 调试模式
在调试模式下，响应会包含验证码明文：

**请求头**:
```
X-Debug-Code: 1
```

**响应**:
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

## 环境配置

### 真实短信服务
当以下条件满足时使用真实短信服务：
- 环境变量 `USE_REAL_SMS` 设置为 `true`
- 配置了有效的短信服务商密钥

### Mock短信服务
在以下情况下使用Mock短信服务：
- 开发环境
- 测试环境
- 未配置真实短信服务

Mock服务会记录验证码到日志，但不会实际发送短信。

## 验证码验证
验证码验证通过工具函数 `_verify_sms_code` 进行：

```python
from wxcloudrun.utils.validators import _verify_sms_code

# 验证验证码
is_valid = _verify_sms_code(phone, purpose, code)
```

## 相关文件
- `backend/src/wxcloudrun/views/sms.py`
- `backend/src/wxcloudrun/sms_service.py`
- `backend/src/wxcloudrun/utils/validators.py`
- `backend/src/config_manager.py`