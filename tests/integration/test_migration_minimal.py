"""
最简单的数据库迁移测试
遵循TDD原则：先写失败测试，观察失败，编写最小代码使其通过
"""
import pytest
import os
import tempfile
import sys

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# 设置测试环境变量
os.environ['USE_SQLITE_FOR_TESTING'] = 'true'

from flask import Flask
from flask_sqlalchemy import SQLAlchemy


@pytest.mark.migration
def test_database_connection():
    """
    RED: 测试数据库连接
    这个测试应该失败，因为我们还没有正确配置数据库
    """
    # 创建临时数据库文件
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # 创建Flask应用
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_path}"
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # 初始化数据库
        db = SQLAlchemy(app)
        
        # 测试连接
        with app.app_context():
            # 尝试执行简单查询 - 使用新版本SQLAlchemy API
            try:
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    # 如果到这里，说明连接成功
                    assert True
            except Exception as e:
                # 如果有异常，测试失败
                pytest.fail(f"Database connection failed: {e}")
    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            os.unlink(db_path)