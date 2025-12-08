# 数据库迁移自动化集成测试设计文档

## 概述

本文档描述了为SafeGuard项目的数据库迁移功能设计的自动化集成测试方案。测试专注于SQLite数据库的结构迁移验证，不涉及数据迁移，确保数据库架构变更的正确性和可靠性。

## 测试目标

1. **验证迁移执行**：确保所有迁移脚本能够正确执行
2. **结构完整性**：验证迁移后的数据库结构符合预期
3. **版本追踪**：确保Alembic版本管理正常工作
4. **回滚能力**：验证迁移可以安全回滚

## 测试架构

### 1. 测试文件结构
```
tests/integration/
├── test_database_migration.py    # 主测试文件
├── conftest.py                   # pytest配置（已存在）
└── migration_test_utils.py       # 迁移测试工具类
```

### 2. 核心组件

#### 2.1 MigrationTestHelper工具类
```python
class MigrationTestHelper:
    """数据库迁移测试辅助工具"""
    
    def get_current_version(self) -> str
    def get_table_schema(self, table_name: str) -> dict
    def compare_schemas(self, actual: dict, expected: dict) -> bool
    def verify_table_exists(self, table_name: str) -> bool
    def verify_column_exists(self, table_name: str, column_name: str) -> bool
    def verify_index_exists(self, index_name: str) -> bool
    def execute_migration(self, revision: str) -> bool
    def rollback_migration(self, revision: str) -> bool
```

#### 2.2 测试数据库管理
- 使用临时SQLite数据库文件
- 每个测试前创建新数据库
- 测试后自动清理
- 确保测试隔离

## 测试用例设计

### 第一阶段：完整迁移测试

#### 1.1 test_complete_migration_path
**目的**：验证从空数据库到最新版本的完整迁移流程

**测试步骤**：
1. 创建空的SQLite数据库
2. 执行所有迁移到最新版本
3. 验证最终版本号
4. 检查所有预期的表是否存在
5. 验证表结构（列、类型、约束）
6. 检查索引和外键关系

**预期结果**：
- 版本号为最新
- 所有表存在且结构正确
- 所有约束和索引正确创建

### 第二阶段：单个迁移测试

#### 2.1 test_initial_database_creation
**目的**：验证初始数据库结构迁移（7788862c130d）

**测试步骤**：
1. 创建空数据库
2. 执行初始迁移
3. 验证版本号
4. 检查核心表创建（counters, users, checkin_rules等）
5. 验证表结构

#### 2.2 test_verification_codes_column_addition
**目的**：验证verification_codes表添加is_used列的迁移（c726e805bc85）

**测试步骤**：
1. 准备包含初始结构的数据库
2. 执行列添加迁移
3. 验证新列存在
4. 检查列属性（类型、默认值、约束）

#### 2.3 test_migration_execution
**目的**：验证迁移执行机制

**测试步骤**：
1. 从任意版本开始
2. 执行单个迁移
3. 验证版本更新
4. 检查迁移日志

#### 2.4 test_rollback_capability
**目的**：验证迁移回滚功能

**测试步骤**：
1. 执行迁移到某个版本
2. 记录当前状态
3. 执行回滚到前一版本
4. 验证版本回退
5. 检查结构是否正确回退

#### 2.5 test_version_tracking
**目的**：验证Alembic版本追踪机制

**测试步骤**：
1. 检查alembic_version表
2. 验证版本记录正确性
3. 测试版本查询功能

### 第三阶段：完整性测试

#### 3.1 test_table_relationships
**目的**：验证表之间的关系完整性

**测试步骤**：
1. 检查所有外键约束
2. 验证级联删除规则
3. 测试关系完整性

#### 3.2 test_constraints_and_indexes
**目的**：验证所有约束和索引

**测试步骤**：
1. 列出所有表的索引
2. 验证唯一约束
3. 检查非空约束
4. 测试索引有效性

## 测试报告格式

### 1. 版本追踪报告
```
=== 版本追踪报告 ===
迁移前版本: None
迁移后版本: c726e805bc85
执行时间: 0.023s
状态: 成功
```

### 2. 结构变更报告
```
=== 结构变更报告 ===
表: verification_codes
  新增列:
    - is_used (BOOLEAN, DEFAULT=False)
    - created_at (DATETIME, NOT NULL)
  修改列: 无
  删除列: 无
```

### 3. 错误诊断报告
```
=== 错误诊断 ===
失败迁移: c726e805bc85
错误信息: sqlite3.OperationalError: duplicate column name: is_used
建议: 检查迁移脚本，可能列已存在
```

## 测试配置

### 1. pytest配置
- 使用conftest.py设置测试环境
- 配置临时数据库路径
- 设置测试日志级别

### 2. 环境变量
- ENV_TYPE=test（使用测试配置）
- SQLITE_DB_PATH=:memory:（内存数据库）或临时文件

## 执行方式

### 1. 通过Makefile执行
```bash
# 运行所有迁移测试
make test-migration

# 运行特定测试
make test-class CLASS=TestDatabaseMigration
```

### 2. 直接使用pytest
```bash
# 运行所有迁移测试
python -m pytest tests/integration/test_database_migration.py -v

# 运行特定测试
python -m pytest tests/integration/test_database_migration.py::TestDatabaseMigration::test_complete_migration_path -v
```

## 注意事项

1. **测试隔离**：每个测试使用独立的数据库，避免相互影响
2. **清理机制**：测试后必须清理临时文件
3. **性能考虑**：使用内存数据库提高测试速度
4. **错误处理**：详细记录错误信息，便于调试
5. **版本兼容**：确保测试与Alembic版本兼容

## 后续扩展

1. **性能测试**：添加迁移执行时间基准测试
2. **并发测试**：验证并发迁移的安全性
3. **数据迁移测试**：未来如需数据迁移，可扩展测试
4. **CI/CD集成**：集成到持续集成流程

## 相关文件

- `/backend/src/migrations/env.py` - Alembic环境配置
- `/backend/src/migrations/versions/` - 迁移脚本目录
- `/backend/tests/integration/conftest.py` - pytest配置
- `/backend/Makefile` - 测试执行命令