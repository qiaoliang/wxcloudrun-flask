# 如何运行自动化测试指南

本文档提供了使用 Makefile 运行后端自动化测试的完整指南。

## 目录
- [环境准备](#环境准备)
- [运行测试](#运行测试)
- [测试类型](#测试类型)
- [高级用法](#高级用法)
- [常见问题](#常见问题)

## 环境准备

### 1. 设置测试环境

首次运行测试前，需要设置测试环境：

```bash
make setup
```

这个命令会：
- 检查是否存在虚拟环境 `venv_py312`
- 如果不存在，创建 Python 3.12 虚拟环境
- 安装所需的依赖包

### 2. 手动设置（可选）

如果需要手动设置环境：

```bash
# 创建虚拟环境
python3.12 -m venv venv_py312

# 激活虚拟环境
source venv_py312/bin/activate

# 安装依赖
pip install -r requirements.txt
```

## 运行测试

### 基本命令

```bash
# 查看所有可用命令
make help

# 运行单元测试
make test-unit

# 运行集成测试
make test-integration

# 运行所有测试
make test-all

# 生成测试覆盖率报告
make test-coverage
```

### 详细输出模式

使用 `VERBOSE=1` 参数可以获得更详细的测试输出：

```bash
# 详细输出单元测试
make test-unit VERBOSE=1

# 详细输出集成测试
make test-integration VERBOSE=1
```

## 测试类型

### 1. 单元测试 (Unit Tests)

位置：`tests/unit/`

运行命令：
```bash
make test-unit
```

包含的测试：
- 打卡规则软删除逻辑
- 删除规则核心逻辑
- 监护关系模型

### 2. 集成测试 (Integration Tests)

位置：`tests/integration/`

运行命令：
```bash
make test-integration
```

包含的测试：
- 账户合并功能
- 注册流程
- 统一登录响应格式

### 3. 其他测试

位置：`tests/` 根目录

运行命令：
```bash
make test-all
```

包含的测试：
- 集成测试（根目录）
- 账户合并测试
- 统一登录响应测试

## 高级用法

### 1. 运行特定测试文件

```bash
# 运行注册流程测试
make test-registration

# 运行账户合并测试
make test-account-merge

# 运行登录响应测试
make test-login-response
```

### 2. 运行特定测试类

```bash
make test-class CLASS=TestAccountMerging
```

### 3. 运行特定测试方法

```bash
make test-method METHOD=test_account_merge_functionality
```

### 4. 运行之前失败的测试

```bash
make test-failed
```

### 5. 生成覆盖率报告

```bash
make test-coverage
```

这会生成 HTML 格式的覆盖率报告，保存在 `htmlcov/` 目录中。

### 6. 清理测试文件

```bash
make clean
```

这个命令会清理：
- Python 缓存文件 (`__pycache__`)
- 编译后的 Python 文件 (`.pyc`)
- pytest 缓存 (`.pytest_cache`)
- 覆盖率报告目录 (`htmlcov`)

## 测试编写指南

### 1. 单元测试结构

```python
import pytest
from wxcloudrun import app, db
from wxcloudrun.model import YourModel

class TestYourClass:
    def test_method_name(self, test_db, test_user):
        """测试方法描述"""
        # 准备测试数据
        # 执行测试操作
        # 验证结果
        assert expected_result == actual_result
```

### 2. 集成测试结构

```python
import pytest
from wxcloudrun import app, db

class TestIntegration:
    def test_integration_scenario(self):
        """集成测试场景描述"""
        # 设置测试环境
        # 执行集成测试
        # 验证完整流程
        assert expected_behavior
```

### 3. 测试命名规范

- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试方法：`test_*`

### 4. 测试数据管理

使用 fixtures 管理测试数据：

```python
@pytest.fixture(scope='function')
def test_user(test_db):
    """创建测试用户"""
    user = User(
        wechat_openid="test_openid_123",
        nickname="测试用户",
        role=1
    )
    test_db.session.add(user)
    test_db.session.commit()
    return user
```

## 常见问题

### 1. 虚拟环境问题

**问题**：`bash: venv_py312/bin/activate: No such file or directory`

**解决方案**：
```bash
make setup
```

### 2. 模块导入错误

**问题**：`ModuleNotFoundError: No module named 'wxcloudrun'`

**解决方案**：
确保在 `backend/` 目录下运行命令，Makefile 会自动设置 PYTHONPATH。

### 3. 数据库连接问题

**问题**：数据库连接失败

**解决方案**：
单元测试使用 SQLite 内存数据库，无需额外配置。集成测试可能需要配置数据库连接。

### 4. 测试失败

**问题**：测试失败但不知道具体原因

**解决方案**：
```bash
# 使用详细输出模式
make test-unit VERBOSE=1

# 或者运行特定测试
make test-class CLASS=YourTestClass
```

### 5. 权限问题

**问题**：无法执行 make 命令

**解决方案**：
确保在 `backend/` 目录下，并且有执行权限：
```bash
cd backend
chmod +x Makefile
```

## 最佳实践

1. **提交代码前运行所有测试**：
   ```bash
   make test-all
   ```

2. **定期生成覆盖率报告**：
   ```bash
   make test-coverage
   ```

3. **保持测试环境清洁**：
   ```bash
   make clean
   ```

4. **编写测试时遵循命名规范**，确保测试能被自动发现。

5. **使用描述性的测试名称**，让测试失败时容易理解问题所在。

6. **保持测试独立**，每个测试应该能够独立运行，不依赖其他测试的状态。

## 联系方式

如有问题，请联系开发团队或在项目仓库中提交 issue。