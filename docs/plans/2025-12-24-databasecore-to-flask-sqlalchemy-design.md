# DatabaseCore 到 Flask-SQLAlchemy 迁移设计

## 概述

本设计文档描述了将 SafeGuard 项目从 DatabaseCore + Flask-SQLAlchemy 混合架构迁移到纯 Flask-SQLAlchemy 架构的方案。

## 当前架构问题

### 1. 架构复杂性
- 同时存在两套数据库访问机制：DatabaseCore 和 Flask-SQLAlchemy
- 开发者需要理解两种不同的会话管理模式
- 增加了新开发者的学习成本

### 2. 一致性缺失
- 部分代码使用 `db.session`（Flask-SQLAlchemy）
- 部分代码使用 `DatabaseCore.get_session()`（自定义层）
- 部分代码混合使用两种方式（如 `db.db.session`）

### 3. 维护负担
- 需要同时维护 DatabaseCore 和 Flask-SQLAlchemy 两套代码
- 数据库配置分散在多个文件中
- 测试环境需要特殊处理（如 e2e 测试中的表创建问题）

### 4. 测试困难
- e2e 测试中需要手动调用 `db.create_all()`
- 内存数据库配置不一致
- 测试隔离性难以保证

## 迁移目标

1. **简化架构**：消除冗余的 DatabaseCore 层，代码库更清晰
2. **提高一致性**：统一数据库访问模式，消除混合使用的不一致性
3. **减少维护成本**：只需维护一套数据库访问层
4. **提升开发体验**：让新开发者更容易理解和贡献

## 迁移原则

- **渐进式迁移**：按模块逐步推进，保持系统可运行
- **测试驱动**：每个步骤都有完整测试覆盖，确保质量
- **向后兼容**：保持现有 API 接口不变，只重构内部实现
- **风险可控**：小步快跑，随时可回滚

## 迁移步骤

### 第一阶段：统一会话管理（1-2天）

#### 1.1 创建迁移工具
```python
# scripts/db_migration_scanner.py
# 扫描所有 DatabaseCore.get_session() 调用
```

#### 1.2 统一视图层
- **优先级1**：`views/sms.py`、`views/share.py`、`views/supervision.py`
- **迁移模式**：`with db.get_session() as session:` → 直接使用 `db.session`

#### 1.3 更新中间件
- `decorators.py`：统一会话管理装饰器
- `utils/validators.py`：更新数据库验证逻辑

#### 1.4 验证测试
- 确保所有视图层测试通过
- 重点验证 e2e 测试的数据库连接

### 第二阶段：迁移服务层（2-3天）

#### 2.1 服务类重构
- `user_service.py`：迁移到纯 Flask-SQLAlchemy
- `community_service.py`：统一会话管理
- `checkin_rule_service.py`：标准化事务处理

#### 2.2 事务处理标准化
- 统一使用 `db.session.commit()` 和 `rollback()`
- 标准化 `try...except` 异常处理块
- 保持现有的事务边界不变

#### 2.3 连接池配置
- 移除 DatabaseCore 的连接池配置
- 统一使用 Flask-SQLAlchemy 的 `SQLALCHEMY_ENGINE_OPTIONS`
- 适配 SQLite 的特殊配置

#### 2.4 集成测试
- 运行所有集成测试
- 验证服务层逻辑正确性

### 第三阶段：清理与优化（1-2天）

#### 3.1 移除 DatabaseCore 代码
- 删除 `src/database/core.py`
- 删除相关导入和引用
- 更新 `src/database/__init__.py`

#### 3.2 更新配置文件
- 简化 `config.py`：只保留 Flask-SQLAlchemy 配置
- 更新 `config_manager.py`：移除 DatabaseCore 相关逻辑

#### 3.3 优化启动逻辑
- 重构 `main.py`：简化数据库初始化
- 移除 `DatabaseCore` 实例创建
- 确保 `db.create_all()` 在正确时机调用

#### 3.4 文档更新
- 更新 AGENTS.md：移除 DatabaseCore 相关说明
- 更新数据库操作指南
- 添加新架构的使用示例

## 技术实现细节

### 关键文件修改清单

#### 1. 核心文件（必须优先处理）
- `src/main.py`：移除 `DatabaseCore` 初始化
- `src/wxcloudrun/__init__.py`：确保 `db.init_app(app)` 正确配置
- `src/config.py`：简化 SQLAlchemy 配置

#### 2. 视图层迁移模式
```python
# 迁移前
from database import get_database
db = get_database()
with db.get_session() as session:
    # 数据库操作

# 迁移后
from database.flask_models import db
# 直接使用 db.session
db.session.query(...)
db.session.add(...)
db.session.commit()
```

#### 3. 事务处理标准化
```python
try:
    # 数据库操作
    db.session.add(new_object)
    db.session.commit()
except Exception as e:
    db.session.rollback()
    logger.error(f"操作失败: {e}")
    raise
```

### 兼容性处理

