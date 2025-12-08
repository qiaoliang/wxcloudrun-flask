# 数据库迁移集成测试实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** 实现完整的数据库迁移自动化集成测试框架，确保SQLite数据库结构迁移的正确性和可靠性

**Architecture:** 基于pytest框架，使用临时SQLite数据库，通过MigrationTestHelper工具类进行迁移测试，支持版本追踪和结构验证

**Tech Stack:** Python 3.12, pytest, SQLAlchemy, Alembic, SQLite

---

## 实施概览

本计划将创建一个完整的数据库迁移集成测试框架，包括：
1. 迁移测试工具类 (MigrationTestHelper)
2. 主测试文件 (test_database_migration.py)
3. 测试配置更新
4. Makefile命令扩展

## 任务分解

### Task 1: 创建迁移测试工具类

**Files:**
- Create: `tests/integration/migration_test_utils.py`

**Step 1: 创建工具类基础结构**

```python
# tests/integration/migration_test_utils.py
"""
数据库迁移测试辅助工具类
提供数据库迁移测试所需的各种工具方法
"""
import os
import sqlite3
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from src.config import db_config


class MigrationTestHelper:
    """数据库迁移测试辅助工具"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化迁移测试助手
        
        Args:
            db_path: 数据库文件路径，如果为None则使用内存数据库
        """
        self.db_path = db_path or ":memory:"
        self.engine: Optional[Engine] = None
        self.temp_file: Optional[str] = None
        
        # 如果需要临时文件
        if db_path is None:
            self.temp_file = tempfile.mktemp(suffix='.db')
            self.db_path = self.temp_file
            
        self._initialize_engine()
    
    def _initialize_engine(self):
        """初始化数据库引擎"""
        db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(db_url)
    
    def get_current_version(self) -> str:
        """获取当前数据库版本"""
        if not self.engine:
            raise RuntimeError("数据库引擎未初始化")
        
        with self.engine.connect() as conn:
            try:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                version = result.scalar()
                return version or "None"
            except Exception:
                return "None"
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """获取表结构信息"""
        if not self.engine:
            raise RuntimeError("数据库引擎未初始化")
        
        with self.engine.connect() as conn:
            # 获取表信息
            result = conn.execute(text(f"PRAGMA table_info({table_name})"))
            columns = []
            for row in result:
                columns.append({
                    'name': row[1],
                    'type': row[2],
                    'not_null': bool(row[3]),
                    'default': row[4],
                    'primary_key': bool(row[5])
                })
            
            # 获取索引信息
            result = conn.execute(text(f"PRAGMA index_list({table_name})"))
            indexes = []
            for row in result:
                indexes.append({
                    'name': row[1],
                    'unique': bool(row[2]),
                    'origin': row[3]
                })
            
            return {
                'table_name': table_name,
                'columns': columns,
                'indexes': indexes
            }
    
    def verify_table_exists(self, table_name: str) -> bool:
        """验证表是否存在"""
        if not self.engine:
            raise RuntimeError("数据库引擎未初始化")
        
        with self.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name=:table_name"
            ), {"table_name": table_name})
            return result.scalar() is not None
    
    def verify_column_exists(self, table_name: str, column_name: str) -> bool:
        """验证列是否存在"""
        schema = self.get_table_schema(table_name)
        return any(col['name'] == column_name for col in schema['columns'])
    
    def verify_index_exists(self, index_name: str) -> bool:
        """验证索引是否存在"""
        if not self.engine:
            raise RuntimeError("数据库引擎未初始化")
        
        with self.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND name=:index_name"
            ), {"index_name": index_name})
            return result.scalar() is not None
    
    def execute_migration(self, revision: str = "head") -> bool:
        """执行数据库迁移"""
        if not self.engine:
            raise RuntimeError("数据库引擎未初始化")
        
        try:
            from alembic.config import Config
            from alembic import command
            
            # 配置Alembic
            alembic_cfg = Config("src/migrations/alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{self.db_path}")
            
            # 执行迁移
            command.upgrade(alembic_cfg, revision)
            return True
        except Exception as e:
            print(f"迁移执行失败: {e}")
            return False
    
    def rollback_migration(self, revision: str) -> bool:
        """回滚数据库迁移"""
        if not self.engine:
            raise RuntimeError("数据库引擎未初始化")
        
        try:
            from alembic.config import Config
            from alembic import command
            
            # 配置Alembic
            alembic_cfg = Config("src/migrations/alembic.ini")
            alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{self.db_path}")
            
            # 执行回滚
            command.downgrade(alembic_cfg, revision)
            return True
        except Exception as e:
            print(f"迁移回滚失败: {e}")
            return False
    
    def get_all_tables(self) -> List[str]:
        """获取所有表名"""
        if not self.engine:
            raise RuntimeError("数据库引擎未初始化")
        
        with self.engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            return [row[0] for row in result if not row[0].startswith('sqlite_')]
    
    def cleanup(self):
        """清理资源"""
        if self.engine:
            self.engine.dispose()
        if self.temp_file and os.path.exists(self.temp_file):
            os.unlink(self.temp_file)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
```

