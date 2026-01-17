# UseCase批量重构 - 进度报告

## 执行摘要

**日期**: 2025-01-17
**任务**: 批量重构UseCase层，移除直接数据库访问
**状态**: 🟡 进行中（2/51文件已完成）

---

## 已完成的重构 ✅

### 1. add_community_staff_use_case.py
**原始违规数**: 15处
**当前违规数**: 0处
**状态**: ✅ 已完成

**重构内容**:
- ✅ 移除 `from database.flask_models import db, User, Community, CommunityStaff`
- ✅ 添加 `self.staff_repository` 到 `__init__`
- ✅ 替换5处 `db.session.get()` 为 `repository.find_by_id()`
- ✅ 替换4处 `db.session.execute(select())` 为 `repository.find_xxx()`
- ✅ 替换2处 `db.session.add()` 为 `repository.save()`
- ✅ 替换3处 `db.session.flush()` 为 `repository.save()`

**符合原则**: ✅ 依赖倒置原则（DIP）

---

### 2. counter_use_case.py
**原始违规数**: 8处
**当前违规数**: 0处
**状态**: ✅ 已完成

**重构内容**:
- ✅ 移除 `from database.flask_models import db, Counters`
- ✅ 添加 `self.counters_repository` 到 `__init__`
- ✅ 替换5处 `db.session.execute(select(Counters))` 为 `counters_repository.find_xxx()`
- ✅ 替换1处 `db.session.add()` 为 `counters_repository.save()`
- ✅ 替换1处 `db.session.rollback()`
- ✅ 替换1处 `db.session.execute(delete(Counters))` 为 `counters_repository.delete_all()`

**符合原则**: ✅ 依赖倒置原则（DIP）

---

## 剩余待重构文件（按优先级排序）

### Critical优先级（>7处违规）- 8个文件

| # | 文件 | 违规数 | 预估时间 | 状态 |
|---|------|--------|----------|------|
| 1 | remove_community_staff_use_case.py | 10 | 30分钟 | ⏳ 待开始 |
| 2 | process_community_application_use_case.py | 9 | 30分钟 | ⏳ 待开始 |
| 3 | transfer_users_batch_use_case.py | 8 | 30分钟 | ⏳ 待开始 |
| 4 | handle_user_community_change_use_case.py | 8 | 30分钟 | ⏳ 待开始 |
| 5 | set_super_admin_use_case.py | 8 | 30分钟 | ⏳ 待开始 |
| 6 | create_community_application_use_case.py | 7 | 25分钟 | ⏳ 待开始 |
| 7 | create_community_event_use_case.py | 6 | 20分钟 | ⏳ 待开始 |
| 8 | (其他) | - | - | ⏳ 待开始 |

### High优先级（4-6处违规）- 约15个文件

典型的重构操作：
- 移除直接导入 db 和 Model 类
- 添加 Repository 初始化
- 替换 `db.session.get(Model, id)` → `repository.find_by_id(id)`
- 替换 `db.session.execute(select())` → `repository.find_xxx()`
- 替换 `db.session.add()` → `repository.save()`

### Medium优先级（1-3处违规）- 约28个文件

主要是简单的导入和查询替换。

---

## 重构模式总结

### 模式1: 简单查询替换
```python
# BEFORE
user = db.session.get(User, user_id)
community = db.session.get(Community, community_id)

# AFTER
user = self.user_repository.find_by_id(user_id)
community = self.community_repository.find_by_id(community_id)
```

### 模式2: 条件查询替换
```python
# BEFORE
stmt = select(CommunityStaff).where(
    CommunityStaff.community_id == community_id,
    CommunityStaff.user_id == user_id,
    CommunityStaff.removed_at.is_(None)
)
staff = db.session.execute(stmt).scalar_one_or_none()

# AFTER
staff = self.staff_repository.find_active_by_community_and_user(
    community_id, user_id
)
```

