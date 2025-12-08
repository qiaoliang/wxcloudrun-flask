"""
数据库迁移集成测试
测试数据库迁移的正确性和完整性
"""
import pytest
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from wxcloudrun import app, db
from flask_migrate import Migrate
from tests.integration.migration_test_utils import MigrationTestHelper, TableSchema, ColumnInfo, IndexInfo


class TestDatabaseMigration:
    """数据库迁移测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """每个测试方法执行前的设置"""
        # 初始化Flask-Migrate
        self.migrate = Migrate(app, db)
        
        # 创建测试辅助工具
        self.helper = MigrationTestHelper(app, db, self.migrate)
        
        # 保存原始配置
        self.original_db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
    
    def test_complete_migration_path(self):
        """测试完整迁移路径 - 从空数据库到最新版本"""
        with self.helper.temp_database() as db_path:
            # 记录测试开始
            self.helper.add_test_report(
                "test_complete_migration_path",
                "开始",
                {"db_path": db_path}
            )
            
            # 验证初始状态
            initial_version = self.helper.get_current_version()
            assert initial_version is None, "初始数据库应该没有版本"
            
            # 执行完整迁移
            success = self.helper.execute_migration()
            assert success, "完整迁移应该成功"
            
            # 验证最终版本
            final_version = self.helper.get_current_version()
            assert final_version is not None, "迁移后应该有版本号"
            
            # 验证核心表存在
            expected_tables = [
                'counters', 'users', 'checkin_rules', 'checkin_records',
                'supervision_relations', 'notifications', 'system_configs',
                'verification_codes'
            ]
            
            for table in expected_tables:
                assert self.helper.verify_table_exists(table), f"表 {table} 应该存在"
            
            # 记录测试成功
            self.helper.add_test_report(
                "test_complete_migration_path",
                "成功",
                {
                    "initial_version": initial_version,
                    "final_version": final_version,
                    "tables_count": len(expected_tables)
                }
            )
    
    def test_initial_database_creation(self):
        """测试初始数据库结构创建（7788862c130d）"""
        with self.helper.temp_database() as db_path:
            # 执行初始迁移
            success = self.helper.execute_migration('7788862c130d')
            assert success, "初始迁移应该成功"
            
            # 验证版本
            version = self.helper.get_current_version()
            assert version == '7788862c130d', f"版本应该是 7788862c130d，实际是 {version}"
            
            # 验证counters表结构
            counters_schema = self.helper.get_table_schema('Counters')
            expected_counters = TableSchema(
                columns=[
                    ColumnInfo(name='id', type='INTEGER', not_null=True, default_value=None, primary_key=True),
                    ColumnInfo(name='count', type='INTEGER', not_null=True, default_value=None, primary_key=False),
                    ColumnInfo(name='created_at', type='DATETIME', not_null=True, default_value=None, primary_key=False),
                    ColumnInfo(name='updated_at', type='DATETIME', not_null=True, default_value=None, primary_key=False)
                ],
                indexes=[],
                foreign_keys=[],
                primary_keys=['id']
            )
            
            is_match, differences = self.helper.compare_schemas(counters_schema, expected_counters)
            assert is_match, f"counters表结构不匹配: {differences}"
            
            # 验证users表结构
            users_schema = self.helper.get_table_schema('users')
            assert len(users_schema.columns) > 0, "users表应该有列"
            assert any(col.name == 'user_id' and col.primary_key for col in users_schema.columns), "users表应该有主键user_id"
            
            # 记录测试结果
            self.helper.add_test_report(
                "test_initial_database_creation",
                "成功",
                {
                    "version": version,
                    "tables_created": ['counters', 'users', 'checkin_rules', 'checkin_records']
                }
            )
    
    def test_verification_codes_column_addition(self):
        """测试verification_codes表添加is_used列的迁移（c726e805bc85）"""
        with self.helper.temp_database() as db_path:
            # 先执行初始迁移
            assert self.helper.execute_migration('7788862c130d'), "初始迁移应该成功"
            
            # 验证is_used列不存在
            assert not self.helper.verify_column_exists('verification_codes', 'is_used'), "初始状态不应该有is_used列"
            
            # 执行列添加迁移
            success = self.helper.execute_migration('c726e805bc85')
            assert success, "列添加迁移应该成功"
            
            # 验证版本
            version = self.helper.get_current_version()
            assert version == 'c726e805bc85', f"版本应该是 c726e805bc85，实际是 {version}"
            
            # 验证is_used列存在
            assert self.helper.verify_column_exists('verification_codes', 'is_used'), "is_used列应该存在"
            
            # 验证列属性
            verification_codes_schema = self.helper.get_table_schema('verification_codes')
            is_used_column = next((col for col in verification_codes_schema.columns if col.name == 'is_used'), None)
            
            assert is_used_column is not None, "is_used列应该存在"
            assert is_used_column.type == 'BOOLEAN', f"is_used应该是BOOLEAN类型，实际是 {is_used_column.type}"
            assert is_used_column.default_value == '0', f"is_used默认值应该是0，实际是 {is_used_column.default_value}"
            
            # 记录测试结果
            self.helper.add_test_report(
                "test_verification_codes_column_addition",
                "成功",
                {
                    "version": version,
                    "column_added": "is_used",
                    "column_type": is_used_column.type,
                    "default_value": is_used_column.default_value
                }
            )
    
    def test_migration_execution(self):
        """测试迁移执行机制"""
        with self.helper.temp_database() as db_path:
            # 测试从None到7788862c130d
            initial_version = self.helper.get_current_version()
            assert initial_version is None, "初始版本应该是None"
            
            success = self.helper.execute_migration('7788862c130d')
            assert success, "迁移应该成功"
            
            version_after_first = self.helper.get_current_version()
            assert version_after_first == '7788862c130d', "版本应该正确更新"
            
            # 测试从7788862c130d到c726e805bc85
            success = self.helper.execute_migration('c726e805bc85')
            assert success, "第二次迁移应该成功"
            
            version_after_second = self.helper.get_current_version()
            assert version_after_second == 'c726e805bc85', "版本应该再次正确更新"
            
            # 记录测试结果
            self.helper.add_test_report(
                "test_migration_execution",
                "成功",
                {
                    "initial_version": initial_version,
                    "first_migration": version_after_first,
                    "second_migration": version_after_second
                }
            )
    
    def test_rollback_capability(self):
        """测试迁移回滚功能"""
        with self.helper.temp_database() as db_path:
            # 迁移到最新版本
            assert self.helper.execute_migration(), "迁移到最新版本应该成功"
            latest_version = self.helper.get_current_version()
            
            # 回滚到初始版本
            success = self.helper.rollback_migration('7788862c130d')
            assert success, "回滚应该成功"
            
            rollback_version = self.helper.get_current_version()
            assert rollback_version == '7788862c130d', f"回滚后版本应该是7788862c130d，实际是{rollback_version}"
            
            # 验证is_used列被删除
            assert not self.helper.verify_column_exists('verification_codes', 'is_used'), "回滚后is_used列不应该存在"
            
            # 再次迁移到最新版本
            success = self.helper.execute_migration()
            assert success, "重新迁移应该成功"
            
            final_version = self.helper.get_current_version()
            assert final_version == latest_version, f"重新迁移后版本应该是{latest_version}，实际是{final_version}"
            
            # 验证is_used列重新存在
            assert self.helper.verify_column_exists('verification_codes', 'is_used'), "重新迁移后is_used列应该存在"
            
            # 记录测试结果
            self.helper.add_test_report(
                "test_rollback_capability",
                "成功",
                {
                    "latest_version": latest_version,
                    "rollback_version": rollback_version,
                    "final_version": final_version
                }
            )
    
    def test_version_tracking(self):
        """测试Alembic版本追踪机制"""
        with self.helper.temp_database() as db_path:
            # 验证alembic_version表
            assert self.helper.execute_migration('7788862c130d'), "迁移应该成功"
            assert self.helper.verify_table_exists('alembic_version'), "alembic_version表应该存在"
            
            # 检查版本记录
            alembic_schema = self.helper.get_table_schema('alembic_version')
            version_num_column = next((col for col in alembic_schema.columns if col.name == 'version_num'), None)
            
            assert version_num_column is not None, "version_num列应该存在"
            assert version_num_column.type == 'VARCHAR(32)', f"version_num应该是VARCHAR(32)，实际是{version_num_column.type}"
            assert version_num_column.not_null, "version_num应该NOT NULL"
            
            # 验证版本号正确
            current_version = self.helper.get_current_version()
            assert current_version == '7788862c130d', f"版本号应该是7788862c130d，实际是{current_version}"
            
            # 记录测试结果
            self.helper.add_test_report(
                "test_version_tracking",
                "成功",
                {
                    "current_version": current_version,
                    "alembic_version_table": "存在",
                    "version_num_column": {
                        "type": version_num_column.type,
                        "not_null": version_num_column.not_null
                    }
                }
            )
    
    def test_table_relationships(self):
        """测试表之间的关系完整性"""
        with self.helper.temp_database() as db_path:
            # 执行所有迁移
            assert self.helper.execute_migration(), "迁移应该成功"
            
            # 验证checkin_records表的外键关系
            checkin_records_schema = self.helper.get_table_schema('checkin_records')
            
            # 检查是否有外键
            assert len(checkin_records_schema.foreign_keys) > 0, "checkin_records应该有外键"
            
            # 验证外键指向正确的表
            for fk in checkin_records_schema.foreign_keys:
                if fk.column == 'solo_user_id':
                    assert fk.references_table == 'users', f"solo_user_id应该引用users表，实际引用{fk.references_table}"
                    assert fk.references_column == 'user_id', f"solo_user_id应该引用user_id列，实际引用{fk.references_column}"
            
            # 记录测试结果
            self.helper.add_test_report(
                "test_table_relationships",
                "成功",
                {
                    "foreign_keys_count": len(checkin_records_schema.foreign_keys),
                    "sample_foreign_key": checkin_records_schema.foreign_keys[0].__dict__ if checkin_records_schema.foreign_keys else None
                }
            )
    
    def test_constraints_and_indexes(self):
        """测试所有约束和索引"""
        with self.helper.temp_database() as db_path:
            # 执行所有迁移
            assert self.helper.execute_migration(), "迁移应该成功"
            
            # 验证users表的主键
            users_schema = self.helper.get_table_schema('users')
            assert 'user_id' in users_schema.primary_keys, "user_id应该是主键"
            
            # 验证主键列的属性
            user_id_column = next(col for col in users_schema.columns if col.name == 'user_id')
            assert user_id_column.primary_key, "user_id列应该标记为主键"
            assert user_id_column.not_null, "主键列应该NOT NULL"
            
            # 检查索引
            if users_schema.indexes:
                for index in users_schema.indexes:
                    assert self.helper.verify_index_exists(index.name), f"索引 {index.name} 应该存在"
            
            # 记录测试结果
            self.helper.add_test_report(
                "test_constraints_and_indexes",
                "成功",
                {
                    "users_primary_keys": users_schema.primary_keys,
                    "users_indexes_count": len(users_schema.indexes),
                    "constraints_verified": True
                }
            )
    
    def test_migration_error_handling(self):
        """测试迁移错误处理"""
        with self.helper.temp_database() as db_path:
            # 尝试迁移到不存在的版本
            success = self.helper.execute_migration('nonexistent_version')
            assert not success, "迁移到不存在的版本应该失败"
            
            # 验证数据库状态未改变
            version = self.helper.get_current_version()
            assert version is None, "失败的迁移不应该改变版本"
            
            # 记录测试结果
            self.helper.add_test_report(
                "test_migration_error_handling",
                "成功",
                {
                    "invalid_version": "nonexistent_version",
                    "migration_failed": True,
                    "version_unchanged": True
                }
            )
    
    def test_invalid_table_name_handling(self):
        """测试无效表名的处理"""
        with self.helper.temp_database() as db_path:
            # 测试空表名
            with pytest.raises(ValueError, match="表名必须是非空字符串"):
                self.helper.get_table_schema("")
            
            # 测试包含非法字符的表名
            with pytest.raises(ValueError, match="表名只能包含字母、数字和下划线"):
                self.helper.get_table_schema("table-name")
            
            # 测试SQL注入尝试
            with pytest.raises(ValueError, match="表名只能包含字母、数字和下划线"):
                self.helper.get_table_schema("users; DROP TABLE users; --")
            
            # 记录测试结果
            self.helper.add_test_report(
                "test_invalid_table_name_handling",
                "成功",
                {
                    "invalid_names_tested": ["", "table-name", "users; DROP TABLE users; --"],
                    "all_rejected": True
                }
            )
    
    def test_temporary_database_cleanup(self):
        """测试临时数据库清理"""
        db_paths = []
        
        # 创建多个临时数据库
        for i in range(3):
            with self.helper.temp_database() as db_path:
                db_paths.append(db_path)
                # 执行一些操作
                assert self.helper.execute_migration('7788862c130d'), "迁移应该成功"
                # 验证文件存在
                assert os.path.exists(db_path), f"临时数据库 {db_path} 应该存在"
        
        # 验证所有临时文件已被清理
        for db_path in db_paths:
            assert not os.path.exists(db_path), f"临时数据库 {db_path} 应该被清理"
        
        # 记录测试结果
        self.helper.add_test_report(
            "test_temporary_database_cleanup",
            "成功",
            {
                "databases_created": len(db_paths),
                "all_cleaned": True
            }
        )
    
    def teardown_method(self):
        """每个测试方法执行后的清理"""
        # 恢复原始配置
        if hasattr(self, 'original_db_uri'):
            app.config['SQLALCHEMY_DATABASE_URI'] = self.original_db_uri
        
        # 打印测试报告
        self.helper.print_test_reports()


# 运行测试的快捷方式
if __name__ == "__main__":
    pytest.main([__file__, "-v"])