#### 1. 会话管理兼容层（可选）
```python
# src/database/compat.py（临时文件，迁移完成后删除）
from .flask_models import db

def get_session():
    """兼容函数，用于逐步迁移"""
    class SessionCompat:
        def __enter__(self):
            return db.session
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                db.session.commit()
            else:
                db.session.rollback()
    return SessionCompat()
```

#### 2. 环境配置适配
- `unit` 环境：内存数据库 + `db.create_all()`
- `function`/`uat`/`prod` 环境：文件数据库 + Alembic 迁移
- 保持 `ENV_TYPE` 配置不变，简化实现

#### 3. 连接池配置优化
```python
# config.py
from sqlalchemy.pool import NullPool

SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'echo': os.getenv('SQL_DEBUG', 'False').lower() == 'true'
}

# SQLite 特殊处理
if 'sqlite:///' in SQLALCHEMY_DATABASE_URI:
    SQLALCHEMY_ENGINE_OPTIONS['poolclass'] = NullPool
```

## 风险控制

### 主要风险识别

1. **会话管理不一致**
   - DatabaseCore 自动提交，Flask-SQLAlchemy 需要显式提交
   - 解决方案：添加兼容层，逐步迁移

2. **连接池行为差异**
   - DatabaseCore 对 SQLite 使用 `NullPool`
   - 解决方案：统一连接池配置

3. **事务边界变化**
   - 可能影响现有的事务隔离级别
   - 解决方案：保持事务边界不变，充分测试

4. **性能影响**
   - 新架构可能有不同的性能特征
   - 解决方案：迁移前后进行性能基准测试

### 回滚策略

1. **代码版本控制**
   - 每个迁移步骤作为一个独立的 git commit
   - 使用清晰的前缀：`feat/db-migrate-step1-*`
   - 保持每个 commit 可独立回滚

2. **功能开关（可选）**
   ```python
   USE_FLASK_SQLALCHEMY_ONLY = os.getenv('USE_FLASK_SQLALCHEMY_ONLY', 'false').lower() == 'true'
   ```

3. **监控与告警**
   - 迁移期间增加数据库性能监控
   - 关键业务接口添加健康检查
   - 日志中标记使用的数据库实现

### 验收标准

1. **功能正确性**
   - 所有现有测试通过（单元、集成、e2e）
   - 无功能回归
   - API 接口完全兼容

2. **性能基准**
   - 关键接口响应时间变化在 ±10% 以内
   - 数据库连接数无异常增长
   - 内存使用稳定

3. **代码质量**
   - 代码复杂度降低
   - 维护性提升
   - 文档完整且准确

## 测试策略

### 1. 单元测试
- 每个迁移后的模块都需要有完整的单元测试
- 测试数据库操作的各个分支
- 验证错误处理逻辑

### 2. 集成测试
- 模拟真实用户操作流程
- 测试跨模块的数据流
- 验证事务一致性

### 3. 端到端测试
- 完整业务流程测试
- 数据库连接和性能测试
- 并发场景测试

### 4. 性能测试
- 迁移前后性能对比
- 连接池压力测试
- 长时间运行稳定性测试

## 实施时间表

| 阶段 | 时间估算 | 主要任务 | 输出成果 |
|------|----------|----------|----------|
| 第一阶段 | 1-2天 | 统一会话管理 | 视图层迁移完成，测试通过 |
| 第二阶段 | 2-3天 | 迁移服务层 | 服务层统一，集成测试通过 |
| 第三阶段 | 1-2天 | 清理与优化 | DatabaseCore 移除，文档更新 |
| 验证阶段 | 1天 | 全面测试 | 性能报告，验收通过 |

## 团队协作

### 角色分工
- **架构师**：设计迁移方案，指导实施
- **开发工程师**：执行具体迁移任务
- **测试工程师**：验证迁移质量，性能测试
- **文档工程师**：更新相关文档

### 沟通机制
- 每日站会同步进度
- 每周进度评审
- 问题及时上报和解决

## 附录

### A. 需要迁移的文件清单

#### 高优先级（直接使用 DatabaseCore）
1. `src/wxcloudrun/views/sms.py`
2. `src/wxcloudrun/views/share.py`
3. `src/wxcloudrun/views/supervision.py`

#### 中优先级（混合使用）
1. `src/wxcloudrun/views/auth.py`
2. `src/wxcloudrun/views/user.py`
3. `src/wxcloudrun/views/community.py`

#### 服务层
1. `src/wxcloudrun/user_service.py`
2. `src/wxcloudrun/community_service.py`
3. `src/wxcloudrun/checkin_rule_service.py`

### B. 迁移检查清单

- [ ] 所有 `DatabaseCore.get_session()` 调用已替换
- [ ] 所有事务边界和错误处理逻辑已适配
- [ ] 数据库连接配置已统一到 Flask-SQLAlchemy
- [ ] 测试套件全部通过（单元、集成、e2e）
- [ ] 性能基准测试结果符合预期
- [ ] 数据一致性验证通过
- [ ] 相关文档已更新
- [ ] 团队培训已完成

### C. 参考资料

1. Flask-SQLAlchemy 官方文档
2. SQLAlchemy 最佳实践
3. 项目现有架构文档
4. 相关迁移设计文档（2025-12-22-*）