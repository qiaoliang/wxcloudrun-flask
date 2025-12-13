## 概述

SafeGuard 后端采用全新的无耦合数据库架构，实现了数据库与Flask框架的完全解耦。本文档提供完整的使用指南。

## 架构特点

- **完全解耦**：数据库层不依赖Flask框架
- **模式灵活**：支持三种使用模式
- **性能优秀**：测试环境快速重置，生产环境稳定
- **使用简单**：统一的API接口

## 架构组件

```
src/database/
├── __init__.py          # 模块入口和公共接口
├── core.py             # 数据库核心类，支持三种模式
└── models.py           # 纯SQLAlchemy模型定义
```

## 三种使用模式

1. **测试模式 (test)**
   - **用途**：单元测试、集成测试
   - **数据库**：内存数据库 (`sqlite:///:memory:`)
   - **特点**：快速重置，完全隔离

2. **独立模式 (standalone)**
   - **用途**：脚本、批处理、后台任务
   - **数据库**：文件数据库 (如 `sqlite:///safeGuard.db`)
   - **特点**：数据持久化，无Flask依赖



## 项目结构

```
backend/
├── src/
│   ├── database/           # 新数据库模块
│   │   ├── __init__.py     # 模块入口
│   │   ├── core.py         # 数据库核心
│   │   └── models.py       # 纯SQLAlchemy模型
│   ├── wxcloudrun/         # Flask应用
│   └── ...
└── tests/
│   ├── unit/               # 单元测试
│   ├── integration/        # 集成测试
│   └── e2e/                # E2E测试
└── ...
```

## 开发环境设置

### 1. 环境要求

```bash
Python 3.12+
pip install -r requirements.txt
```

### 2. 项目结构

```
backend/
├── src/
│   ├── database/           # 新数据库模块
│   │   ├── __init__.py     # 模块入口
│   │   ├── core.py         # 数据库核心
│   │   └── models.py       # 纯SQLAlchemy模型
│   ├── wxcloudrun/         # Flask应用
│   │   ├── __init__.py     # 应用初始化
│   │   ├── views/          # API视图
│   │   └── ...
│   └── ...
├── tests/
│   ├── unit/               # 单元测试
│   ├── integration/        # 集成测试
│   └── e2e/                # E2E测试
└── ...
```

## 使用新架构编写自动化测试

### 单元测试示例

```python
# tests/unit/test_user_creation.py
import pytest
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.models import User

class TestUserCreation:
    def test_create_user(self):
        """测试用户创建"""
        from database import get_database
        
        # 使用测试模式
        db = get_database('test')
        
        with db.get_session() as session:
            user = User(
                wechat_openid="test_user_123",
                nickname="测试用户",
                role=1,
                status=1
            )
            session.add(user)
            session.commit()
            
            # 验证
            assert user.user_id is not None
            assert user.nickname == "测试用户"
    
    def test_user_query(self):
        """测试用户查询"""
        from database import get_database
        
        db = get_database('test')
        
        with db.get_session() as session:
            # 创建测试数据
            user = User(
                wechat_openid="query_test",
                nickname="查询测试",
                role=2,
                status=1
            )
            session.add(user)
            session.commit()
            
            # 查询验证
            found_user = session.query(User).filter(
                User.wechat_openid == "query_test"
            ).first()
            
            assert found_user is not None
            assert found_user.role == 2
```

### 集成测试示例

```python
# tests/integration/test_user_community.py
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.models import User, Community, CommunityStaff

class TestUserCommunityIntegration:
    def test_user_join_community(self):
        """测试用户加入社区"""
        from database import get_database
        
        db = get_database('test')
        
        with db.get_session() as session:
            # 创建用户
            user = User(
                wechat_openid="community_user",
                nickname="社区用户",
                role=1,
                status=1
            )
            session.add(user)
            session.flush()
            
            # 创建社区
            community = Community(
                name="测试社区",
                location="测试地址",
                status=1
            )
            session.add(community)
            session.flush()
            
            # 添加用户到社区
            member = CommunityMember(
                community_id=community.community_id,
                user_id=user.user_id
            )
            session.add(member)
            session.commit()
            
            # 验证
            assert member.id is not None
```

