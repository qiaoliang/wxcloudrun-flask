"""
数据库迁移测试辅助工具
提供SQLite数据库迁移测试所需的通用功能
"""
import os
import sqlite3
import tempfile
import logging
import contextlib
from typing import Dict, List, Optional, Tuple, Any, Generator
from datetime import datetime
from dataclasses import dataclass

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, upgrade, downgrade, current


@dataclass
class ColumnInfo:
    """列信息"""
    name: str
    type: str
    not_null: bool
    default_value: Optional[str]
    primary_key: bool


@dataclass
class IndexInfo:
    """索引信息"""
    name: str
    unique: bool
    columns: List[str]


@dataclass
class ForeignKeyInfo:
    """外键信息"""
    column: str
    references_table: str
    references_column: str


@dataclass
class TableSchema:
    """表结构信息"""
    columns: List[ColumnInfo]
    indexes: List[IndexInfo]
    foreign_keys: List[ForeignKeyInfo]
    primary_keys: List[str]


class MigrationTestHelper:
    """数据库迁移测试辅助工具类"""
    
    def __init__(self, app: Flask, db: SQLAlchemy, migrate: Migrate):
        """
        初始化测试辅助工具
        
        Args:
            app: Flask应用实例
            db: SQLAlchemy数据库实例
            migrate: Flask-Migrate实例
        """
        self.app = app
        self.db = db
        self.migrate = migrate
        self.logger = logging.getLogger(__name__)
        self._temp_db_path = None
        self.test_reports = []
    
    @property
    def temp_db_path(self) -> Optional[str]:
        """获取临时数据库路径"""
        return self._temp_db_path
    
    @temp_db_path.setter
    def temp_db_path(self, value: Optional[str]):
        """设置临时数据库路径"""
        self._temp_db_path = value
        
    @contextlib.contextmanager
    def temp_database(self) -> Generator[str, None, None]:
        """
        临时数据库上下文管理器
        
        Yields:
            str: 临时数据库文件路径
        """
        temp_fd = None
        temp_path = None
        try:
            # 创建临时文件
            temp_fd, temp_path = tempfile.mkstemp(suffix='.db', prefix='test_migration_')
            os.close(temp_fd)  # 关闭文件描述符，只保留路径
            
            # 更新应用配置使用临时数据库
            self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{temp_path}'
            self._temp_db_path = temp_path
            
            self.logger.info(f"创建临时数据库: {temp_path}")
            yield temp_path
            
        finally:
            self.cleanup_temp_database()
            if temp_fd is not None:
                try:
                    os.close(temp_fd)
                except:
                    pass  # 文件可能已经关闭
    
    def cleanup_temp_database(self):
        """清理临时数据库文件"""
        if self._temp_db_path and os.path.exists(self._temp_db_path):
            os.unlink(self._temp_db_path)
            self.logger.info(f"清理临时数据库: {self._temp_db_path}")
            self._temp_db_path = None
    
    def get_current_version(self) -> Optional[str]:
        """
        获取当前数据库版本
        
        Returns:
            Optional[str]: 版本号，如果未初始化则返回None
        """
        try:
            with self.app.app_context():
                revision = current()
                return revision
        except Exception as e:
            self.logger.warning(f"获取当前版本失败: {e}")
            return None
    
    def _validate_table_name(self, table_name: str) -> None:
        """
        验证表名是否有效
        
        Args:
            table_name: 表名
            
        Raises:
            ValueError: 表名无效
        """
        if not table_name or not isinstance(table_name, str):
            raise ValueError("表名必须是非空字符串")
        
        # 只允许字母、数字和下划线
        if not table_name.replace('_', '').isalnum():
            raise ValueError("表名只能包含字母、数字和下划线")
    
    def get_table_schema(self, table_name: str) -> TableSchema:
        """
        获取表结构信息
        
        Args:
            table_name: 表名
            
        Returns:
            TableSchema: 表结构信息对象
        """
        self._validate_table_name(table_name)
        
        columns = []
        indexes = []
        foreign_keys = []
        primary_keys = []
        
        try:
            with sqlite3.connect(self._temp_db_path) as conn:
                cursor = conn.cursor()
                
                # 获取列信息
                cursor.execute("PRAGMA table_info(?)", (table_name,))
                column_rows = cursor.fetchall()
                for col in column_rows:
                    column_info = ColumnInfo(
                        name=col[1],
                        type=col[2],
                        not_null=bool(col[3]),
                        default_value=col[4],
                        primary_key=bool(col[5])
                    )
                    columns.append(column_info)
                    if col[5]:
                        primary_keys.append(col[1])
                
                # 获取索引信息
                cursor.execute("PRAGMA index_list(?)", (table_name,))
                index_rows = cursor.fetchall()
                for idx in index_rows:
                    cursor.execute("PRAGMA index_info(?)", (idx[1],))
                    index_info_rows = cursor.fetchall()
                    index_info = IndexInfo(
                        name=idx[1],
                        unique=bool(idx[2]),
                        columns=[info[2] for info in index_info_rows]
                    )
                    indexes.append(index_info)
                
                # 获取外键信息
                cursor.execute("PRAGMA foreign_key_list(?)", (table_name,))
                fk_rows = cursor.fetchall()
                for fk in fk_rows:
                    fk_info = ForeignKeyInfo(
                        column=fk[3],
                        references_table=fk[2],
                        references_column=fk[4]
                    )
                    foreign_keys.append(fk_info)
                    
        except sqlite3.DatabaseError as e:
            self.logger.error(f"数据库错误 - 获取表 {table_name} 结构失败: {e}")
            raise
        except sqlite3.OperationalError as e:
            self.logger.error(f"操作错误 - 表 {table_name} 可能不存在: {e}")
            raise
        except Exception as e:
            self.logger.error(f"未知错误 - 获取表 {table_name} 结构失败: {e}")
            raise
            
        return TableSchema(
            columns=columns,
            indexes=indexes,
            foreign_keys=foreign_keys,
            primary_keys=primary_keys
        )
    
    def verify_table_exists(self, table_name: str) -> bool:
        """
        验证表是否存在
        
        Args:
            table_name: 表名
            
        Returns:
            bool: 表是否存在
        """
        self._validate_table_name(table_name)
        
        try:
            with sqlite3.connect(self._temp_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name=?",
                    (table_name,)
                )
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            self.logger.error(f"检查表 {table_name} 是否存在失败: {e}")
            return False
    
    def verify_column_exists(self, table_name: str, column_name: str) -> bool:
        """
        验证列是否存在
        
        Args:
            table_name: 表名
            column_name: 列名
            
        Returns:
            bool: 列是否存在
        """
        try:
            schema = self.get_table_schema(table_name)
            return any(col.name == column_name for col in schema.columns)
        except Exception:
            return False
    
    def verify_index_exists(self, index_name: str) -> bool:
        """
        验证索引是否存在
        
        Args:
            index_name: 索引名
            
        Returns:
            bool: 索引是否存在
        """
        try:
            with sqlite3.connect(self._temp_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='index' AND name=?",
                    (index_name,)
                )
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            self.logger.error(f"检查索引 {index_name} 是否存在失败: {e}")
            return False
    
    def execute_migration(self, revision: Optional[str] = None) -> bool:
        """
        执行数据库迁移
        
        Args:
            revision: 目标版本，None表示迁移到最新版本
            
        Returns:
            bool: 迁移是否成功
        """
        try:
            with self.app.app_context():
                current_version = self.get_current_version()
                self.logger.debug(f"当前版本: {current_version}, 目标版本: {revision}")
                
                if revision:
                    upgrade(revision)
                    self.logger.info(f"迁移到版本 {revision} 成功")
                else:
                    upgrade()
                    self.logger.info("迁移到最新版本成功")
                return True
        except Exception as e:
            current_version = self.get_current_version()
            self.logger.error(f"迁移失败 - 从版本 {current_version} 到 {revision}: {e}")
            return False
    
    def rollback_migration(self, revision: str) -> bool:
        """
        回滚数据库迁移
        
        Args:
            revision: 目标版本
            
        Returns:
            bool: 回滚是否成功
        """
        try:
            with self.app.app_context():
                current_version = self.get_current_version()
                self.logger.debug(f"当前版本: {current_version}, 回滚目标: {revision}")
                
                downgrade(revision)
                self.logger.info(f"回滚到版本 {revision} 成功")
                return True
        except Exception as e:
            current_version = self.get_current_version()
            self.logger.error(f"回滚失败 - 从版本 {current_version} 到 {revision}: {e}")
            return False
    
    def compare_schemas(self, actual: TableSchema, expected: TableSchema) -> Tuple[bool, List[str]]:
        """
        比较两个表结构
        
        Args:
            actual: 实际结构
            expected: 预期结构
            
        Returns:
            Tuple[bool, List[str]]: (是否匹配, 差异列表)
        """
        differences = []
        
        # 比较列
        actual_columns = {col.name: col for col in actual.columns}
        expected_columns = {col.name: col for col in expected.columns}
        
        # 检查缺失的列
        for name in expected_columns:
            if name not in actual_columns:
                differences.append(f"缺失列: {name}")
            else:
                # 比较列属性
                exp_col = expected_columns[name]
                act_col = actual_columns[name]
                if exp_col.type != act_col.type:
                    differences.append(f"列 {name} 类型不匹配: 预期 {exp_col.type}, 实际 {act_col.type}")
                if exp_col.not_null != act_col.not_null:
                    differences.append(f"列 {name} NOT NULL 约束不匹配")
                if exp_col.primary_key != act_col.primary_key:
                    differences.append(f"列 {name} 主键约束不匹配")
        
        # 检查多余的列
        for name in actual_columns:
            if name not in expected_columns:
                differences.append(f"多余列: {name}")
        
        # 比较索引
        actual_indexes = {idx.name: idx for idx in actual.indexes}
        expected_indexes = {idx.name: idx for idx in expected.indexes}
        
        for name in expected_indexes:
            if name not in actual_indexes:
                differences.append(f"缺失索引: {name}")
            else:
                exp_idx = expected_indexes[name]
                act_idx = actual_indexes[name]
                if exp_idx.unique != act_idx.unique:
                    differences.append(f"索引 {name} 唯一性不匹配")
                if sorted(exp_idx.columns) != sorted(act_idx.columns):
                    differences.append(f"索引 {name} 列不匹配")
        
        for name in actual_indexes:
            if name not in expected_indexes:
                differences.append(f"多余索引: {name}")
        
        return len(differences) == 0, differences
    
    def add_test_report(self, test_name: str, status: str, details: Dict = None):
        """
        添加测试报告
        
        Args:
            test_name: 测试名称
            status: 测试状态
            details: 测试详情
        """
        report = {
            'test_name': test_name,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.test_reports.append(report)
    
    def print_test_reports(self):
        """打印测试报告"""
        print("\n" + "="*60)
        print("数据库迁移测试报告")
        print("="*60)
        
        for report in self.test_reports:
            print(f"\n测试: {report['test_name']}")
            print(f"状态: {report['status']}")
            print(f"时间: {report['timestamp']}")
            
            if report['details']:
                print("详情:")
                for key, value in report['details'].items():
                    print(f"  {key}: {value}")
        
        print("\n" + "="*60)