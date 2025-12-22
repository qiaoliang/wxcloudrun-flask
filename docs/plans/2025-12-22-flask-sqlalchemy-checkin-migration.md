# Flask-SQLAlchemy 迁移计划 - 打卡功能模块

## 概述
本文档详细描述了将打卡相关服务从纯 SQLAlchemy 迁移到 Flask-SQLAlchemy 的计划。

## 迁移范围
### 主要服务
1. **核心打卡服务**
   - `CheckinRuleService` - 个人打卡规则管理
   - `CheckinRecordService` - 打卡记录管理

2. **社区打卡服务**
   - `CommunityCheckinRuleService` - 社区打卡规则管理
   - `UserCheckinRuleService` - 用户规则聚合服务

3. **关联服务**
   - `CommunityService` - 已在社区模块计划中迁移
   - `UserService` - 已完成迁移

### 依赖的视图层
- `views/checkin.py` - 个人打卡 API
- `views/user_checkin.py` - 用户打卡相关 API
- `views/community_checkin.py` - 社区打卡 API

### 相关模型（已存在）
- `CheckinRule` - 个人打卡规则
- `CheckinRecord` - 打卡记录
- `CommunityCheckinRule` - 社区打卡规则
- `UserCommunityRule` - 用户社区规则关联
- `User` - 用户模型
- `Community` - 社区模型

## 迁移步骤

### Phase 1: 核心打卡服务迁移（2-3天）
1. **CheckinRuleService 迁移**
   - 更新导入：`from database.models` → `from database.flask_models`
   - 替换会话：`get_db().get_session()` → `db.session`
   - 简化事务管理
   - 保持复杂的规则查询逻辑

2. **CheckinRecordService 迁移**
   - 同样的导入和会话更新
   - 特别注意打卡操作的事务完整性
   - 保持性能优化的批量操作

### Phase 2: 社区打卡服务迁移（2-3天）
1. **CommunityCheckinRuleService 迁移**
   - 更新数据库访问方式
   - 确保与已迁移的 CommunityService 兼容
   - 处理复杂的规则继承逻辑

2. **UserCheckinRuleService 迁移**
   - 整合多个数据源的规则查询
   - 确保规则优先级逻辑正确
   - 优化聚合查询性能

### Phase 3: 视图层更新（1天）
1. **更新所有打卡相关视图**
   - 个人打卡接口
   - 社区打卡接口
   - 规则管理接口

2. **错误处理调整**
   - 更新异常捕获
   - 保持 API 响应格式一致

### Phase 4: 测试迁移（2天）
1. **单元测试更新**
   - `tests/unit/test_checkin_rule_service.py`
   - `tests/unit/test_checkin_record_service.py`
   - `tests/unit/test_community_checkin_rule_service.py`
   - `tests/unit/test_user_checkin_rule_service.py`

2. **集成测试**
   - 打卡流程端到端测试
   - 社区规则继承测试
   - 性能测试

### Phase 5: 验证和优化（1天）
1. **功能验证**
   - 个人打卡功能
   - 社区打卡功能
   - 规则管理功能

2. **性能优化**
   - 优化频繁查询
   - 确保事务效率

## 关键注意事项

### 1. 复杂查询处理
```python
# 旧方式
with get_db().get_session() as session:
    rules = session.query(CheckinRule).filter(
        and_(
            CheckinRule.user_id == user_id,
            CheckinRule.is_deleted == False
        )
    ).all()

# 新方式
rules = db.session.query(CheckinRule).filter(
    and_(
        CheckinRule.user_id == user_id,
        CheckinRule.is_deleted == False
    )
).all()
```

### 2. 事务边界
- 打卡操作需要确保原子性
- 规则创建和更新的事务处理
- 批量操作的性能考虑

### 3. 性能敏感操作
- 打卡记录查询（可能大量数据）
- 规则聚合逻辑
- 社区规则继承计算

## 特殊挑战

### 1. 规则聚合逻辑
UserCheckinRuleService 需要整合多个数据源：
- 个人规则
- 社区规则
- 用户社区规则关联

### 2. 事务完整性
打卡操作涉及：
- 创建打卡记录
- 更新用户状态
- 可能触发通知

### 3. 性能优化
- 规则查询缓存
- 打卡记录分页
- 批量数据处理

## 风险评估

### 高风险
- 规则聚合逻辑复杂，容易出错
- 打卡事务完整性要求高

### 中风险
- 性能可能受查询方式改变影响
- 异常处理需要仔细调整

### 低风险
- 模型定义已完成
- 有 UserService 迁移经验

## 时间估算
- Phase 1: 2.5 天
- Phase 2: 2.5 天
- Phase 3: 1 天
- Phase 4: 2 天
- Phase 5: 1 天
- **总计: 9 天**

## 依赖关系
1. 依赖社区管理模块迁移完成
2. 依赖 UserService 已完成迁移
3. 为后续监督功能迁移打基础

## 成功标准
- 所有打卡相关单元测试通过
- 打卡功能性能不降低
- 社区规则继承正常工作
- API 响应时间保持在可接受范围

## 后续计划
1. 迁移 CommunityEventService
2. 迁移监督功能（SupervisionService）
3. 迁移 SMS 服务
4. 清理旧的 database.models