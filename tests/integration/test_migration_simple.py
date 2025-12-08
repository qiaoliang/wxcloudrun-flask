"""
数据库迁移测试 - 测试最简单的迁移场景
遵循TDD原则：先写失败测试，观察失败，编写最小代码使其通过
"""
import pytest
import os
import tempfile
import sqlite3
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


@pytest.mark.migration
class TestSimpleMigration:
    """测试最简单的数据库迁移场景"""
    
    def test_migration_creates_counters_table(self, temp_db_path):
        """
        RED: 测试迁移应该创建Counters表
        这个测试会失败，因为我们还没有创建迁移逻辑
        """
        # 1. 创建临时数据库
        db_uri = f"sqlite:///{temp_db_path}"
        
        # 2. 创建Flask应用和数据库配置
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db = SQLAlchemy(app)
        migrate = Migrate(app, db)
        
        # 3. 验证初始状态 - Counters表不应该存在
        with app.app_context():
            # 直接查询数据库，应该抛出异常因为表不存在
            conn = db.engine.connect()
            with pytest.raises(Exception):  # 期望表不存在的异常
                conn.execute("SELECT * FROM Counters LIMIT 1")
            conn.close()
        
        # 4. 运行迁移
        with app.app_context():
            # 配置alembic
            alembic_cfg = Config()
            alembic_cfg.set_main_option("script_location", "migrations")
            alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
            
            # 运行迁移到最新版本
            command.upgrade(alembic_cfg, "head")
        
        # 5. 验证迁移后状态 - Counters表应该存在且可查询
        with app.app_context():
            # 现在应该能够查询Counters表
            conn = db.engine.connect()
            result = conn.execute("SELECT COUNT(*) FROM Counters")
            count = result.fetchone()[0]
            conn.close()
            
            # 验证表存在且初始为空
            assert count == 0
    
    @pytest.fixture
    def temp_db_path(self):
        """创建临时数据库文件路径"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            yield f.name
        # 清理临时文件
        if os.path.exists(f.name):
            os.unlink(f.name)