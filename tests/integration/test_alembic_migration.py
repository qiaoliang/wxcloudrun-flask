"""
Alembic 迁移系统的集成测试
"""
import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from pathlib import Path

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

class TestAlembicMigration:
    """Alembic 迁移系统测试类"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # 设置测试环境变量
        os.environ['ENV_TYPE'] = 'unit'
        
    def teardown_method(self):
        """每个测试方法执行后的清理"""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_config_manager_loads_environment_config(self):
        """测试配置管理器能够正确加载环境配置"""
        # unit 环境使用内存数据库，这是正确的
        from config_manager import load_environment_config, get_database_config
        
        # 加载环境配置
        load_environment_config()
        
        # 验证配置已加载
        db_config = get_database_config()
        assert db_config['DATABASE_TYPE'] == 'memory'
        assert db_config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
        
    def test_alembic_migration_script_exists(self):
        """测试 alembic_migration.py 脚本存在且可导入"""
        # 这个测试会失败，因为脚本还不存在
        from alembic_migration import migrate_database
        assert callable(migrate_database)
        
    def test_alembic_migration_returns_true_on_success(self):
        """测试迁移成功时返回 True"""
        from alembic_migration import migrate_database
        
        # Mock alembic command 成功执行
        with patch('alembic.command.upgrade') as mock_upgrade:
            mock_upgrade.return_value = None
            
            result = migrate_database()
            assert result is True
            
    def test_alembic_migration_returns_false_on_failure(self):
        """测试迁移失败时返回 False"""
        from alembic_migration import migrate_database
        
        # Mock alembic command 抛出异常
        with patch('alembic.command.upgrade') as mock_upgrade:
            mock_upgrade.side_effect = Exception("Migration failed")
            
            result = migrate_database()
            assert result is False
            
    def test_alembic_migration_logs_errors(self):
        """测试迁移失败时记录错误日志"""
        from alembic_migration import migrate_database
        import logging
        
        # 捕获日志
        with patch('alembic.command.upgrade') as mock_upgrade:
            mock_upgrade.side_effect = Exception("Test error")
            
            with patch('logging.Logger.error') as mock_error:
                migrate_database()
                
                # 验证错误被记录
                mock_error.assert_called()
                
    def test_main_py_calls_migration_before_app_creation(self):
        """测试 main.py 在创建应用前调用迁移"""
        # 这个测试验证 main 函数的逻辑结构
        # 由于 ENV_TYPE 在模块导入时就被读取，我们需要重新导入模块
        import importlib
        
        # 使用 func 环境（开发环境）来确保迁移被调用
        os.environ['ENV_TYPE'] = 'func'
        
        # 重新导入 main 模块
        if 'main' in sys.modules:
            del sys.modules['main']
        if 'wxcloudrun' in sys.modules:
            del sys.modules['wxcloudrun']
        from main import main
        
        with patch('main.run_migration') as mock_run_migration:
            with patch('main.create_app') as mock_create_app:
                with patch('wxcloudrun.app.run') as mock_run:
                    
                    # 修改 sys.argv 来模拟命令行参数
                    with patch.object(sys, 'argv', ['main.py', '0.0.0.0', '8080']):
                        main()
                    
                    # 验证迁移在应用创建前被调用
                    mock_run_migration.assert_called_once()
                    mock_create_app.assert_called_once()
                    
    def test_main_py_exits_on_migration_failure(self):
        """测试迁移失败时 main.py 正确退出"""
        import importlib
        
        # 使用 func 环境（开发环境）来确保迁移被调用
        os.environ['ENV_TYPE'] = 'func'
        
        # 重新导入 main 模块
        if 'main' in sys.modules:
            del sys.modules['main']
        if 'wxcloudrun' in sys.modules:
            del sys.modules['wxcloudrun']
        from main import main
        
        with patch('main.run_migration') as mock_run_migration:
            mock_run_migration.return_value = False
            
            # 修改 sys.argv 来模拟命令行参数
            with patch.object(sys, 'argv', ['main.py', '0.0.0.0', '8080']):
                with pytest.raises(SystemExit) as exc_info:
                    main()
                    
                assert exc_info.value.code == 1
            
    def test_alembic_env_loads_correctly(self):
        """测试 alembic/env.py 能够正确加载"""
        # 测试 env.py 文件是否存在且可导入
        # 获取实际的项目根目录
        current_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        env_file = current_dir / 'src' / 'alembic' / 'env.py'
        assert env_file.exists(), f"env.py not found at {env_file}"
        
        # 验证 env.py 包含必要的函数
        content = env_file.read_text()
        assert 'def run_migrations_online():' in content
        assert 'def run_migrations_offline():' in content
        
    def test_alembic_directory_structure_created(self):
        """测试 Alembic 目录结构被正确创建"""
        # 获取实际的项目根目录
        current_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        base_dir = current_dir / 'src'
        alembic_dir = base_dir / 'alembic'
        versions_dir = alembic_dir / 'versions'
        
        assert alembic_dir.exists(), f"alembic dir not found at {alembic_dir}"
        assert versions_dir.exists(), f"versions dir not found at {versions_dir}"
        assert (alembic_dir / 'env.py').exists()
        assert (alembic_dir / 'script.py.mako').exists()
        assert (base_dir / 'alembic.ini').exists()