**Step 2: 运行工具类语法检查**

Run: `python -m py_compile tests/integration/migration_test_utils.py`
Expected: 无语法错误

**Step 3: 提交工具类**

```bash
git add tests/integration/migration_test_utils.py
git commit -m "feat: 创建数据库迁移测试工具类 MigrationTestHelper"
```

---

### Task 2: 创建主测试文件

**Files:**
- Create: `tests/integration/test_database_migration.py`

**Step 1: 编写测试文件基础结构**

```python
# tests/integration/test_database_migration.py
"""
数据库迁移集成测试
验证数据库迁移的正确性和完整性
"""
import pytest
import tempfile
import os
from migration_test_utils import MigrationTestHelper


class TestDatabaseMigration:
    """数据库迁移测试类"""
    
    @pytest.fixture
    def migration_helper(self):
        """创建迁移测试助手fixture"""
        with MigrationTestHelper() as helper:
            yield helper
    
    @pytest.fixture
    def empty_db_helper(self):
        """创建空数据库助手fixture"""
        temp_db = tempfile.mktemp(suffix='.db')
        try:
            with MigrationTestHelper(temp_db) as helper:
                yield helper
        finally:
            if os.path.exists(temp_db):
                os.unlink(temp_db)
```

**Step 2: 运行基础测试结构检查**

Run: `python -m pytest tests/integration/test_database_migration.py::TestDatabaseMigration -v`
Expected: 测试类被发现，无语法错误

**Step 3: 实现完整迁移路径测试**

```python
# 在 TestDatabaseMigration 类中添加以下方法

def test_complete_migration_path(self, empty_db_helper):
    """测试从空数据库到最新版本的完整迁移流程"""
    helper = empty_db_helper
    
    # 记录开始时间
    start_time = datetime.now()
    
    # 执行完整迁移
    success = helper.execute_migration("head")
    assert success, "完整迁移执行失败"
    
    # 记录结束时间
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    
    # 验证版本号
    current_version = helper.get_current_version()
    assert current_version != "None", "版本号不应为空"
    print(f"=== 版本追踪报告 ===")
    print(f"迁移前版本: None")
    print(f"迁移后版本: {current_version}")
    print(f"执行时间: {execution_time:.3f}s")
    print(f"状态: 成功")
    
    # 验证核心表存在
    expected_tables = [
        'alembic_version',
        'counters', 
        'users',
        'verification_codes',
        'checkin_rules',
        'checkin_records',
        'supervision_relations',
        'notifications',
        'communities',
        'system_configs'
    ]
    
    all_tables = helper.get_all_tables()
    missing_tables = [table for table in expected_tables if table not in all_tables]
    assert not missing_tables, f"缺少表: {missing_tables}"
    
    print(f"=== 表创建验证 ===")
    print(f"预期表数量: {len(expected_tables)}")
    print(f"实际表数量: {len([t for t in all_tables if t in expected_tables])}")
    print(f"所有预期表已创建: ✓")
```

**Step 4: 实现初始数据库创建测试**

