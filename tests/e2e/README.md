# 环境配置 API 端到端测试

这个测试套件验证 SafeGuard 后端项目的环境配置 API 功能。

## 测试内容

该测试包含以下测试用例：

1. **test_env_endpoint_returns_200**: 测试 `/env` 端点返回 200 状态码
2. **test_env_api_endpoint_returns_200**: 测试 `/api/get_envs` API 端点返回 200 状态码并包含有效数据
3. **test_env_api_toml_format**: 测试 `/api/get_envs` 端点支持 TOML 格式输出

## 运行测试

### 方法 1: 使用 make 命令（推荐）

```bash
make e2e-single TEST=tests/e2e/test_env_api.py
```

### 方法 2: 直接使用 pytest

```bash
source venv_py312/bin/activate
python -m pytest tests/e2e/test_env_api.py -v
```

### 方法 3: 运行单个测试

```bash
source venv_py312/bin/activate
python -m pytest tests/e2e/test_env_api.py::TestEnvAPIE2E::test_env_endpoint_returns_200 -v
```

## 测试原理

每个测试方法会：

1. 启动一个独立的 Flask 应用进程（使用端口 9998）
2. 等待应用完全启动
3. 发送 HTTP 请求到相应的端点
4. 验证响应状态码和内容
5. 清理并停止 Flask 应用进程

## e2e 测试用例编写指南

1. 创建一个测试方法，方法名以 `test_` 开头，并使用 `@pytest.mark.e2e` 标记
2. 如果测试方法中需要随机数字，要使用 `testutil.random_str()` 获取随机数字
3. 如果测试方法中需要随机字符串，要使用 `testutil.uuid_str()` 获取随机字符串
4. 测试用例使用的用户名和昵称，请使用与验证相关且有业务含义的固定前缀+随机字符串，以如：`f"supper_admin_${uuid_str(20)}"`
5. 测试方法中，请勿使用全局变量，以免测试之间相互影响
6. 每个测试用例如果需要使用电话号，请使用 `f"192${random_phone(8)}` 或 `f"188${random_phone(8)}"` 获取随机电话号码

## 注意事项

-   测试会自动处理进程清理，避免端口冲突
-   每个测试方法独立运行，确保测试之间不会相互影响
-   测试使用 `ENV_TYPE=func` 环境配置
-   如果测试失败，请检查端口 9998 是否被其他进程占用