### 测试配置文件

```python
# tests/unit/conftest.py
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database import initialize_for_test, get_database, reset_all

@pytest.fixture(scope='function')
def test_db():
    """为每个测试提供干净的数据库"""
    # 重置确保干净状态
    reset_all()
    
    # 初始化测试数据库
    db = initialize_for_test()
    yield db
    
    # 自动清理（内存数据库会自动清理）

@pytest.fixture(scope='function')
def test_session(test_db):
    """提供数据库会话"""
    with test_db.get_session() as session:
        yield session
```

### 运行测试

```bash
# 运行所有单元测试
pytest tests/unit/

# 运行特定测试
pytest tests/unit/test_user_creation.py

# 运行并显示详细输出
pytest tests/unit/ -v

# 生成覆盖率报告
pytest tests/unit/ --cov=database --cov-report=html
```

## 脚本和批处理

### 脚本示例

```python
# scripts/data_migration.py
#!/usr/bin/env python
"""
数据迁移脚本
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from database import initialize_for_standalone

def main():
    # 初始化独立数据库
    db = initialize_for_standalone('sqlite:///migration.db')
    
    with db.get_session() as session:
        from database.models import User
        
        # 批量导入用户
        users_data = [
            {'wechat_openid': 'user1', 'nickname': '用户1', 'role': 1},
            {'wechat_openid': 'user2', 'nickname': '用户2', 'role': 2},
        ]
        
        for user_data in users_data:
            user = User(**user_data)
            session.add(user)
        
        session.commit()
        print(f"成功导入 {len(users_data)} 个用户")

if __name__ == "__main__":
    main()
```

### 批处理任务

```python
# scripts/batch_process.py
#!/usr/bin/env python
"""
批处理任务示例
"""
from database import initialize_for_standalone
from datetime import datetime, timedelta

def cleanup_expired_tokens():
    """清理过期令牌"""
    db = initialize_for_standalone()
    
    with db.get_session() as session:
        from database.models import User
        
        # 查找过期令牌
        expired_time = datetime.now() - timedelta(days=30)
        expired_users = session.query(User).filter(
            User.refresh_token_expire < expired_time
        ).all()
        
        for user in expired_users:
            user.refresh_token = None
            user.refresh_token_expire = None
        
        session.commit()
        print(f"清理了 {len(expired_users)} 个过期令牌")

if __name__ == "__main__":
    cleanup_expired_tokens()
```

## 启动生产代码

### 1. 环境配置

```bash
# 设置生产环境变量
export ENV_TYPE=prod

# 或创建 .env.prod 文件
echo "ENV_TYPE=prod" > .env.prod
echo "SQLALCHEMY_DATABASE_URI=sqlite:///safeGuard_prod.db" >> .env.prod
```

### 2. 启动Flask应用

```python
# main.py - 生产入口
from wxcloudrun import app
from database import bind_flask_db

if __name__ == "__main__":
    # 绑定数据库到Flask
    with app.app_context():
        db_core = bind_flask_db(app.db, app)
    
    # 启动服务
    app.run(
        host='0.0.0.0',
        port=9999,
        debug=False
    )
```

### 3. 使用Docker部署

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 9999

# 启动命令
CMD ["python", "main.py"]
```

```bash
# 构建镜像
docker build -t safeguard-backend .

# 运行容器
docker run -d -p 9999:9999 safeguard-backend
```

### 4. 使用启动脚本

```bash
#!/bin/bash
# scripts/start_production.sh

echo "启动SafeGuard后端服务..."

# 设置环境
export ENV_TYPE=prod

# 启动服务
python main.py
```

## 数据库管理

### Alembic迁移

```bash
# 创建迁移
cd src
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 数据库备份

```python
# scripts/backup_database.py
import sqlite3
import datetime
from database import get_database_config

def backup_database():
    config = get_database_config()
    db_path = config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    conn = sqlite3.connect(db_path)
    backup_conn = sqlite3.connect(backup_path)
    
    conn.backup(backup_conn)
    conn.close()
    backup_conn.close()
    
    print(f"数据库已备份到: {backup_path}")

if __name__ == "__main__":
    backup_database()
```