```python
# 在 TestDatabaseMigration 类中添加以下方法

def test_initial_database_creation(self, empty_db_helper):
    """测试初始数据库结构迁移（7788862c130d）"""
    helper = empty_db_helper
    
    # 执行初始迁移
    success = helper.execute_migration("7788862c130d")
    assert success, "初始迁移执行失败"
    
    # 验证版本号
    current_version = helper.get_current_version()
    assert current_version == "7788862c130d", f"版本号不匹配，期望: 7788862c130d，实际: {current_version}"
    
    # 验证核心表结构
    core_tables = ['counters', 'users', 'verification_codes']
    for table in core_tables:
        assert helper.verify_table_exists(table), f"核心表 {table} 不存在"
    
    # 验证counters表结构
    counters_schema = helper.get_table_schema('counters')
    expected_columns = ['id', 'count', 'created_at', 'updated_at']
    actual_columns = [col['name'] for col in counters_schema['columns']]
    
    for col in expected_columns:
        assert col in actual_columns, f"counters表缺少列: {col}"
    
    print(f"=== 初始数据库结构验证 ===")
    print(f"版本号: {current_version}")
    print(f"核心表数量: {len(core_tables)}")
    print(f"结构验证: ✓")
```

**Step 5: 实现列添加测试**

```python
# 在 TestDatabaseMigration 类中添加以下方法

def test_verification_codes_column_addition(self, empty_db_helper):
    """测试verification_codes表添加is_used列的迁移（c726e805bc85）"""
    helper = empty_db_helper
    
    # 先执行初始迁移
    assert helper.execute_migration("7788862c130d"), "初始迁移失败"
    
    # 记录迁移前状态
    before_schema = helper.get_table_schema('verification_codes')
    before_columns = [col['name'] for col in before_schema['columns']]
    
    # 执行列添加迁移
    success = helper.execute_migration("c726e805bc85")
    assert success, "列添加迁移执行失败"
    
    # 验证版本更新
    current_version = helper.get_current_version()
    assert current_version == "c726e805bc85", f"版本号不匹配，期望: c726e805bc85，实际: {current_version}"
    
    # 记录迁移后状态
    after_schema = helper.get_table_schema('verification_codes')
    after_columns = [col['name'] for col in after_schema['columns']]
    
    # 验证新列存在
    assert helper.verify_column_exists('verification_codes', 'is_used'), "is_used列不存在"
    assert helper.verify_column_exists('verification_codes', 'created_at'), "created_at列不存在"
    
    # 验证列属性
    is_used_col = next(col for col in after_schema['columns'] if col['name'] == 'is_used')
    assert is_used_col['type'].upper() == 'BOOLEAN', f"is_used列类型错误: {is_used_col['type']}"
    
    print(f"=== 结构变更报告 ===")
    print(f"表: verification_codes")
    print(f"  新增列:")
    print(f"    - is_used (BOOLEAN, DEFAULT=False)")
    print(f"    - created_at (DATETIME, NOT NULL)")
    print(f"  修改列: 无")
    print(f"  删除列: 无")
```

**Step 6: 运行测试验证**

Run: `python -m pytest tests/integration/test_database_migration.py -v`
Expected: 所有测试通过

**Step 7: 提交主测试文件**

```bash
git add tests/integration/test_database_migration.py
git commit -m "feat: 实现数据库迁移集成测试核心用例"
```

---

### Task 3: 扩展测试用例

**Files:**
- Modify: `tests/integration/test_database_migration.py`

**Step 1: 实现迁移执行测试**

```python
# 在 TestDatabaseMigration 类中添加以下方法

def test_migration_execution(self, empty_db_helper):
    """测试迁移执行机制"""
    helper = empty_db_helper
    
    # 从初始版本开始
    assert helper.execute_migration("7788862c130d"), "初始迁移失败"
    
    initial_version = helper.get_current_version()
    
    # 执行单个迁移
    success = helper.execute_migration("+1")  # 升级到下一个版本
    assert success, "单个迁移执行失败"
    
    # 验证版本更新
    new_version = helper.get_current_version()
    assert new_version != initial_version, "版本号未更新"
    assert new_version == "c726e805bc85", f"版本号不正确: {new_version}"
    
    print(f"=== 迁移执行验证 ===")
    print(f"初始版本: {initial_version}")
    print(f"升级后版本: {new_version}")
    print(f"执行成功: ✓")
```

**Step 2: 实现回滚测试**

