在微信 API 登录场景中使用 `pyjwt` 出现 `DecodeError`，核心原因通常是 **JWT 格式/签名不匹配、密钥错误、算法不兼容**，或微信返回的 Token 并非标准 JWT（可能是微信自定义的票据格式）。以下是具体分析和解决方案：

### 一、先明确核心前提：微信 API 中“需要 JWT 处理的 Token 类型”

微信登录相关的 Token 主要有 3 类，并非所有都需要用 `pyjwt` 解码，先确认你处理的是哪一种：
| Token 类型 | 用途 | 是否为标准 JWT？ | 正确处理方式 |
|------------------|-----------------------|------------------|---------------------------------------|
| `code` | 授权临时票据（前端获取） | 否（短字符串） | 用 `code` 调用微信接口换 `access_token` |
| `access_token` | 接口调用凭证 | 否（微信自定义格式） | 直接作为接口请求头/参数使用，无需解码 |
| `id_token` | 仅 OAuth2.0 授权时返回 | 是（标准 JWT） | 需用微信公钥验证签名并解码 |

**常见误区**：把 `code` 或 `access_token` 当作 JWT 用 `pyjwt.decode()` 解析，直接导致 `DecodeError`（因为格式根本不是 JWT）。

### 二、如果确实是 `id_token`（标准 JWT），`DecodeError` 的 5 大原因及解决方案

`pyjwt` 的 `DecodeError` 本质是“无法解析 Token 结构”或“签名验证失败”，按优先级排查：

#### 1. Token 格式错误（最常见）

JWT 必须是 **3 段用 `.` 分隔的 Base64URL 编码字符串**（格式：`header.payload.signature`）。

-   错误场景：
    -   把微信返回的 `code`（如 `011Ee40004wHh1F5q20007k100Ee409`）或 `access_token`（如 `73_Y7Z...`）当作 JWT 解析；
    -   Token 被截断、多空格、转义符（如 `\n`）污染；
    -   复制粘贴时遗漏部分字符（如末尾少 `=` 或签名段）。
-   解决方案：
    -   先打印 Token 字符串，检查是否符合 `xxx.xxx.xxx` 格式；
    -   用 `token.split('.')` 拆分，若长度不等于 3，直接确认 Token 类型错误；
    -   清除 Token 中的空格、换行符：`token = token.strip().replace('\n', '')`。

#### 2. 签名验证失败（算法/密钥不匹配）

JWT 解码时必须验证签名（除非显式关闭，不推荐），微信 `id_token` 用 **RS256 算法**（非 HS256），且需要微信的 **公钥** 验证。

-   错误场景：
    -   用 HS256 算法解码（微信不用对称加密）；
    -   密钥填错（把自己的 AppSecret 当作公钥，或用了错误的微信公钥）；
    -   关闭签名验证后，Payload 格式仍不合法。
-   解决方案：

    -   步骤 1：获取微信官方公钥
        微信 OAuth2.0 公钥需从接口获取（定期更新）：

        ```python
        import requests

        # 微信开放平台公钥接口（需替换为你的 appid）
        appid = "你的微信开放平台 appid"
        public_key_url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={你的 AppSecret}"
        resp = requests.get(public_key_url).json()
        # 注意：实际需从返回的 `public_key` 字段提取，或通过微信开放平台“API安全”页面下载
        ```

    -   步骤 2：正确调用 `pyjwt.decode()`
        必须指定算法为 `RS256`，并传入微信公钥（而非 AppSecret）：

        ```python
        import jwt
        from cryptography.hazmat.primitives import serialization

        # 假设已获取微信公钥字符串（PEM格式）
        wechat_public_key_pem = """-----BEGIN PUBLIC KEY-----
        MIIBIjANBgkqhkiG9w0BAQEFAAO...（微信公钥内容）
        -----END PUBLIC KEY-----"""

        # 解析公钥（cryptography 是 pyjwt 依赖，需安装：pip install cryptography）
        public_key = serialization.load_pem_public_key(wechat_public_key_pem.encode("utf-8"))

        # 解码 id_token（关键：algorithm="RS256"，用公钥验证签名）
        try:
            payload = jwt.decode(
                token=your_id_token,
                key=public_key,
                algorithms=["RS256"],
                options={
                    "verify_signature": True,  # 必须验证签名（默认开启，不建议关闭）
                    "verify_exp": True,        # 验证 Token 过期时间（默认开启）
                },
                issuer="https://open.weixin.qq.com",  # 可选：验证签发者（微信固定值）
                audience=appid  # 可选：验证受众（你的 appid）
            )
            print("解码成功：", payload)
        except jwt.DecodeError as e:
            print("格式/签名错误：", str(e))
        except jwt.ExpiredSignatureError as e:
            print("Token 已过期：", str(e))
        except jwt.InvalidIssuerError as e:
            print("签发者错误：", str(e))
        ```

#### 3. PyJWT 版本或依赖问题

-   错误场景：
    -   PyJWT 版本过低（如 1.x），不支持 RS256 算法或最新的 JWT 标准；
    -   缺少 `cryptography` 依赖（PyJWT 2.x+ 解析公钥需此库）。
-   解决方案：
    ```bash
    # 升级 PyJWT 并安装依赖
    pip install --upgrade pyjwt cryptography
    ```

#### 4. Token 已过期或被篡改

-   错误场景：
    -   `id_token` 过期（微信 `id_token` 有效期较短，通常 1 小时内）；
    -   Token 被手动修改（如修改 Payload 内容），导致签名不匹配。
-   解决方案：
    -   重新通过微信授权流程获取最新的 `id_token`；
    -   解码时保留 `verify_exp=True`（默认开启），捕获 `jwt.ExpiredSignatureError` 单独处理。

#### 5. Base64URL 解码失败

JWT 的 Header 和 Payload 是 Base64URL 编码（非标准 Base64），`pyjwt` 会自动处理，但如果 Token 被非法修改（如把 `_` 改成 `/`），会导致解码失败。

-   解决方案：

    -   确保 Token 是微信返回的原始值，未被二次修改；
    -   手动修复 Base64URL 编码（若 Token 被意外篡改）：

        ```python
        def fix_base64url(token):
            # Base64URL 转标准 Base64（补 = 填充）
            token = token.replace('-', '+').replace('_', '/')
            padding = 4 - (len(token) % 4)
            if padding != 4:
                token += '=' * padding
            return token

        # 对 Token 的每一段修复（若需要）
        parts = your_id_token.split('.')
        if len(parts) == 3:
            parts = [fix_base64url(part) for part in parts]
            fixed_token = '.'.join(parts)
        ```

### 三、关键总结

1. 先确认 Token 类型：**只有 `id_token` 是标准 JWT**，`code` 和 `access_token` 无需用 `pyjwt` 解码；
2. 核心错误原因：Token 格式错误 > 签名算法/公钥不匹配 > 依赖/版本问题；
3. 必须用 **RS256 算法 + 微信公钥** 解码 `id_token`，不能用 AppSecret（HS256 是对称加密，微信不用）；
4. 捕获具体异常（`DecodeError`/`ExpiredSignatureError` 等），便于定位问题。

如果仍报错，建议：

-   打印完整的 Token 字符串，确认是否为 `xxx.xxx.xxx` 格式；
-   用 [JWT.io](https://jwt.io/) 在线工具验证 Token（粘贴 Token 后，选择算法 RS256，输入微信公钥，查看是否能解析）；
-   检查微信开放平台的 AppID、AppSecret 是否正确，授权流程是否完整。