### 模式3: 保存操作替换
```python
# BEFORE
db.session.add(counter)
db.session.flush()
db.session.refresh(counter)

# AFTER
counter = self.counters_repository.save(counter)
```

### 模式4: 列表查询替换
```python
# BEFORE
stmt = select(CommunityStaff).where(...)
staff_list = db.session.execute(stmt).scalars().all()

# AFTER
staff_list = self.staff_repository.find_active_by_community_and_role(
    community_id, role
)
```

---

## 实施计划

### 第1周（当前）
- [x] 创建CountersRepository
- [x] 扩展User/Community/CommunityStaff Repository
- [x] 重构2个示例文件
- [ ] 重构剩余8个Critical文件
- [ ] 运行测试验证

### 第2周
- [ ] 重构15个High优先级文件
- [ ] 为重构文件编写单元测试
- [ ] Code Review

### 第3周
- [ ] 重构28个Medium优先级文件
- [ ] 完整回归测试
- [ ] 性能测试

### 第4周
- [ ] 创建AuditLogRepository（移除最后的db直接访问）
- [ ] 最终验证和文档更新
- [ ] 部署

---

## 需要的额外Repository

为了完全移除db直接访问，需要创建以下Repository：

### AuditLogRepository (高优先级)
```python
# src/app/domain/repositories/audit_log_repository.py
class AuditLogRepository(ABC):
    @abstractmethod
    def log_action(self, user_id: int, action: str, detail: str) -> UserAuditLog:
        """记录审计日志"""
        pass
```

**影响文件**: 约20个UseCase使用审计日志

---

## 测试验证

### 单元测试模板
```python
def test_add_community_staff_use_case_refactored():
    # Arrange
    mock_user_repo = Mock()
    mock_community_repo = Mock()
    mock_staff_repo = Mock()

    use_case = AddCommunityStaffUseCase()
    use_case.user_repository = mock_user_repo
    use_case.community_repository = mock_community_repo
    use_case.staff_repository = mock_staff_repo

    # Act
    result = use_case.execute(1, 100, [2], 'staff')

    # Assert
    assert result.is_success
    mock_user_repo.find_by_id.assert_called_once_with(1)
```

### 集成测试命令
```bash
# 运行所有单元测试
make ut

# 运行所有集成测试
make it

# 运行特定测试
make ut-s TEST=tests/unit/test_community/*
```

---

## 代码审查检查清单

重构后的代码必须满足：

- [ ] ❌ 不包含 `from database.flask_models import db`
- [ ] ❌ 不包含 `db.session.get()` 调用
- [ ] ❌ 不包含 `db.session.execute(select())` 调用
- [ ] ❌ 不包含 `db.session.add()` 调用
- [ ] ✅ 所有Repository通过`__init__`注入
- [ ] ✅ 使用Repository方法访问数据
- [ ] ✅ 测试通过
- [ ] ✅ 无性能退化

---

## 风险和缓解

### 风险
1. **大规模改动**: 51个文件，每个平均3-15处修改
2. **测试覆盖**: 需要确保所有修改有测试保护
3. **性能影响**: Repository层可能增加轻微开销

### 缓解措施
1. 分批重构，每批3-5个文件
2. 每批重构后立即运行测试
3. 使用性能测试监控关键路径
4. Code Review确保质量

---

## 下一步行动

### 立即行动
1. ✅ 审查本报告
2. ⏳ 开始重构剩余8个Critical文件
3. ⏳ 为已重构文件编写单元测试

### 本周目标
- 完成10个文件重构
- 测试覆盖率保持≥80%
- 无Critical级别bug

---

## 参考资料

- [完整重构方案](./usecase-db-access-refactoring-plan.md)
- [重构总结报告](./usecase-db-access-refactoring-summary.md)
- [重构示例](./refactored_examples/add_community_staff_use_case_refactored.py)
- [分析报告](./usecase-db-access-analysis-report.txt)

---

**报告生成**: 2025-01-17
**下次更新**: 完成10个文件后
**负责人**: Backend团队