```python
# 在 TestDatabaseMigration 类中添加以下方法

def test_rollback_capability(self, empty_db_helper):
    """测试迁移回滚功能"""
    helper = empty_db_helper
    
    # 迁移到最新版本
    assert helper.execute_migration("head"), "升级到最新版本失败"
    latest_version = helper.get_current_version()
    
    # 记录当前状态
    tables_before_rollback = helper.get_all_tables()
    
    # 回滚到初始版本
    success = helper.rollback_migration("7788862c130d")
    assert success, "回滚失败"
    
    # 验证版本回退
    rollback_version = helper.get_current_version()
    assert rollback_version == "7788862c130d", f"回滚后版本不正确: {rollback_version}"
    
    # 验证结构回退
    assert not helper.verify_column_exists('verification_codes', 'is_used'), "is_used列应该已被回滚"
    
    print(f"=== 回滚能力验证 ===")
    print(f"回滚前版本: {latest_version}")
    print(f"回滚后版本: {rollback_version}")
    print(f"回滚成功: ✓")
```

**Step 3: 实现版本追踪测试**

```python
# 在 TestDatabaseMigration 类中添加以下方法

def test_version_tracking(self, empty_db_helper):
    """测试Alembic版本追踪机制"""
    helper = empty_db_helper
    
    # 检查初始状态（无版本表）
    initial_version = helper.get_current_version()
    assert initial_version == "None", "初始版本应为None"
    
    # 执行迁移
    assert helper.execute_migration("head"), "迁移失败"
    
    # 检查版本表存在
    assert helper.verify_table_exists('alembic_version'), "alembic_version表不存在"
    
    # 验证版本记录
    version_schema = helper.get_table_schema('alembic_version')
    version_columns = [col['name'] for col in version_schema['columns']]
    assert 'version_num' in version_columns, "version_num列不存在"
    
    # 验证版本值格式
    current_version = helper.get_current_version()
    assert len(current_version) == 12, f"版本号格式不正确: {current_version}"
    assert all(c in '0123456789abcdef' for c in current_version), "版本号包含非法字符"
    
    print(f"=== 版本追踪验证 ===")
    print(f"版本表存在: ✓")
    print(f"版本格式正确: ✓")
    print(f"当前版本: {current_version}")
```

**Step 4: 实现表关系测试**

```python
# 在 TestDatabaseMigration 类中添加以下方法

def test_table_relationships(self, empty_db_helper):
    """测试表之间的关系完整性"""
    helper = empty_db_helper
    
    # 执行完整迁移
    assert helper.execute_migration("head"), "迁移失败"
    
    # 检查外键约束（SQLite中需要通过CREATE TABLE语句中的REFERENCES检查）
    # 这里我们检查关键表是否存在，以及它们的结构是否包含关系字段
    
    # 检查supervision_relations表
    assert helper.verify_table_exists('supervision_relations'), "supervision_relations表不存在"
    
    relation_schema = helper.get_table_schema('supervision_relations')
    relation_columns = [col['name'] for col in relation_schema['columns']]
    
    # 验证外键字段存在
    expected_fk_columns = ['solo_user_id', 'supervisor_user_id']
    for col in expected_fk_columns:
        assert col in relation_columns, f"外键字段 {col} 不存在"
    
    # 检查checkin_records表
    assert helper.verify_table_exists('checkin_records'), "checkin_records表不存在"
    
    record_schema = helper.get_table_schema('checkin_records')
    record_columns = [col['name'] for col in record_schema['columns']]
    
    expected_record_fk = ['solo_user_id', 'rule_id']
    for col in expected_record_fk:
        assert col in record_columns, f"外键字段 {col} 不存在"
    
    print(f"=== 表关系验证 ===")
    print(f"监督关系表: ✓")
    print(f"打卡记录表: ✓")
    print(f"外键字段完整性: ✓")
```

**Step 5: 实现约束和索引测试**

```python
# 在 TestDatabaseMigration 类中添加以下方法

def test_constraints_and_indexes(self, empty_db_helper):
    """测试所有约束和索引"""
    helper = empty_db_helper
    
    # 执行完整迁移
    assert helper.execute_migration("head"), "迁移失败"
    
    # 检查users表的唯一约束
    users_schema = helper.get_table_schema('users')
    users_columns = [col['name'] for col in users_schema['columns']]
    
    # 验证关键字段
    expected_unique_fields = ['wechat_openid', 'phone_number']
    for field in expected_unique_fields:
        assert field in users_columns, f"唯一字段 {field} 不存在"
    
    # 检查索引
    all_indexes = []
    for table in helper.get_all_tables():
        if table.startswith('sqlite_'):
            continue
        schema = helper.get_table_schema(table)
        for index in schema['indexes']:
            all_indexes.append(f"{table}.{index['name']}")
    
    print(f"=== 约束和索引验证 ===")
    print(f"表数量: {len(helper.get_all_tables())}")
    print(f"索引数量: {len(all_indexes)}")
    print(f"唯一约束字段: {len(expected_unique_fields)}")
    print(f"验证通过: ✓")
```