## 常见问题

### Q: 如何在测试中使用不同的数据库？
A: 通过修改模式参数：
```python
# 内存数据库（默认）
db = get_database('test')

# 文件数据库
db = get_database('standalone')
db.initialize('sqlite:///test.db')
```

### Q: 如何在Flask外访问数据库？
A: 使用独立模式：
```python
from database import initialize_for_standalone
db = initialize_for_standalone()
with db.get_session() as session:
    # 数据库操作
```

### Q: 如何处理数据库连接池？
A: 在初始化时配置：
```python
db = initialize_for_standalone(
    'postgresql://user:pass@localhost/db',
    pool_size=10,
    max_overflow=20
)
```

## 最佳实践

1. **测试隔离**：每个测试使用独立的内存数据库
2. **资源管理**：使用上下文管理器确保会话正确关闭
3. **错误处理**：在数据库操作中使用事务和回滚
4. **性能优化**：批量操作使用bulk_save_mappings
5. **安全性**：生产环境使用连接池和SSL

## 数据库结构修改工作流程

### 工作流程概述

当需要添加新表或修改数据库结构时，遵循以下工作流程确保数据一致性和系统稳定性。

### 1. 设计阶段

#### 1.1 需求分析
- 明确新表/字段的业务需求
- 确定数据类型、约束和索引
- 评估对现有代码的影响

#### 1.2 模型设计
```python
# src/database/models.py
from sqlalchemy import Column, Integer, String, DateTime
from . import Base

class NewTable(Base):
    __tablename__ = 'new_table'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # 添加索引
    __table_args__ = (
        Index('idx_new_table_name', 'name'),
    )
```

### 2. 开发阶段

#### 2.1 创建迁移脚本
```bash
cd src
alembic revision --autogenerate -m "添加新表new_table"
```

#### 2.2 验证迁移脚本
检查生成的迁移文件 `src/alembic/versions/xxx_add_new_table.py`：
```python
"""添加新表new_table

Revision ID: xxx
Revises: previous
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('new_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('pk_new_table')
    )
    op.create_index('idx_new_table_name', 'new_table', ['name'])
    # ### end Alembic commands ###

def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_new_table_name', 'new_table')
    op.drop_table('new_table')
    # ### end Alembic commands ###
```

### 3. 测试阶段

#### 3.1 单元测试
```python
# tests/unit/test_new_table.py
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.models import NewTable

class TestNewTable:
    def test_create_new_table(self):
        """测试创建新表"""
        from database import get_database
        
        db = get_database('test')
        
        with db.get_session() as session:
            item = NewTable(name="测试项")
            session.add(item)
            session.commit()
            
            assert item.id is not None
            assert item.name == "测试项"
```

#### 3.2 集成测试
```python
# tests/integration/test_new_table_integration.py
def test_new_table_with_existing_data():
    """测试新表与现有数据的集成"""
    from database import get_database
    
    db = get_database('test')
    
    with db.get_session() as session:
        from database.models import User, NewTable
        
        # 创建用户
        user = User(wechat_openid="test_user", nickname="测试用户", role=1)
        session.add(user)
        session.flush()
        
        # 创建关联数据
        item = NewTable(name=f"{user.nickname}的项目")
        session.add(item)
        session.commit()
        
        # 验证关联
        assert item.name == "测试用户的项目"
```

### 4. 部署阶段

#### 4.1 测试环境部署
```bash
# 在测试环境执行迁移
export ENV_TYPE=test
python -c "
from alembic import command
from alembic.config import Config
alembic_cfg = Config('alembic.ini')
command.upgrade(alembic_cfg, 'head')
"
```

#### 4.2 生产环境部署
```bash
# 1. 备份生产数据库
python scripts/backup_database.py

# 2. 执行迁移
export ENV_TYPE=prod
cd src
alembic upgrade head

# 3. 验证迁移
python scripts/verify_migration.py
```

### 5. 验证阶段

