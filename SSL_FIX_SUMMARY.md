# SSL证书问题修复方案

## 问题描述
生产环境中出现SSL证书验证失败错误：
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1010)
```

## 解决方案
通过更新Docker镜像中的系统CA证书和Python certifi包来解决SSL证书验证问题。

## 修改内容

### 1. Dockerfile 修改
```dockerfile
# 更新系统包并安装最新的CA证书
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        && \
    apt-get upgrade -y ca-certificates && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# 安装依赖并升级certifi包到最新版本
RUN pip install --user -r requirements.txt && \
    pip install --user --upgrade certifi
```

### 2. 容器名称统一更新
- 镜像名称：`safeguard-prod-img` → `s-prod`
- 容器名称：`safeguard-prod` → `s-prod`

### 3. 新增脚本文件
- `scripts/test_ssl_fix.sh` - SSL连接测试脚本
- `scripts/verify_ssl_fix.sh` - 修改验证脚本

## 修复原理

### 系统CA证书更新
- 使用 `apt-get upgrade -y ca-certificates` 确保系统CA证书是最新的
- 清理包缓存和临时文件减少镜像大小

### Python certifi包升级
- certifi包包含了Mozilla CA证书包，Python的requests库依赖它进行SSL验证
- 升级到最新版本确保证书库是最新的

## 安全性
✅ **保持SSL验证开启** - 没有使用 `verify=False`，保持安全性
✅ **更新可信CA证书** - 使用官方最新的CA证书包
✅ **无需代码修改** - 纯粹通过基础设施更新解决问题

## 使用方法

### 构建和运行生产环境
```bash
# 构建镜像
./scripts/build-prod.sh

# 运行容器
./scripts/run-prod.sh
```

### 测试SSL连接
```bash
# 运行SSL连接测试
./scripts/test_ssl_fix.sh
```

### 验证修改
```bash
# 验证所有修改是否正确
./scripts/verify_ssl_fix.sh
```

## 预期效果
1. 解决生产环境中的SSL证书验证失败问题
2. 保持应用的安全性（不禁用SSL验证）
3. 提高与微信API连接的稳定性
4. 减少因证书问题导致的网络请求失败

## 注意事项
1. 需要重新构建Docker镜像才能生效
2. 建议在测试环境先验证修复效果
3. 定期更新镜像以获取最新的CA证书
4. 如果问题仍然存在，可能需要检查网络环境或防火墙设置