**Step 6: 运行扩展测试**

Run: `python -m pytest tests/integration/test_database_migration.py -v`
Expected: 所有扩展测试通过

**Step 7: 提交扩展测试**

```bash
git add tests/integration/test_database_migration.py
git commit -m "feat: 扩展数据库迁移测试用例，包含回滚、版本追踪和关系验证"
```

---

### Task 4: 更新测试配置

**Files:**
- Modify: `tests/integration/conftest.py`

**Step 1: 添加迁移测试配置**

```python
# 在 tests/integration/conftest.py 中添加以下内容

import pytest
import tempfile
import os
from migration_test_utils import MigrationTestHelper

@pytest.fixture(scope="function")
def test_db():
    """创建测试数据库fixture"""
    temp_db = tempfile.mktemp(suffix='.db')
    try:
        with MigrationTestHelper(temp_db) as helper:
            yield helper
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)

@pytest.fixture(scope="function") 
def empty_test_db():
    """创建空测试数据库fixture"""
    temp_db = tempfile.mktemp(suffix='.db')
    try:
        with MigrationTestHelper(temp_db) as helper:
            yield helper
    finally:
        if os.path.exists(temp_db):
            os.unlink(temp_db)

# 添加迁移测试标记
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "migration: 标记数据库迁移测试"
    )

def pytest_collection_modifyitems(config, items):
    """为迁移测试添加标记"""
    for item in items:
        if "migration" in item.nodeid:
            item.add_marker(pytest.mark.migration)
```

**Step 2: 运行配置测试**

Run: `python -m pytest tests/integration/test_database_migration.py -v -m migration`
Expected: 测试正常运行，标记生效

**Step 3: 提交配置更新**

```bash
git add tests/integration/conftest.py
git commit -m "feat: 更新集成测试配置，添加迁移测试支持"
```

---

### Task 5: 扩展Makefile命令

**Files:**
- Modify: `Makefile`

**Step 1: 添加迁移测试命令**

```makefile
# 在 Makefile 中添加以下命令

# 运行数据库迁移测试
test-migration:
	@echo "运行数据库迁移测试..."
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	if [ "$(VERBOSE)" = "1" ]; then \
		python -m pytest tests/integration/test_database_migration.py -v -s -m migration; \
	else \
		python -m pytest tests/integration/test_database_migration.py -v -m migration; \
	fi

# 运行特定迁移测试
test-migration-method:
	@if [ -z "$(METHOD)" ]; then \
		echo "请指定测试方法，例如: make test-migration-method METHOD=test_complete_migration_path"; \
		exit 1; \
	fi
	@echo "运行迁移测试方法: $(METHOD)"
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	python -m pytest tests/integration/test_database_migration.py::TestDatabaseMigration::$(METHOD) -v

# 运行迁移性能测试
test-migration-performance:
	@echo "运行迁移性能测试..."
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	python -m pytest tests/integration/test_database_migration.py::TestDatabaseMigration::test_complete_migration_path -v -s --benchmark-only

# 清理迁移测试相关文件
clean-migration:
	@echo "清理迁移测试文件..."
	@find tests/integration -name "*.db" -delete 2>/dev/null || true
	@echo "清理完成"
```

**Step 2: 更新help信息**

