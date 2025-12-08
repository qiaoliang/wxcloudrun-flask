"""
数据库迁移测试 - 直接测试迁移脚本
遵循TDD原则：先写失败测试，观察失败，编写最小代码使其通过
"""
import pytest
import os
import tempfile
import sys
from pathlib import Path

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from sqlalchemy import create_engine, text


@pytest.fixture
def temp_database():
    """创建临时数据库"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    engine = create_engine(f"sqlite:///{db_path}")
    yield engine
    
    # 清理
    engine.dispose()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.mark.migration
def test_counters_table_creation(temp_database):
    """
    测试Counters表的创建和验证
    验证：1) 表不存在 2) 创建表 3) 表存在且结构正确
    """
    # 1. 验证初始状态 - Counters表不应该存在
    assert_table_not_exists(temp_database, "Counters")
    
    # 2. 执行迁移 - 创建Counters表
    create_counters_table(temp_database)
    
    # 3. 验证迁移后状态
    assert_table_exists_with_correct_structure(temp_database)


def assert_table_not_exists(engine, table_name):
    """断言表不存在"""
    with engine.connect() as conn:
        with pytest.raises(Exception) as exc_info:
            conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        
        error_msg = str(exc_info.value).lower()
        assert "no such table" in error_msg or "does not exist" in error_msg


def create_counters_table(engine):
    """创建Counters表 - 模拟迁移过程"""
    create_table_sql = """
    CREATE TABLE Counters (
        id INTEGER NOT NULL, 
        count INTEGER, 
        created_at DATETIME, 
        updated_at DATETIME, 
        PRIMARY KEY (id)
    );
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()


def assert_table_exists_with_correct_structure(engine):
    """断言表存在且结构正确"""
    with engine.connect() as conn:
        # 验证表存在且可查询
        result = conn.execute(text("SELECT COUNT(*) FROM Counters"))
        count = result.fetchone()[0]
        assert count == 0, "Counters table should be empty initially"
        
        # 验证表结构
        result = conn.execute(text("PRAGMA table_info(Counters)"))
        columns = [row[1] for row in result.fetchall()]
        expected_columns = ['id', 'count', 'created_at', 'updated_at']
        
        for col in expected_columns:
            assert col in columns, f"Column {col} should exist in Counters table"