# DatabaseCore 到 Flask-SQLAlchemy 迁移分析报告

生成时间: N/A

## 总体统计
- 总文件数: 8
- 高优先级文件: 3
- 中优先级文件: 1
- 低优先级文件: 4

## High Priority 文件

### src/database/core.py
- 行数: 224
- 发现的模式:
  - import_get_database: 1 处
  - get_session_call: 1 处
  - db_core_attr: 3 处
  - query_method: 2 处
- 具体位置:
  - 第 47 行: from config_manager import get_database_config... [import_get_database]
  - 第 132 行: return self.session_factory().query(*entities, **kwargs)... [query_method]
  - 第 138 行: return current_app.db_core.session_factory().query(*entities, **kwargs)... [db_core_attr, query_method]
  - 第 182 行: if _db_core is None or _db_core.mode != mode:... [db_core_attr]
  - 第 187 行: _db_core.initialize()... [db_core_attr]
  - 第 218 行: return db.get_session()... [get_session_call]

### src/database/initialization.py
- 行数: 196
- 发现的模式:
  - import_get_database: 1 处
  - get_session_call: 1 处
  - with_db_session: 1 处
  - db_core_attr: 1 处
  - query_method: 9 处
- 具体位置:
  - 第 11 行: from database.core import get_database... [import_get_database]
  - 第 26 行: with db_core.get_session() as session:... [get_session_call, with_db_session, db_core_attr]
  - 第 31 行: existing_admin = session.query(User).filter(... [query_method]
  - 第 67 行: existing_community = session.query(Community).filter(... [query_method]
  - 第 75 行: admin_user = session.query(User).filter(... [query_method]
  - 第 80 行: existing_staff = session.query(CommunityStaff).filter(... [query_method]
  - 第 98 行: admin_user = session.query(User).filter(... [query_method]
  - 第 130 行: existing_blackhouse = session.query(Community).filter(... [query_method]
  - 第 138 行: admin_user = session.query(User).filter(... [query_method]
  - 第 143 行: existing_staff = session.query(CommunityStaff).filter(... [query_method]
  - ... 还有 1 行

### src/wxcloudrun/utils/validators.py
- 行数: 141
- 发现的模式:
  - get_session_call: 2 处
  - with_db_session: 2 处
  - db_core_attr: 4 处
- 具体位置:
  - 第 100 行: db_core = current_app.db_core... [db_core_attr]
  - 第 101 行: with db_core.get_session() as session:... [get_session_call, with_db_session, db_core_attr]
  - 第 118 行: db_core = current_app.db_core... [db_core_attr]
  - 第 119 行: with db_core.get_session() as session:... [get_session_call, with_db_session, db_core_attr]

## Medium Priority 文件

### src/main.py
- 行数: 173
- 发现的模式:
  - import_get_database: 1 处
  - db_core_attr: 1 处
- 具体位置:
  - 第 101 行: from database import get_database... [import_get_database]
  - 第 109 行: db_core.initialize()... [db_core_attr]

## Low Priority 文件

### src/alembic_migration.py
- 行数: 350
- 发现的模式:
  - import_get_database: 5 处
- 具体位置:
  - 第 50 行: from config_manager import get_database_config... [import_get_database]
  - 第 66 行: from config_manager import get_database_config... [import_get_database]
  - 第 156 行: from config_manager import get_database_config... [import_get_database]
  - 第 221 行: from config_manager import get_database_config... [import_get_database]
  - 第 292 行: from config_manager import get_database_config... [import_get_database]

### src/config.py
- 行数: 22
- 发现的模式:
  - import_get_database: 1 处
- 具体位置:
  - 第 2 行: from config_manager import load_environment_config, get_database_config... [import_get_database]

### src/wxcloudrun/__init__.py
- 行数: 76
- 发现的模式:
  - import_get_database: 1 处
- 具体位置:
  - 第 10 行: from config_manager import get_database_config... [import_get_database]

### src/alembic/env.py
- 行数: 99
- 发现的模式:
  - import_get_database: 1 处
- 具体位置:
  - 第 12 行: from config_manager import load_environment_config, get_database_config... [import_get_database]

## 迁移建议

### 高优先级文件（建议首先迁移）
这些文件直接使用 `DatabaseCore.get_session()`，迁移后收益最大：
- `src/database/core.py`
- `src/database/initialization.py`
- `src/wxcloudrun/utils/validators.py`

### 迁移步骤
1. 为每个高优先级文件创建备份
2. 替换 `with db.get_session() as session:` 为直接使用 `db.session`
3. 更新事务处理：确保显式调用 `db.session.commit()` 和 `rollback()`
4. 运行相关测试
5. 重复步骤2-4直到所有高优先级文件完成
