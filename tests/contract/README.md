# API 契约测试

## 概述

这个目录包含 API 契约测试，用于验证前端实际调用的 API 返回符合前端期望的数据结构。

## 设计理念

- **基于实际使用**：直接从 `frontend/src/api/` 目录中提取前端实际调用的 API
- **双向验证**：同时验证 API 调用成功和响应数据结构
- **自动化**：自动扫描前端代码，无需手动维护 API 列表

## 测试覆盖

### 1. API 调用成功验证
- 验证前端调用的所有 API 都能成功返回
- 检查 HTTP 状态码

### 2. 响应结构验证
- 验证 API 响应包含前端使用的所有字段
- 检查字段命名和类型

### 3. 数据类型验证
- 验证关键字段的数据类型正确
- 例如：`community_id` 应该是整数，`name` 应该是字符串

### 4. 空数据验证
- 识别返回空数据的 API
- 区分正常空数据和非预期空数据

## 运行测试

### 运行所有契约测试

```bash
cd backend
make it-s TEST=tests/contract/test_api_contract.py
```

### 运行单个测试

```bash
cd backend
pytest tests/contract/test_api_contract.py::TestAPIContract::test_frontend_api_calls_succeed -v
```

### 查看测试报告

```bash
cd backend
pytest tests/contract/test_api_contract.py::TestAPIContract::test_frontend_api_coverage -v -s
```

## 测试数据

契约测试使用以下测试数据：

- **超级管理员**：`13141516171` / `F1234567`
- **普通用户**：自动生成随机用户

## 维护指南

### 添加新的 API 测试

1. 在 `frontend/src/api/` 中添加新的 API 调用
2. 契约测试会自动发现并测试新的 API
3. 如果 API 返回的数据结构与前端使用不匹配，测试会失败

### 修复失败的测试

1. 查看测试输出，了解哪个 API 失败
2. 检查前端代码中使用的字段
3. 确保后端 API 返回相应的字段
4. 重新运行测试验证修复

## CI/CD 集成

建议在 CI/CD 流程中包含契约测试：

```yaml
# .github/workflows/contract-tests.yml
name: API Contract Tests

on: [pull_request]

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-test.txt
      - name: Run contract tests
        run: |
          cd backend
          make it-s TEST=tests/contract/test_api_contract.py
```

## 已知限制

1. **GET 方法优先**：当前实现主要测试 GET 请求，POST/PUT/DELETE 需要额外配置
2. **字段提取**：通过正则表达式提取字段，可能无法覆盖所有使用场景
3. **动态字段**：某些 API 可能返回动态字段，需要手动验证

## 未来改进

- [ ] 支持所有 HTTP 方法（POST/PUT/DELETE）
- [ ] 更精确的字段提取（使用 AST）
- [ ] 生成 API 使用报告
- [ ] 集成到前端构建流程