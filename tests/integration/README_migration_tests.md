# 数据库迁移集成测试指南

本指南说明如何运行和理解数据库迁移集成测试。

## 概述

数据库迁移集成测试验证：
- 迁移脚本的正确执行
- 数据库结构的完整性
- 版本追踪机制
- 回滚能力
- 错误处理

## 快速开始

### 运行所有迁移测试
```bash
# 使用Makefile（推荐）
make test-migration

# 或直接使用pytest
python -m pytest tests/integration/test_database_migration.py -v
```

### 运行特定测试方法
```bash
# 使用Makefile
make test-migration-method METHOD=test_complete_migration_path

# 或使用pytest
python -m pytest tests/integration/test_database_migration.py::TestDatabaseMigration::test_complete_migration_path -v
```

### 详细输出
```bash
make test-migration VERBOSE=1
```

## 测试用例说明

### 1. test_complete_migration_path
**目的**：验证从空数据库到最新版本的完整迁移流程

**验证内容**：
- 初始状态无版本
- 迁移成功执行
- 最终版本正确
- 所有预期表存在

### 2. test_initial_database_creation
**目的**：验证初始数据库结构迁移（7788862c130d）

**验证内容**：
- Counters表结构
- users表结构
- 基础表创建

### 3. test_verification_codes_column_addition
**目的**：验证verification_codes表添加is_used列的迁移（c726e805bc85）

**验证内容**：
- 列存在性
- 列类型（BOOLEAN）
- 默认值（0）

### 4. test_migration_execution
**目的**：验证迁移执行机制

**验证内容**：
- 版本正确更新
- 多步迁移执行

### 5. test_rollback_capability
**目的**：验证迁移回滚功能

**验证内容**：
- 成功回滚到指定版本
- 结构正确回退
- 重新迁移能力

### 6. test_version_tracking
**目的**：验证Alembic版本追踪机制

**验证内容**：
- alembic_version表存在
- version_num列属性
- 版本记录正确性

### 7. test_table_relationships
**目的**：验证表之间的关系完整性

**验证内容**：
- 外键约束
- 引用完整性

### 8. test_constraints_and_indexes
**目的**：验证所有约束和索引

**验证内容**：
- 主键约束
- 索引存在性

### 9. test_migration_error_handling
**目的**：测试迁移错误处理

**验证内容**：
- 无效版本处理
- 状态不变性

### 10. test_invalid_table_name_handling
**目的**：测试无效表名的处理

**验证内容**：
- SQL注入防护
- 输入验证

### 11. test_temporary_database_cleanup
**目的**：测试临时数据库清理

**验证内容**：
- 资源自动清理
- 无残留文件

## 测试报告

测试执行后会生成详细报告，包括：

### 版本追踪报告
```
=== 版本追踪报告 ===
测试: test_complete_migration_path
状态: 成功
时间: 2024-12-08T10:30:45
详情:
  initial_version: None
  final_version: c726e805bc85
  tables_count: 8
```

### 结构变更报告
```
=== 结构变更报告 ===
测试: test_verification_codes_column_addition
状态: 成功
时间: 2024-12-08T10:31:02
详情:
  version: c726e805bc85
  column_added: is_used
  column_type: BOOLEAN
  default_value: 0
```

### 错误诊断报告
```
=== 错误诊断 ===
测试: test_migration_error_handling
状态: 成功
时间: 2024-12-08T10:31:20
详情:
  invalid_version: nonexistent_version
  migration_failed: True
  version_unchanged: True
```

## 故障排除

### 常见问题

#### 1. ModuleNotFoundError: No module named 'wxcloudrun'
**解决方案**：
```bash
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"
```

#### 2. 数据库连接错误
**可能原因**：
- 临时文件权限问题
- SQLite版本不兼容

**解决方案**：
```bash
make clean
make test-migration
```

#### 3. 迁移版本不匹配
**可能原因**：
- 迁移文件更新
- 测试数据过时

**解决方案**：
```bash
# 重新生成测试数据库
rm -rf tests/temp_*.db
make test-migration
```

### 调试技巧

#### 1. 查看详细日志
```bash
make test-migration VERBOSE=1
```

#### 2. 运行单个测试
```bash
make test-migration-method METHOD=test_complete_migration_path
```

#### 3. 使用pdb调试
```bash
python -m pytest tests/integration/test_database_migration.py::TestDatabaseMigration::test_complete_migration_path --pdb
```

## 最佳实践

### 1. 测试隔离
- 每个测试使用独立的临时数据库
- 测试后自动清理资源
- 避免测试间状态共享

### 2. 性能考虑
- 使用内存数据库提高速度
- 避免不必要的重复迁移
- 监控测试执行时间

### 3. 维护建议
- 定期更新期望的表结构
- 添加新迁移的测试用例
- 保持测试文档同步

## 扩展测试

### 添加新的测试用例

1. 在`test_database_migration.py`中添加测试方法
2. 使用`@pytest.mark.migration`标记
3. 遵循命名约定`test_<功能>`

示例：
```python
@pytest.mark.migration
def test_new_migration_feature(self):
    """测试新的迁移功能"""
    with self.helper.temp_database() as db_path:
        # 测试逻辑
        pass
```

### 添加性能测试

```python
def test_migration_performance(self):
    """测试迁移性能"""
    with self.helper.temp_database() as db_path:
        start_time = time.time()
        assert self.helper.execute_migration()
        execution_time = time.time() - start_time
        
        assert execution_time < 30.0, f"迁移耗时过长: {execution_time}秒"
```

## 相关文件

- `/tests/integration/test_database_migration.py` - 主测试文件
- `/tests/integration/migration_test_utils.py` - 测试工具类
- `/tests/integration/conftest.py` - pytest配置
- `/src/migrations/versions/` - 迁移脚本目录