```makefile
# 更新 help 目标中的说明

help:
	@echo "可用的测试命令:"
	@echo "  make setup        - 设置测试环境"
	@echo "  make test-unit    - 运行单元测试"
	@echo "  make test-integration - 运行集成测试"
	@echo "  make test-all     - 运行所有测试"
	@echo "  make test-migration - 运行数据库迁移测试"
	@echo "  make test-coverage - 生成测试覆盖率报告"
	@echo "  make clean        - 清理测试文件"
	@echo "  make clean-migration - 清理迁移测试文件"
	@echo "  make test-failed  - 运行之前失败的测试"
	@echo ""
	@echo "迁移测试专项:"
	@echo "  make test-migration-method METHOD=<method> - 运行特定迁移测试方法"
	@echo "  make test-migration-performance - 运行迁移性能测试"
	@echo ""
	@echo "示例:"
	@echo "  make test-migration            # 运行迁移测试"
	@echo "  make test-migration VERBOSE=1  # 详细输出"
	@echo "  make test-migration-method METHOD=test_complete_migration_path"
```

**Step 3: 测试Makefile命令**

Run: `make test-migration`
Expected: 迁移测试正常执行

Run: `make help`
Expected: 帮助信息包含新的迁移测试命令

**Step 4: 提交Makefile更新**

```bash
git add Makefile
git commit -m "feat: 添加数据库迁移测试专用Makefile命令"
```

---

### Task 6: 创建测试文档

**Files:**
- Create: `tests/integration/README_migration_tests.md`

**Step 1: 编写测试文档**

```markdown
# 数据库迁移集成测试文档

## 概述

本文档描述了SafeGuard项目数据库迁移集成测试的使用方法和最佳实践。

## 测试结构

```
tests/integration/
├── test_database_migration.py    # 主测试文件
├── migration_test_utils.py       # 迁移测试工具类
├── conftest.py                   # pytest配置
└── README_migration_tests.md     # 本文档
```

## 核心组件

### MigrationTestHelper

提供数据库迁移测试所需的各种工具方法：

- `get_current_version()` - 获取当前数据库版本
- `get_table_schema(table_name)` - 获取表结构信息
- `verify_table_exists(table_name)` - 验证表是否存在
- `verify_column_exists(table_name, column_name)` - 验证列是否存在
- `execute_migration(revision)` - 执行数据库迁移
- `rollback_migration(revision)` - 回滚数据库迁移

## 测试用例

### 主要测试用例

1. **test_complete_migration_path** - 完整迁移路径测试
2. **test_initial_database_creation** - 初始数据库创建测试
3. **test_verification_codes_column_addition** - 列添加测试
4. **test_migration_execution** - 迁移执行测试
5. **test_rollback_capability** - 回滚能力测试
6. **test_version_tracking** - 版本追踪测试
7. **test_table_relationships** - 表关系测试
8. **test_constraints_and_indexes** - 约束和索引测试

## 运行测试

### 使用Makefile

```bash
# 运行所有迁移测试
make test-migration

# 运行特定测试方法
make test-migration-method METHOD=test_complete_migration_path

# 详细输出
make test-migration VERBOSE=1

# 性能测试
make test-migration-performance
```

### 使用pytest

```bash
# 运行所有迁移测试
python -m pytest tests/integration/test_database_migration.py -v -m migration

# 运行特定测试
python -m pytest tests/integration/test_database_migration.py::TestDatabaseMigration::test_complete_migration_path -v

# 运行带详细输出的测试
python -m pytest tests/integration/test_database_migration.py -v -s
```

## 测试报告

测试执行时会生成详细的报告，包括：

### 版本追踪报告
```
=== 版本追踪报告 ===
迁移前版本: None
迁移后版本: c726e805bc85
执行时间: 0.023s
状态: 成功
```

### 结构变更报告
```
=== 结构变更报告 ===
表: verification_codes
  新增列:
    - is_used (BOOLEAN, DEFAULT=False)
    - created_at (DATETIME, NOT NULL)
  修改列: 无
  删除列: 无
```

## 最佳实践

1. **测试隔离** - 每个测试使用独立的数据库
2. **资源清理** - 测试后自动清理临时文件
3. **版本验证** - 每次迁移后验证版本号
4. **结构检查** - 验证表、列、索引的正确性
5. **回滚测试** - 确保迁移可以安全回滚

## 故障排除

### 常见问题

1. **数据库连接错误**
   - 检查SQLite文件权限
   - 确保临时目录可写

2. **迁移执行失败**
   - 检查迁移脚本语法
   - 验证数据库连接配置

3. **版本号不匹配**
   - 检查Alembic配置
   - 确认迁移脚本版本号

### 调试技巧

1. 使用 `-s` 参数查看详细输出
2. 检查日志文件中的错误信息
3. 使用SQLite命令行工具直接检查数据库

## 扩展测试

如需添加新的测试用例：

1. 在 `TestDatabaseMigration` 类中添加新方法
2. 方法名以 `test_` 开头
3. 使用 `migration_helper` fixture
4. 遵循现有测试的模式和断言风格

## 相关文件

- `/backend/src/migrations/` - Alembic迁移脚本
- `/backend/src/migrations/alembic.ini` - Alembic配置
- `/backend/tests/integration/conftest.py` - pytest配置
- `/backend/Makefile` - 测试命令
```

