# DDD 迁移执行路线图

**版本**: v1.0
**创建日期**: 2026-01-15
**预计总工期**: 16 周
**目标**: 按阶段完成 DDD 迁移，确保质量和稳定性

---

## 目录

1. [总体时间线](#总体时间线)
2. [阶段 0：准备工作](#阶段-0准备工作-1-2周)
3. [阶段 1：认证模块迁移](#阶段-1认证模块迁移-1周)
4. [阶段 2：用户管理模块迁移](#阶段-2用户管理模块迁移-2周)
5. [阶段 3：社区管理模块迁移](#阶段-3社区管理模块迁移-2周)
6. [阶段 4：打卡管理模块迁移](#阶段-4打卡管理模块迁移-2周)
7. [阶段 5：事件管理模块迁移](#阶段-5事件管理模块迁移-1周)
8. [阶段 6：监督管理模块迁移](#阶段-6监督管理模块迁移-1周)
9. [阶段 7：分享链接模块迁移](#阶段-7分享链接模块迁移-1周)
10. [阶段 8：其他模块迁移](#阶段-8其他模块迁移-1周)
11. [阶段 9：清理旧代码](#阶段-9清理旧代码-1周)
12. [阶段 10：聚合边界优化](#阶段-10聚合边界优化-2-3周)
13. [里程碑和验收标准](#里程碑和验收标准)
14. [资源分配](#资源分配)
15. [沟通计划](#沟通计划)

---

## 总体时间线

```
Week 1-2:   准备工作
Week 3:     认证模块迁移
Week 4-5:   用户管理模块迁移
Week 6-7:   社区管理模块迁移
Week 8-9:   打卡管理模块迁移
Week 10:    事件管理模块迁移
Week 11:    监督管理模块迁移
Week 12:    分享链接和其他模块迁移
Week 13:    清理旧代码
Week 14-16: 聚合边界优化
```

**关键里程碑**:
- Week 2: 准备工作完成，开始迁移
- Week 5: 核心模块（认证、用户、社区）迁移完成
- Week 9: 主要业务模块迁移完成
- Week 12: 所有模块迁移完成
- Week 13: 旧代码清理完成
- Week 16: 聚合边界优化完成，DDD 迁移完成

---

## 阶段 0：准备工作（1-2周）

### 时间安排

**Week 1**: 完成核心 UseCase 测试
**Week 2**: 设置 CI/CD，准备迁移环境

### 详细任务

#### Week 1: 完成核心 UseCase 测试

**Day 1-2**: 认证模块 UseCase 测试
- [ ] 为 LoginWeChatUseCase 编写单元测试
- [ ] 为 RefreshTokenUseCase 编写单元测试
- [ ] 为 LogoutUseCase 编写单元测试
- [ ] 运行测试，确保通过

**Day 3-4**: 用户管理模块 UseCase 测试
- [ ] 为 UpdateProfileUseCase 编写单元测试
- [ ] 为 ChangePasswordUseCase 编写单元测试
- [ ] 为 UploadAvatarUseCase 编写单元测试
- [ ] 为 SearchUsersUseCase 编写单元测试
- [ ] 运行测试，确保通过

**Day 5**: 社区管理模块 UseCase 测试
- [ ] 为 CreateCommunityUseCase 编写单元测试
- [ ] 为 JoinCommunityUseCase 编写单元测试
- [ ] 为 LeaveCommunityUseCase 编写单元测试
- [ ] 运行测试，确保通过

#### Week 2: 设置 CI/CD，准备迁移环境

**Day 1-2**: CI/CD 配置
- [ ] 配置 GitHub Actions 工作流
- [ ] 配置单元测试流水线
- [ ] 配置集成测试流水线
- [ ] 配置代码覆盖率报告

**Day 3-4**: 迁移环境准备
- [ ] 创建迁移分支 `feature/ddd-migration-phase-1`
- [ ] 设置测试数据库
- [ ] 准备测试数据生成器
- [ ] 编写迁移文档

**Day 5**: 最终检查
- [ ] 检查所有测试通过
- [ ] 检查 CI/CD 配置正确
- [ ] 检查迁移环境就绪
- [ ] 团队评审和确认

### 验收标准

- [ ] 所有核心 UseCase 都有单元测试
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] CI/CD 流水线配置完成
- [ ] 迁移环境准备就绪
- [ ] 团队评审通过

### 风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 测试编写时间不足 | 中 | 中 | 优先完成核心 UseCase 测试 |
| CI/CD 配置问题 | 低 | 中 | 提前测试，准备备选方案 |
| 团队准备不足 | 低 | 低 | 提前培训，文档说明 |

---

## 阶段 1：认证模块迁移（1周）

### 时间安排

**Week 3**: 认证模块完整迁移

### 详细任务

#### Day 1-2: 完善 UseCase 实现

**任务**:
- [ ] 检查 LoginWeChatUseCase 实现完整性
- [ ] 检查 RefreshTokenUseCase 实现完整性
- [ ] 检查 LogoutUseCase 实现完整性
- [ ] 补充缺失的功能
- [ ] 优化代码质量

**产出**:
- 完整的认证 UseCase 实现
- 单元测试覆盖率 ≥ 90%

#### Day 3-4: 重构认证路由

**任务**:
- [ ] 阅读 `src/app/modules/auth/routes.py`
- [ ] 识别所有使用旧服务的代码
- [ ] 重构路由使用 UseCase
- [ ] 保持 API 兼容性
- [ ] 添加错误处理

**代码示例**:
```python
# 旧代码
@auth_bp.route('/login/wechat', methods=['POST'])
def login_wechat():
    code = request.json.get('code')
    result = UserService.login_wechat(code)
    return make_succ_response(result)

# 新代码
from app.application.use_cases.auth.login_wechat_use_case import LoginWeChatUseCase

@auth_bp.route('/login/wechat', methods=['POST'])
def login_wechat():
    code = request.json.get('code')
    use_case = LoginWeChatUseCase()
    result = use_case.execute(code=code)
    if result.status == UseCaseStatus.SUCCESS:
        return make_succ_response(result.data)
    else:
        return make_err_response(result.message)
```

**产出**:
- 重构后的认证路由
- 集成测试通过

#### Day 5: 测试和验证

**任务**:
- [ ] 运行所有认证相关测试
- [ ] 运行集成测试
- [ ] 性能测试（登录响应时间 < 500ms）
- [ ] 前端联调测试
- [ ] 代码审查

**测试清单**:
- [ ] 单元测试: `pytest tests/unit/test_*login*.py -v`
- [ ] 集成测试: `pytest tests/integration/test_auth_login_phone.py -v`
- [ ] 性能测试: `pytest tests/performance/test_api_performance.py::test_login_performance -v`

**产出**:
- 所有测试通过
- 性能指标达标
- 代码审查通过

### 验收标准

- [ ] 认证模块所有 UseCase 实现完整
- [ ] 认证路由完全使用 UseCase
- [ ] 所有测试通过（单元 + 集成 + 性能）
- [ ] API 兼容性保持
- [ ] 性能无明显下降
- [ ] 代码审查通过

### 风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| API 不兼容 | 低 | 高 | 充分测试，前端联调 |
| 性能下降 | 中 | 中 | 性能测试，优化查询 |
| 测试失败 | 低 | 中 | 充分测试，准备回滚 |

---

## 阶段 2：用户管理模块迁移（2周）

### 时间安排

**Week 4**: 实现 UseCase 和单元测试
**Week 5**: 重构路由和集成测试

### 详细任务

#### Week 4: 实现 UseCase 和单元测试

**Day 1-2**: 实现用户管理 UseCase
- [ ] 实现 UpdateProfileUseCase
- [ ] 实现 ChangePasswordUseCase
- [ ] 实现 UploadAvatarUseCase
- [ ] 实现 SearchUsersUseCase
- [ ] 实现 GetUserDetailsUseCase（如需要）

**Day 3-4**: 编写单元测试
- [ ] 为 UpdateProfileUseCase 编写单元测试
- [ ] 为 ChangePasswordUseCase 编写单元测试
- [ ] 为 UploadAvatarUseCase 编写单元测试
- [ ] 为 SearchUsersUseCase 编写单元测试
- [ ] 为 GetUserDetailsUseCase 编写单元测试

**Day 5**: 测试和优化
- [ ] 运行所有单元测试
- [ ] 优化代码质量
- [ ] 代码审查

#### Week 5: 重构路由和集成测试

**Day 1-3**: 重构用户路由
- [ ] 阅读 `src/app/modules/user/routes.py`（826行代码）
- [ ] 识别所有使用旧服务的代码
- [ ] 重构路由使用 UseCase
- [ ] 保持 API 兼容性

**重点迁移**:
- [ ] 用户资料更新: `UpdateProfileUseCase`
- [ ] 修改密码: `ChangePasswordUseCase`
- [ ] 上传头像: `UploadAvatarUseCase`
- [ ] 搜索用户: `SearchUsersUseCase`
- [ ] 获取用户详情: `GetUserDetailsUseCase`

**Day 4**: 启用聚合根和领域事件
- [ ] 在 UseCase 中使用 UserAggregate
- [ ] 发布用户领域事件
- [ ] 测试领域事件发布

**代码示例**:
```python
# 在 UpdateProfileUseCase 中使用聚合根
from app.domain.aggregates.user_aggregate import UserAggregate
from app.domain.events.user_events import UserUpdatedEvent

class UpdateProfileUseCase(BaseUseCase):
    def execute(self, user_id, **kwargs):
        # 获取用户聚合
        user_aggregate = UserAggregate(user_id)

        # 更新用户资料
        user_aggregate.update_profile(**kwargs)

        # 发布领域事件
        event = UserUpdatedEvent(
            aggregate_id=user_id,
            data={'updated_fields': list(kwargs.keys())}
        )
        EventBus.publish(event)

        # 保存
        self.user_repository.save(user_aggregate.root)

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            data=user_aggregate.root.to_dict()
        )
```

**Day 5**: 测试和验证
- [ ] 运行所有用户相关测试
- [ ] 运行集成测试
- [ ] 性能测试
- [ ] 代码审查

### 验收标准

- [ ] 用户管理所有 UseCase 实现完整
- [ ] 用户路由完全使用 UseCase
- [ ] UserAggregate 正确使用
- [ ] 用户领域事件正确发布
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

### 风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 路由代码复杂 | 中 | 中 | 分步重构，充分测试 |
| 聚合根使用不当 | 中 | 中 | 代码审查，文档说明 |
| 领域事件发布失败 | 低 | 中 | 充分测试，错误处理 |

---

## 阶段 3：社区管理模块迁移（2周）

### 时间安排

**Week 6**: 实现 UseCase 和单元测试
**Week 7**: 重构路由和集成测试

### 详细任务

#### Week 6: 实现 UseCase 和单元测试

**Day 1-2**: 实现社区管理 UseCase
- [ ] 检查已有 UseCase 实现
- [ ] 补充缺失的功能
- [ ] 优化代码质量

**已有 UseCase**:
- [x] CreateCommunityUseCase
- [x] JoinCommunityUseCase
- [x] LeaveCommunityUseCase
- [x] GetCommunityDetailsUseCase
- [x] UpdateCommunityUseCase
- [x] DeleteCommunityUseCase
- [x] SearchCommunityUseCase
- [x] ListCommunityUsersUseCase

**Day 3-4**: 编写单元测试
- [ ] 为所有社区 UseCase 编写单元测试
- [ ] 测试覆盖率 ≥ 90%

**Day 5**: 测试和优化
- [ ] 运行所有单元测试
- [ ] 优化代码质量
- [ ] 代码审查

#### Week 7: 重构路由和集成测试

**Day 1-3**: 重构社区路由
- [ ] 阅读 `src/app/modules/community/routes.py`
- [ ] 重构社区子模块（6个子模块）:
  - [ ] community_basic.py
  - [ ] community_members.py
  - [ ] community_staff.py
  - [ ] community_applications.py
  - [ ] user_search.py
  - [ ] user_community_ops.py
- [ ] 重构主路由文件
- [ ] 保持 API 兼容性

**Day 4**: 启用聚合根和领域事件
- [ ] 在 UseCase 中使用 CommunityAggregate
- [ ] 发布社区领域事件
- [ ] 测试领域事件发布

**代码示例**:
```python
# 在 CreateCommunityUseCase 中使用聚合根
from app.domain.aggregates.community_aggregate import CommunityAggregate
from app.domain.events.community_events import CommunityCreatedEvent

class CreateCommunityUseCase(BaseUseCase):
    def execute(self, user_id, **kwargs):
        # 创建社区聚合
        community_aggregate = CommunityAggregate(
            name=kwargs['name'],
            description=kwargs.get('description'),
            address=kwargs.get('address'),
            creator_id=user_id
        )

        # 发布领域事件
        event = CommunityCreatedEvent(
            aggregate_id=community_aggregate.root.community_id,
            data={'name': kwargs['name'], 'creator_id': user_id}
        )
        EventBus.publish(event)

        # 保存
        self.community_repository.save(community_aggregate.root)

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            data=community_aggregate.root.to_dict()
        )
```

**Day 5**: 测试和验证
- [ ] 运行所有社区相关测试
- [ ] 运行集成测试
- [ ] 性能测试
- [ ] 代码审查

### 验收标准

- [ ] 社区管理所有 UseCase 实现完整
- [ ] 社区路由完全使用 UseCase
- [ ] CommunityAggregate 正确使用
- [ ] 社区领域事件正确发布
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

### 风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 子模块复杂 | 高 | 中 | 分步重构，充分测试 |
| 业务逻辑复杂 | 中 | 中 | 代码审查，文档说明 |
| 数据关联复杂 | 中 | 中 | 优化查询，使用缓存 |

---

## 阶段 4：打卡管理模块迁移（2周）

### 时间安排

**Week 8**: 实现 UseCase 和单元测试
**Week 9**: 重构路由和集成测试

### 详细任务

#### Week 8: 实现 UseCase 和单元测试

**Day 1-2**: 实现打卡管理 UseCase
- [ ] 检查已有 UseCase 实现
- [ ] 补充缺失的功能
- [ ] 优化代码质量

**已有 UseCase**:
- [x] CreateCheckinRuleUseCase
- [x] PerformCheckinUseCase
- [x] GetTodayCheckinsUseCase
- [x] UpdateCheckinRuleUseCase
- [x] DeleteCheckinRuleUseCase
- [x] CancelCheckinUseCase
- [x] GetCheckinHistoryUseCase
- [x] ReportMissCheckinUseCase

**Day 3-4**: 编写单元测试
- [ ] 为所有打卡 UseCase 编写单元测试
- [ ] 测试覆盖率 ≥ 90%

**Day 5**: 测试和优化
- [ ] 运行所有单元测试
- [ ] 优化代码质量
- [ ] 代码审查

#### Week 9: 重构路由和集成测试

**Day 1-2**: 重构打卡路由
- [ ] 阅读 `src/app/modules/checkin/routes.py`
- [ ] 阅读 `src/app/modules/user_checkin/routes.py`
- [ ] 阅读 `src/app/modules/community_checkin/routes.py`
- [ ] 重构所有打卡路由
- [ ] 保持 API 兼容性

**Day 3**: 启用聚合根和领域事件
- [ ] 在 UseCase 中使用 CheckinRuleAggregate
- [ ] 发布打卡领域事件
- [ ] 测试领域事件发布

**Day 4-5**: 测试和验证
- [ ] 运行所有打卡相关测试
- [ ] 运行集成测试
- [ ] 性能测试
- [ ] 代码审查

### 验收标准

- [ ] 打卡管理所有 UseCase 实现完整
- [ ] 打卡路由完全使用 UseCase
- [ ] CheckinRuleAggregate 正确使用
- [ ] 打卡领域事件正确发布
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

### 风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 打卡规则复杂 | 中 | 中 | 充分测试，文档说明 |
| 性能问题 | 中 | 高 | 性能测试，优化查询 |
| 数据一致性 | 低 | 高 | 事务管理，数据验证 |

---

## 阶段 5：事件管理模块迁移（1周）

### 时间安排

**Week 10**: 事件管理完整迁移

### 详细任务

#### Day 1-2: 完善 UseCase 实现

**任务**:
- [ ] 检查已有 UseCase 实现
- [ ] 补充缺失的功能
- [ ] 优化代码质量

**已有 UseCase**:
- [x] CreateEventUseCase
- [x] SupportEventUseCase
- [x] CloseEventUseCase
- [x] GetEventDetailsUseCase
- [x] GetCommunityEventsUseCase
- [x] GetPendingEventsUseCase
- [x] AddEventMessageUseCase
- [x] UpdateEventLocationUseCase

#### Day 3-4: 重构事件路由

**任务**:
- [ ] 阅读 `src/app/modules/events/routes.py`
- [ ] 重构事件路由
- [ ] 保持 API 兼容性

#### Day 5: 测试和验证

**任务**:
- [ ] 运行所有事件相关测试
- [ ] 运行集成测试
- [ ] 性能测试
- [ ] 代码审查

### 验收标准

- [ ] 事件管理所有 UseCase 实现完整
- [ ] 事件路由完全使用 UseCase
- [ ] CommunityEventAggregate 正确使用
- [ ] 事件领域事件正确发布
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

### 风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 事件逻辑复杂 | 中 | 中 | 充分测试，文档说明 |
| 实时性要求 | 中 | 高 | 性能测试，优化查询 |
| 数据一致性 | 低 | 高 | 事务管理，数据验证 |

---

## 阶段 6：监督管理模块迁移（1周）

### 时间安排

**Week 11**: 监督管理完整迁移

### 详细任务

#### Day 1-2: 完善 UseCase 实现

**任务**:
- [ ] 检查已有 UseCase 实现
- [ ] 补充缺失的功能
- [ ] 优化代码质量

**已有 UseCase**:
- [x] InviteSupervisorUseCase
- [x] SendInternalInvitationUseCase
- [x] GetSupervisedUsersUseCase
- [x] GetGuardiansUseCase
- [x] GetSupervisionRecordsUseCase
- [x] GetTodaySupervisionDataUseCase

#### Day 3-4: 重构监督路由

**任务**:
- [ ] 阅读 `src/app/modules/supervision/routes.py`
- [ ] 重构监督路由
- [ ] 保持 API 兼容性

#### Day 5: 测试和验证

**任务**:
- [ ] 运行所有监督相关测试
- [ ] 运行集成测试
- [ ] 性能测试
- [ ] 代码审查

### 验收标准

- [ ] 监督管理所有 UseCase 实现完整
- [ ] 监督路由完全使用 UseCase
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

### 风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 监督关系复杂 | 中 | 中 | 充分测试，文档说明 |
| 权限检查复杂 | 中 | 中 | 代码审查，单元测试 |

---

## 阶段 7：分享链接模块迁移（1周）

### 时间安排

**Week 12**: 分享链接完整迁移

### 详细任务

#### Day 1-2: 完善 UseCase 实现

**任务**:
- [ ] 检查已有 UseCase 实现
- [ ] 补充缺失的功能
- [ ] 优化代码质量

**已有 UseCase**:
- [x] CreateShareLinkUseCase
- [x] ResolveShareLinkUseCase

#### Day 3-4: 重构分享链接路由

**任务**:
- [ ] 阅读 `src/app/modules/share/routes.py`
- [ ] 重构分享链接路由
- [ ] 保持 API 兼容性

#### Day 5: 测试和验证

**任务**:
- [ ] 运行所有分享链接相关测试
- [ ] 运行集成测试
- [ ] 性能测试
- [ ] 代码审查

### 验收标准

- [ ] 分享链接所有 UseCase 实现完整
- [ ] 分享链接路由完全使用 UseCase
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

### 风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 分享逻辑复杂 | 低 | 低 | 充分测试，文档说明 |

---

## 阶段 8：其他模块迁移（1周）

### 时间安排

**Week 12（下半周）**: 其他模块完整迁移

### 详细任务

#### Day 1-2: 完善 UseCase 实现

**任务**:
- [ ] 检查已有 UseCase 实现
- [ ] 补充缺失的功能
- [ ] 优化代码质量

**已有 UseCase**:
- [x] SendVerificationCodeUseCase
- [x] GetEnvironmentsUseCase
- [x] CounterUseCase
- [x] UploadMediaUseCase
- [x] GetTrendDataUseCase
- [x] GetAbnormalUsersUseCase
- [x] GetCommunityStatsUseCase
- [x] GetPendingEventsUseCase
- [x] GetUserAbnormalityDetailUseCase

#### Day 3-4: 重构其他路由

**任务**:
- [ ] 阅读 `src/app/modules/sms/routes.py`
- [ ] 阅读 `src/app/modules/misc/routes.py`
- [ ] 阅读 `src/app/modules/community_dashboard/routes.py`
- [ ] 重构所有其他路由
- [ ] 保持 API 兼容性

#### Day 5: 测试和验证

**任务**:
- [ ] 运行所有测试
- [ ] 运行集成测试
- [ ] 性能测试
- [ ] 代码审查

### 验收标准

- [ ] 所有 UseCase 实现完整
- [ ] 所有路由完全使用 UseCase
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

### 风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 模块分散 | 低 | 低 | 充分测试，文档说明 |

---

## 阶段 9：清理旧代码（1周）

### 时间安排

**Week 13**: 清理所有旧代码

### 详细任务

#### Day 1-2: 删除旧服务类

**任务**:
- [ ] 删除 `wxcloudrun/user_service.py`
- [ ] 删除 `wxcloudrun/community_service.py`
- [ ] 删除 `wxcloudrun/checkin_rule_service.py`
- [ ] 删除 `wxcloudrun/checkin_record_service.py`
- [ ] 删除 `wxcloudrun/community_event_service.py`
- [ ] 删除 `wxcloudrun/community_staff_service.py`
- [ ] 删除 `wxcloudrun/medical_history_service.py`
- [ ] 删除 `wxcloudrun/user_transfer_service.py`

#### Day 3-4: 清理未使用的代码

**任务**:
- [ ] 删除未使用的导入
- [ ] 删除未使用的函数
- [ ] 删除未使用的类
- [ ] 代码格式化

#### Day 5: 更新文档和注释

**任务**:
- [ ] 更新架构文档
- [ ] 更新开发指南
- [ ] 更新代码注释
- [ ] 更新 README

### 验收标准

- [ ] 所有旧服务类已删除
- [ ] 无未使用的代码
- [ ] 代码风格统一
- [ ] 文档完整
- [ ] 所有测试通过

### 风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 误删代码 | 低 | 高 | 充分测试，代码审查 |
| 文档不完整 | 中 | 低 | 同步更新文档 |

---

## 阶段 10：聚合边界优化（2-3周）

### 时间安排

**Week 14-16**: 聚合边界优化

### 详细任务

#### Week 14: 拆分 User 聚合

**Day 1-2**: 提取 Medical 聚合
- [ ] 创建 UserMedicalHistory 聚合
- [ ] 更新相关 UseCase
- [ ] 测试和验证

**Day 3-4**: 提取 Supervision 聚合
- [ ] 创建 SupervisionRuleRelation 聚合
- [ ] 更新相关 UseCase
- [ ] 测试和验证

**Day 5**: 测试和验证
- [ ] 运行所有测试
- [ ] 性能测试
- [ ] 代码审查

#### Week 15: 拆分 Event 和 Checkin 聚合

**Day 1-2**: 提取 Event 聚合
- [ ] 创建 CommunityEvent 聚合
- [ ] 更新相关 UseCase
- [ ] 测试和验证

**Day 3-4**: 提取 Checkin 聚合
- [ ] 创建 CheckinRule 聚合
- [ ] 更新相关 UseCase
- [ ] 测试和验证

**Day 5**: 测试和验证
- [ ] 运行所有测试
- [ ] 性能测试
- [ ] 代码审查

#### Week 16: 优化 Community 聚合

**Day 1-3**: 优化 Community 聚合
- [ ] 分析 Community 聚合边界
- [ ] 拆分不必要的关联
- [ ] 优化加载策略
- [ ] 更新相关 UseCase

**Day 4-5**: 最终测试和验证
- [ ] 运行所有测试
- [ ] 性能测试
- [ ] 代码审查
- [ ] 文档更新

### 验收标准

- [ ] User 聚合边界清晰
- [ ] Community 聚合边界清晰
- [ ] 所有聚合根正确使用
- [ ] 所有测试通过
- [ ] 性能提升
- [ ] 代码审查通过

### 风险和缓解措施

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| 聚合拆分复杂 | 高 | 高 | 逐步拆分，充分测试 |
| 性能下降 | 中 | 高 | 性能测试，优化查询 |
| 数据不一致 | 低 | 高 | 事务管理，数据验证 |

---

## 里程碑和验收标准

### 里程碑 1：准备工作完成（Week 2）

**验收标准**:
- [ ] 所有核心 UseCase 都有单元测试
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] CI/CD 流水线配置完成
- [ ] 迁移环境准备就绪
- [ ] 团队评审通过

### 里程碑 2：核心模块迁移完成（Week 5）

**验收标准**:
- [ ] 认证、用户、社区模块迁移完成
- [ ] 所有核心 UseCase 实现完整
- [ ] 所有核心路由使用 UseCase
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

### 里程碑 3：主要业务模块迁移完成（Week 9）

**验收标准**:
- [ ] 认证、用户、社区、打卡模块迁移完成
- [ ] 所有主要 UseCase 实现完整
- [ ] 所有主要路由使用 UseCase
- [ ] 聚合根正确使用
- [ ] 领域事件正确发布
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

### 里程碑 4：所有模块迁移完成（Week 12）

**验收标准**:
- [ ] 所有模块迁移完成
- [ ] 所有 UseCase 实现完整
- [ ] 所有路由使用 UseCase
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

### 里程碑 5：旧代码清理完成（Week 13）

**验收标准**:
- [ ] 所有旧服务类已删除
- [ ] 无未使用的代码
- [ ] 代码风格统一
- [ ] 文档完整
- [ ] 所有测试通过

### 里程碑 6：聚合边界优化完成（Week 16）

**验收标准**:
- [ ] 聚合边界清晰
- [ ] 所有聚合根正确使用
- [ ] 所有测试通过
- [ ] 性能提升
- [ ] 代码审查通过
- [ ] DDD 迁移完成

---

## 资源分配

### 人力资源

| 角色 | 人数 | 职责 |
|------|------|------|
| 后端开发工程师 | 2-3人 | UseCase 实现、路由重构、测试编写 |
| 测试工程师 | 1人 | 测试设计、测试执行、测试报告 |
| 架构师 | 1人 | 架构设计、代码审查、技术咨询 |
| 项目经理 | 1人 | 项目管理、进度跟踪、风险管理 |

### 时间分配

| 阶段 | 工期 | 人力投入 | 关键路径 |
|------|------|---------|---------|
| 阶段 0 | 2周 | 2-3人 | 是 |
| 阶段 1 | 1周 | 2-3人 | 是 |
| 阶段 2 | 2周 | 2-3人 | 是 |
| 阶段 3 | 2周 | 2-3人 | 是 |
| 阶段 4 | 2周 | 2-3人 | 是 |
| 阶段 5 | 1周 | 1-2人 | 否 |
| 阶段 6 | 1周 | 1-2人 | 否 |
| 阶段 7 | 1周 | 1人 | 否 |
| 阶段 8 | 1周 | 1人 | 否 |
| 阶段 9 | 1周 | 2-3人 | 是 |
| 阶段 10 | 2-3周 | 2-3人 | 是 |

### 工具和环境

**开发工具**:
- IDE: VS Code / PyCharm
- 版本控制: Git
- 代码审查: GitHub PR

**测试工具**:
- 单元测试: pytest
- 集成测试: pytest + SQLAlchemy
- 性能测试: pytest-benchmark
- 代码覆盖率: pytest-cov

**CI/CD 工具**:
- GitHub Actions
- Codecov

---

## 沟通计划

### 每日站会

**时间**: 每天 10:00 AM
**时长**: 15 分钟
**参与者**: 全体开发团队
**内容**:
- 昨天完成了什么
- 今天计划做什么
- 遇到什么问题

### 每周评审会

**时间**: 每周五 3:00 PM
**时长**: 1 小时
**参与者**: 全体开发团队 + 项目经理 + 架构师
**内容**:
- 本周完成情况
- 下周计划
- 风险和问题
- 里程碑验收

### 里程碑评审会

**时间**: 每个里程碑完成后
**时长**: 2 小时
**参与者**: 全体开发团队 + 项目经理 + 架构师 + 利益相关者
**内容**:
- 里程碑完成情况
- 验收标准检查
- 经验总结
- 下一步计划

### 沟通渠道

**即时沟通**:
- Slack / 企业微信
- 频道: #ddd-migration

**文档共享**:
- GitHub Wiki
- 文档: `backend/docs/ddd-*`

**问题跟踪**:
- GitHub Issues
- 标签: ddd-migration

---

## 附录

### A. 迁移检查清单

**阶段 0：准备工作**
- [ ] 所有核心 UseCase 都有单元测试
- [ ] 单元测试覆盖率 ≥ 80%
- [ ] CI/CD 流水线配置完成
- [ ] 迁移环境准备就绪
- [ ] 团队评审通过

**阶段 1：认证模块**
- [ ] 认证模块所有 UseCase 实现完整
- [ ] 认证路由完全使用 UseCase
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

**阶段 2：用户管理模块**
- [ ] 用户管理所有 UseCase 实现完整
- [ ] 用户路由完全使用 UseCase
- [ ] UserAggregate 正确使用
- [ ] 用户领域事件正确发布
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

**阶段 3：社区管理模块**
- [ ] 社区管理所有 UseCase 实现完整
- [ ] 社区路由完全使用 UseCase
- [ ] CommunityAggregate 正确使用
- [ ] 社区领域事件正确发布
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

**阶段 4：打卡管理模块**
- [ ] 打卡管理所有 UseCase 实现完整
- [ ] 打卡路由完全使用 UseCase
- [ ] CheckinRuleAggregate 正确使用
- [ ] 打卡领域事件正确发布
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

**阶段 5：事件管理模块**
- [ ] 事件管理所有 UseCase 实现完整
- [ ] 事件路由完全使用 UseCase
- [ ] CommunityEventAggregate 正确使用
- [ ] 事件领域事件正确发布
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

**阶段 6：监督管理模块**
- [ ] 监督管理所有 UseCase 实现完整
- [ ] 监督路由完全使用 UseCase
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

**阶段 7：分享链接模块**
- [ ] 分享链接所有 UseCase 实现完整
- [ ] 分享链接路由完全使用 UseCase
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

**阶段 8：其他模块**
- [ ] 所有 UseCase 实现完整
- [ ] 所有路由完全使用 UseCase
- [ ] 所有测试通过
- [ ] 性能无明显下降
- [ ] 代码审查通过

**阶段 9：清理旧代码**
- [ ] 所有旧服务类已删除
- [ ] 无未使用的代码
- [ ] 代码风格统一
- [ ] 文档完整
- [ ] 所有测试通过

**阶段 10：聚合边界优化**
- [ ] 聚合边界清晰
- [ ] 所有聚合根正确使用
- [ ] 所有测试通过
- [ ] 性能提升
- [ ] 代码审查通过

### B. 风险登记册

| 风险ID | 风险描述 | 概率 | 影响 | 严重程度 | 缓解措施 | 负责人 | 状态 |
|--------|---------|------|------|---------|---------|--------|------|
| R001 | API 不兼容 | 低 | 高 | 高 | 充分测试，前端联调 | 开发团队 | 监控中 |
| R002 | 性能下降 | 中 | 高 | 高 | 性能测试，优化查询 | 开发团队 | 监控中 |
| R003 | 测试失败 | 低 | 中 | 中 | 充分测试，准备回滚 | 测试工程师 | 监控中 |
| R004 | 聚合拆分复杂 | 高 | 高 | 高 | 逐步拆分，充分测试 | 架构师 | 监控中 |
| R005 | 数据不一致 | 低 | 高 | 高 | 事务管理，数据验证 | 开发团队 | 监控中 |
| R006 | 代码审查不充分 | 中 | 中 | 中 | 强制代码审查，至少 2 人审核 | 架构师 | 监控中 |
| R007 | 文档不完整 | 中 | 低 | 低 | 同步更新文档，代码注释 | 开发团队 | 监控中 |
| R008 | 开发延期 | 低 | 低 | 低 | 合理安排时间，预留缓冲期 | 项目经理 | 监控中 |

### C. 联系人

| 角色 | 姓名 | 邮箱 | 电话 |
|------|------|------|------|
| 项目经理 | - | - | - |
| 架构师 | - | - | - |
| 后端开发工程师 | - | - | - |
| 测试工程师 | - | - | - |

---

**文档版本**: v1.0
**最后更新**: 2026-01-15
**维护者**: 开发团队