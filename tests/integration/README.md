# 集成测试使用指南

本目录包含微信与手机注册流程优化项目的集成测试，使用 pytest 框架编写。

## 快速开始

### 方法1：使用脚本（推荐）
```bash
# 运行所有集成测试
./run_integration_tests.sh
```

### 方法2：使用 Makefile
```bash
# 查看所有可用命令
make help

# 运行所有集成测试
make test-integration

# 运行特定测试文件
make test-registration
make test-account-merge
make test-login-response

# 运行所有测试（包括单元测试）
make test-all

# 生成覆盖率报告
make test-coverage
```

### 方法3：直接使用 pytest
```bash
# 激活虚拟环境
source venv_py312/bin/activate

# 设置 PYTHONPATH
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# 运行所有集成测试
python -m pytest tests/integration/ -v

# 运行特定测试文件
python -m pytest tests/integration/test_registration_flow.py -v

# 运行特定测试类
python -m pytest tests/integration/test_account_merging.py::TestAccountMerging -v

# 运行特定测试方法
python -m pytest tests/integration/test_registration_flow.py::TestPhoneRegisterRejectsExistingPhone::test_phone_register_rejects_existing_phone -v
```

## 测试覆盖率

生成测试覆盖率报告：
```bash
make test-coverage
```

报告将生成在 `htmlcov/index.html`

## 调试技巧

### 运行单个测试并查看输出
```bash
# 显示详细输出
make test-integration VERBOSE=1

# 或使用 pytest
python -m pytest tests/integration/test_registration_flow.py -v -s
```

### 只运行失败的测试
```bash
make test-failed
```

### 使用 pdb 调试
```bash
# 在测试失败时进入调试器
python -m pytest tests/integration/test_registration_flow.py --pdb
```

## 环境要求

- Python 3.12
- 虚拟环境 `venv_py312`
- 安装的所有依赖（在 requirements.txt 中）

## 常见问题

### 1. ModuleNotFoundError: No module named 'wxcloudrun'
确保已设置正确的 PYTHONPATH：
```bash
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
```

### 2. 虚拟环境未激活
确保使用虚拟环境中的 Python：
```bash
source venv_py312/bin/activate
```

### 3. 数据库相关错误
测试使用内存数据库，无需额外配置。如遇到问题，尝试清理缓存：
```bash
make clean
```