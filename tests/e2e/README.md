# E2E 测试说明

## 概述

本目录包含端到端(E2E)测试用例，用于验证API在实际运行环境中的功能。

## 测试特点

- 使用Docker UAT环境进行测试
- 整个测试套件只启动一次Docker环境
- 每个测试用例独立运行，不共享数据
- 测试结束后自动清理环境

## 运行前准备

1. 确保Docker已安装并运行
2. 确保已构建UAT镜像：
   ```bash
   cd backend
   ./scripts/build-uat.sh
   ```

## 运行测试

### 运行所有E2E测试

```bash
cd backend
pytest tests/e2e/ -v
```

### 运行特定的测试类

```bash
cd backend
pytest tests/e2e/test_count_api.py::TestCountAPI -v
```

### 运行特定的测试方法

```bash
cd backend
pytest tests/e2e/test_count_api.py::TestCountAPI::test_get_count_initial_value -v
```

### 查看详细输出

```bash
cd backend
pytest tests/e2e/ -v -s
```

## 测试内容

当前测试覆盖：

- 计数器API的GET请求
- 计数器API的POST请求（递增和清零）
- 错误处理（无效参数、缺少参数）
- 并发请求处理

## 故障排除

### Docker启动失败

如果看到"Docker不可用"或"启动UAT容器失败"错误：

1. 检查Docker是否正在运行
2. 确认UAT镜像已构建：`docker images | grep safeguard-uat-img`
3. 检查8080端口是否被占用

### 测试超时

如果测试超时：

1. 检查UAT服务是否正常启动
2. 查看容器日志：`docker logs s-uat-e2e-test`

### 清理残留容器

如果测试异常退出，可能需要手动清理：

```bash
docker stop s-uat-e2e-test
docker rm s-uat-e2e-test
```