# Flask-SQLAlchemy 迁移计划 - 社区管理模块

## 概述
本文档详细描述了将社区管理相关服务从纯 SQLAlchemy 迁移到 Flask-SQLAlchemy 的计划。

## 迁移范围
### 主要服务
- `CommunityService` - 社区管理核心服务
- `CommunityStaffService` - 社区工作人员管理服务

### 依赖的视图层
- `views/community.py` - 社区管理 API 接口
- `views/community_checkin.py` - 社区打卡相关接口
- `views/events.py` - 事件管理接口（部分使用）
- `views/auth.py` - 认证接口（用户分配社区时使用）

### 相关模型（已存在）
- `Community` - 社区模型
- `CommunityStaff` - 社区工作人员模型
- `CommunityApplication` - 社区申请模型
- `User` - 用户模型
- `UserAuditLog` - 用户审计日志

## 迁移步骤

### Phase 1: 准备工作
1. **备份当前服务文件**
   - 复制 `community_service.py` 为 `old_community_service.py`
   - 复制 `community_staff_service.py` 为 `old_community_staff_service.py`

2. **创建测试基类**
   - 更新 `tests/unit/conftest.py` 确保支持社区相关测试
   - 创建社区测试数据 fixtures

### Phase 2: 核心服务迁移
1. **CommunityService 迁移**
   - 更新导入语句：`from database.models` → `from database.flask_models`
   - 替换数据库会话：`get_db().get_session()` → `db.session`
   - 移除手动事务管理（Flask-SQLAlchemy 自动处理）
   - 更新方法签名，移除可选的 session 参数

2. **CommunityStaffService 迁移**
   - 同样的导入和会话更新
   - 确保与 CommunityService 的一致性

### Phase 3: 视图层更新
1. **更新导入语句**
   - 确保所有视图文件正确导入新的服务

2. **错误处理调整**
   - Flask-SQLAlchemy 的异常可能略有不同
   - 更新异常捕获逻辑

### Phase 4: 测试迁移
1. **单元测试更新**
   - 更新 `tests/unit/test_community.py`
   - 修复所有使用旧数据库方式的测试
   - 确保使用 `test_session` fixture

2. **集成测试**
   - 运行 `tests/integration/test_community_integration.py`
   - 修复任何兼容性问题

### Phase 5: 验证和清理
1. **功能验证**
   - 运行完整的社区管理功能测试
   - 确保所有 API 端点正常工作

2. **性能验证**
   - 对比迁移前后的性能指标
   - 确保没有性能退化

3. **清理工作**
   - 删除旧的备份文件（如果验证通过）
   - 更新文档

## 关键注意事项

### 1. 会话管理差异
```python
# 旧方式
with get_db().get_session() as session:
    user = session.query(User).first()

# 新方式
user = db.session.query(User).first()
```

### 2. 事务处理
- Flask-SQLAlchemy 自动处理事务
- 移除手动的 commit/rollback 调用
- 保留必要的异常处理

### 3. 关系查询
```python
# 旧方式
community = session.query(Community).options(
    joinedload(Community.users)
).first()

# 新方式（类似，但使用 db.session）
community = db.session.query(Community).options(
    joinedload(Community.users)
).first()
```

## 风险评估

### 高风险
- 社区工作人员权限逻辑复杂
- 多表关联查询可能需要调整

### 中风险
- 事务边界变化可能影响业务逻辑
- 异常处理需要更新

### 低风险
- 模型定义已完成
- UserService 已成功迁移，有参考经验

## 时间估算
- Phase 1: 0.5 天
- Phase 2: 2 天
- Phase 3: 1 天
- Phase 4: 1.5 天
- Phase 5: 1 天
- **总计: 6 天**

## 后续计划
1. 迁移打卡相关服务（CheckinRuleService、CheckinRecordService）
2. 迁移 CommunityEventService
3. 迁移监督功能（SupervisionService）
4. 迁移短信服务（SMSService）
5. 清理旧的 database.models 和相关代码

## 成功标准
- 所有社区管理相关的单元测试通过
- 所有社区管理 API 端点正常工作
- 性能不低于迁移前
- 代码更加简洁和可维护