#### 5.1 数据完整性验证
```python
# scripts/verify_migration.py
from database import get_database
from database.models import NewTable

def verify_new_table():
    """验证新表创建成功"""
    db = get_database('flask')  # 生产模式
    
    with db.get_session() as session:
        count = session.query(NewTable).count()
        print(f"新表记录数: {count}")
        
        # 检查表结构
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = inspector.get_columns('new_table')
        
        expected_columns = ['id', 'name', 'created_at']
        actual_columns = [col['name'] for col in columns]
        
        assert set(actual_columns) == set(expected_columns)
        print("表结构验证通过")

if __name__ == "__main__":
    verify_new_table()
```

#### 5.2 功能验证
```python
# scripts/test_new_functionality.py
def test_new_functionality():
    """测试新功能"""
    from database import get_database
    
    db = get_database('flask')
    
    with db.get_session() as session:
        from database.models import NewTable
        
        # 测试新功能
        item = NewTable(name="功能测试")
        session.add(item)
        session.commit()
        
        # 验证功能
        items = session.query(NewTable).filter(
            NewTable.name.like('%测试%')
        ).all()
        
        assert len(items) > 0
        print("功能验证通过")
```

### 6. 回滚计划

#### 6.1 回滚脚本
```python
# scripts/rollback_migration.py
from alembic import command
from alembic.config import Config

def rollback_migration(revision_id):
    """回滚到指定版本"""
    alembic_cfg = Config('alembic.ini')
    command.downgrade(alembic_cfg, revision_id)
    print(f"已回滚到版本: {revision_id}")

if __name__ == "__main__":
    # 回滚到上一个版本
    rollback_migration('previous')
```

#### 6.2 回滚验证
```python
# scripts/verify_rollback.py
def verify_rollback():
    """验证回滚成功"""
    from database import get_database
    try:
        from database.models import NewTable
        print("错误：表仍然存在，回滚失败")
    except ImportError:
        print("验证通过：表已成功移除")
```

### 7. 文档更新

#### 7.1 更新API文档
```markdown
# API/NewTable.md
## NewTable API

### 创建新项
POST /api/new-table
{
    "name": "项目名称"
}
```

#### 7.2 更新模型文档
```markdown
# docs/models.md
## 数据模型

### NewTable
新表用于存储项目信息。

字段：
- id: 主键
- name: 项目名称
- created_at: 创建时间
```

### 8. 代码质量保证

- **测试覆盖率**：确保新功能有充分的测试覆盖
- **代码审查**：所有数据库相关代码都需要经过审查
- **性能测试**：关键查询需要有性能测试

### 9. 监控指标

#### 9.1 性能监控
- 数据库连接池使用率
- 查询响应时间
- 事务执行时间

#### 9.2 错误监控
- 数据库连接错误
- 查询失败率
- 迁移执行状态

### 10. 常见修改场景

#### 添加新表
1. 在 `src/database/models.py` 中定义模型
2. 生成Alembic迁移：`alembic revision --autogenerate -m "描述"`
3. 编写单元测试验证功能
4. 在测试环境验证迁移
5. 生产环境执行迁移

#### 添加新字段
1. 在模型中添加字段定义
2. 生成迁移脚本
3. 更新相关业务代码
4. 测试验证
5. 部署执行

#### 修改表结构
1. 创建数据迁移脚本
2. 分阶段执行迁移（数据安全）
3. 验证数据完整性
4. 更新应用代码
5. 测试验证

## 总结

新架构提供了灵活、高效的数据库管理方案，支持从单元测试到生产环境的各种使用场景。通过合理使用三种模式，可以最大化开发效率和生产稳定性。

### 关键优势
- **完全解耦**：数据库不依赖Web框架，测试更快速
- **模式灵活**：根据使用场景选择最佳模式
- **易于维护**：清晰的架构分层，职责明确
- **性能优秀**：针对不同场景优化

### 使用建议
- **单元测试**：使用测试模式，快速且隔离
- **脚本任务**：使用独立模式，无额外依赖
- **Web服务**：使用Flask模式，完整功能支持