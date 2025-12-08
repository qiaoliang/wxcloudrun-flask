"""
数据库迁移测试 - 测试Counters表的创建
遵循TDD原则：先写失败测试，观察失败，编写最小代码使其通过
"""
import pytest
import os
import tempfile
import sys
from pathlib import Path

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# 设置测试环境变量
os.environ['USE_SQLITE_FOR_TESTING'] = 'true'
os.environ['AUTO_RUN_MIGRATIONS'] = 'false'  # 手动控制迁移以便测试

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from alembic import command
from alembic.config import Config
from sqlalchemy import text


@pytest.mark.migration
def test_counters_table_migration():
    """
    RED: 测试迁移创建Counters表
    这个测试会失败，因为我们还没有正确配置迁移逻辑
    """
    # 1. 创建临时数据库
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # 2. 创建Flask应用和数据库配置
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        migrate = Migrate(app, db)
        
        # 3. 验证初始状态 - Counters表不应该存在
        with app.app_context():
            # 直接查询数据库，应该抛出异常因为表不存在
            try:
                with db.engine.connect() as conn:
                    result = conn.execute(text("SELECT COUNT(*) FROM Counters"))
                    # 如果到这里，说明表已经存在，测试失败
                    pytest.fail("Counters table should not exist before migration")
            except Exception as e:
                # 期望表不存在的异常
                assert "no such table" in str(e).lower() or "does not exist" in str(e).lower()
        
        # 4. 运行迁移
        with app.app_context():
            # 配置alembic
            alembic_cfg = Config()
            # 使用src目录下的migrations
            migrations_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src', 'migrations')
            alembic_cfg.set_main_option("script_location", migrations_path)
            alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
            
            # 运行迁移到最新版本
            command.upgrade(alembic_cfg, "head")
        
        # 5. 验证迁移后状态 - Counters表应该存在且可查询
        with app.app_context():
            # 现在应该能够查询Counters表
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM Counters"))
                count = result.fetchone()[0]
                
                # 验证表存在且初始为空
                assert count == 0
                
                # 验证表结构 - 检查是否有正确的列
                result = conn.execute(text("PRAGMA table_info(Counters)"))
                columns = [row[1] for row in result.fetchall()]
                expected_columns = ['id', 'count', 'created_at', 'updated_at']
                
                for col in expected_columns:
                    assert col in columns, f"Column {col} should exist in Counters table"
    
    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            os.unlink(db_path)