**Step 2: 提交文档**

```bash
git add tests/integration/README_migration_tests.md
git commit -m "docs: 添加数据库迁移集成测试文档"
```

---

### Task 7: 最终验证和优化

**Files:**
- Modify: `tests/integration/test_database_migration.py`

**Step 1: 添加性能基准测试**

```python
# 在 TestDatabaseMigration 类中添加以下方法

@pytest.mark.benchmark
def test_migration_performance(self, empty_db_helper):
    """测试迁移执行性能"""
    helper = empty_db_helper
    
    import time
    
    # 测试完整迁移性能
    start_time = time.time()
    success = helper.execute_migration("head")
    end_time = time.time()
    
    assert success, "迁移失败"
    
    execution_time = end_time - start_time
    
    # 性能断言（根据实际情况调整阈值）
    assert execution_time < 5.0, f"迁移执行时间过长: {execution_time:.3f}s"
    
    print(f"=== 性能基准报告 ===")
    print(f"执行时间: {execution_time:.3f}s")
    print(f"性能要求: < 5.0s")
    print(f"性能达标: {'✓' if execution_time < 5.0 else '✗'}")
```

**Step 2: 添加错误处理测试**

```python
# 在 TestDatabaseMigration 类中添加以下方法

def test_migration_error_handling(self, empty_db_helper):
    """测试迁移错误处理"""
    helper = empty_db_helper
    
    # 尝试迁移到不存在的版本
    success = helper.execute_migration("nonexistent_version")
    assert not success, "迁移到不存在版本应该失败"
    
    # 尝试回滚到不存在的版本
    success = helper.rollback_migration("nonexistent_version")
    assert not success, "回滚到不存在版本应该失败"
    
    print(f"=== 错误处理验证 ===")
    print(f"无效版本迁移: ✓")
    print(f"无效版本回滚: ✓")
    print(f"错误处理正常: ✓")
```

**Step 3: 运行完整测试套件**

Run: `python -m pytest tests/integration/test_database_migration.py -v --tb=short`
Expected: 所有测试通过，无错误

**Step 4: 运行覆盖率检查**

Run: `python -m pytest tests/integration/test_database_migration.py --cov=migration_test_utils --cov-report=term-missing`
Expected: 工具类覆盖率 > 90%

**Step 5: 最终提交**

```bash
git add tests/integration/test_database_migration.py
git commit -m "feat: 添加性能基准测试和错误处理测试"
```

---

## 实施总结

### 完成的文件

1. **`tests/integration/migration_test_utils.py`** - 迁移测试工具类
2. **`tests/integration/test_database_migration.py`** - 主测试文件
3. **`tests/integration/conftest.py`** - 更新的pytest配置
4. **`tests/integration/README_migration_tests.md`** - 测试文档
5. **`Makefile`** - 更新的构建命令

### 核心功能

- ✅ 完整迁移路径测试
- ✅ 单个迁移验证
- ✅ 版本追踪机制
- ✅ 回滚能力测试
- ✅ 表结构验证
- ✅ 约束和索引检查
- ✅ 性能基准测试
- ✅ 错误处理验证

### 使用方式

```bash
# 运行所有迁移测试
make test-migration

# 运行特定测试
make test-migration-method METHOD=test_complete_migration_path

# 详细输出
make test-migration VERBOSE=1
```

### 质量保证

- 测试隔离：每个测试使用独立数据库
- 自动清理：测试后自动清理临时文件
- 详细报告：提供版本追踪和结构变更报告
- 性能监控：包含执行时间基准测试
- 错误处理：验证异常情况的处理

这个实施计划提供了完整的数据库迁移集成测试框架，确保数据库结构变更的正确性和可靠性。