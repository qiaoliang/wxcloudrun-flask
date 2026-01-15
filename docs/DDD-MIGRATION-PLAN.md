# DDD 迁移计划

**版本**: v1.0
**创建日期**: 2026-01-15
**目标**: 完成 SafeGuard 后端从混合架构到纯 DDD 架构的迁移

---

## 目录

1. [现状分析](#现状分析)
2. [迁移目标](#迁移目标)
3. [迁移原则](#迁移原则)
4. [迁移阶段](#迁移阶段)
5. [详细执行计划](#详细执行计划)
6. [风险评估](#风险评估)
7. [回滚策略](#回滚策略)

---

## 现状分析

### 当前架构状态

**已完成**（阶段 1-7，2026-01-11）：
- ✅ 应用服务层（79个 UseCase）
- ✅ 领域层（6个实体、6个值对象、4个聚合根）
- ✅ 仓储模式（17个接口 + 17个实现）
- ✅ 领域事件系统（EventBus + 事件处理器）
- ✅ 基础设施层（RepositoryFactory + SQLAlchemy 仓储）

**存在的问题**：
- ❌ 新旧架构并存：35处路由仍使用 `wxcloudrun.*_Service`
- ❌ 聚合根未实际使用：4个聚合根定义但未被调用
- ❌ 领域事件未发布：EventBus 实现但无实际调用
- ❌ 应用用例使用率低：68个 UseCase 仅少数被使用

### 技术债务统计

| 类型 | 数量 | 优先级 |
|------|------|--------|
| 需要重构的路由 | 35处 | 高 |
| 未使用的聚合根 | 4个 | 中 |
| 未使用的领域事件 | 10+个 | 中 |
| 旧服务类 | 8个 | 高 |
| 硬编码常量 | 50+处 | 低 |

---

## 迁移目标

### 主要目标

1. **完全迁移到 DDD 架构**
   - 所有路由使用应用用例（UseCase）
   - 删除所有 `wxcloudrun.*_Service` 旧服务
   - 启用聚合根和领域事件

2. **提升代码质量**
   - 统一代码风格和架构模式
   - 提高可测试性和可维护性
   - 减少技术债务

3. **确保系统稳定性**
   - 零生产事故
   - 所有测试通过
   - 性能无明显下降

### 次要目标

- 优化聚合边界（拆分过大的 User 聚合）
- 统一常量定义
- 完善文档和注释

---

## 迁移原则

### 1. 渐进式迁移

**原则**: 逐步迁移，每次只修改一个模块，确保系统稳定运行。

**实施**:
- 按模块优先级分批迁移
- 每个模块迁移后立即测试
- 发现问题立即回滚

### 2. 测试先行

**原则**: 在修改代码前，先确保有充分的测试覆盖。

**实施**:
- 为旧服务编写集成测试（如有必要）
- 为新用例编写单元测试
- 确保测试覆盖率 ≥ 80%

### 3. 向后兼容

**原则**: 在迁移过程中保持 API 兼容性。

**实施**:
- 不改变 API 接口签名
- 保持响应格式一致
- 使用特性开关控制新旧逻辑

### 4. 持续集成

**原则**: 每次提交都运行所有测试，确保质量。

**实施**:
- 使用 CI/CD 管道
- 自动运行单元测试和集成测试
- 代码审查必须通过

---

## 迁移阶段

### 阶段 0：准备工作（1-2周）

**目标**: 为迁移做好准备，降低风险。

**任务**:
- [ ] 完成所有应用用例的实现
- [ ] 为所有 UseCase 编写单元测试
- [ ] 为旧服务编写集成测试（如有必要）
- [ ] 创建迁移分支策略
- [ ] 设置 CI/CD 管道
- [ ] 准备回滚方案

**产出**:
- 完整的测试套件
- CI/CD 配置
- 迁移分支计划

---

### 阶段 1：认证模块迁移（1周）

**优先级**: ⭐⭐⭐⭐⭐ 最高

**原因**: 认证是所有功能的基础，必须最先迁移。

**影响范围**:
- `src/app/modules/auth/routes.py`
- `wxcloudrun/user_service.py` (部分方法)

**迁移任务**:
- [ ] 确保所有认证 UseCase 已实现
- [ ] 为认证 UseCase 编写单元测试
- [ ] 重构 `auth/routes.py` 使用 UseCase
- [ ] 运行所有认证相关测试
- [ ] 验证登录、刷新 Token、登出功能
- [ ] 性能测试（登录响应时间 < 500ms）

**验证标准**:
- ✅ 所有认证测试通过
- ✅ 性能无明显下降
- ✅ 前端无需修改

---

### 阶段 2：用户管理模块迁移（2周）

**优先级**: ⭐⭐⭐⭐ 高

**原因**: 用户管理是核心功能，使用频率高。

**影响范围**:
- `src/app/modules/user/routes.py`
- `wxcloudrun/user_service.py`
- `wxcloudrun/medical_history_service.py`

**迁移任务**:
- [ ] 实现所有用户管理 UseCase
  - [ ] UpdateProfileUseCase
  - [ ] ChangePasswordUseCase
  - [ ] UploadAvatarUseCase
  - [ ] SearchUsersUseCase
  - [ ] GetUserDetailsUseCase
- [ ] 为所有用户 UseCase 编写单元测试
- [ ] 重构 `user/routes.py` (826行代码)
- [ ] 启用 UserAggregate（聚合根）
- [ ] 发布用户领域事件（UserCreatedEvent, UserUpdatedEvent）
- [ ] 运行所有用户相关测试
- [ ] 用户资料更新功能验证

**验证标准**:
- ✅ 所有用户测试通过
- ✅ 用户领域事件正确发布
- ✅ 聚合根正确使用
- ✅ 旧服务标记为废弃

---

### 阶段 3：社区管理模块迁移（2周）

**优先级**: ⭐⭐⭐⭐ 高

**原因**: 社区管理是核心功能，业务逻辑复杂。

**影响范围**:
- `src/app/modules/community/routes.py`
- `src/app/modules/community/*.py` (6个子模块)
- `wxcloudrun/community_service.py`
- `wxcloudrun/community_staff_service.py`

**迁移任务**:
- [ ] 实现所有社区管理 UseCase
  - [ ] CreateCommunityUseCase ✅ (已实现)
  - [ ] JoinCommunityUseCase ✅ (已实现)
  - [ ] LeaveCommunityUseCase ✅ (已实现)
  - [ ] GetCommunityDetailsUseCase ✅ (已实现)
  - [ ] UpdateCommunityUseCase ✅ (已实现)
  - [ ] DeleteCommunityUseCase ✅ (已实现)
  - [ ] SearchCommunityUseCase ✅ (已实现)
  - [ ] ListCommunityUsersUseCase ✅ (已实现)
- [ ] 为所有社区 UseCase 编写单元测试
- [ ] 重构 `community/routes.py`
- [ ] 重构 `community/community_*.py` (6个子模块)
- [ ] 启用 CommunityAggregate（聚合根）
- [ ] 发布社区领域事件
- [ ] 运行所有社区相关测试

**验证标准**:
- ✅ 所有社区测试通过
- ✅ 社区领域事件正确发布
- ✅ 聚合根正确使用
- ✅ 社区成员管理功能正常

---

### 阶段 4：打卡管理模块迁移（2周）

**优先级**: ⭐⭐⭐ 中

**原因**: 打卡是核心功能，但相对独立。

**影响范围**:
- `src/app/modules/checkin/routes.py`
- `src/app/modules/user_checkin/routes.py`
- `src/app/modules/community_checkin/routes.py`
- `wxcloudrun/checkin_rule_service.py`
- `wxcloudrun/checkin_record_service.py`

**迁移任务**:
- [ ] 实现所有打卡 UseCase
  - [ ] CreateCheckinRuleUseCase ✅ (已实现)
  - [ ] PerformCheckinUseCase ✅ (已实现)
  - [ ] GetTodayCheckinsUseCase ✅ (已实现)
  - [ ] UpdateCheckinRuleUseCase ✅ (已实现)
  - [ ] DeleteCheckinRuleUseCase ✅ (已实现)
  - [ ] CancelCheckinUseCase ✅ (已实现)
  - [ ] GetCheckinHistoryUseCase ✅ (已实现)
  - [ ] ReportMissCheckinUseCase ✅ (已实现)
- [ ] 为所有打卡 UseCase 编写单元测试
- [ ] 重构所有打卡路由
- [ ] 启用 CheckinRuleAggregate（聚合根）
- [ ] 发布打卡领域事件
- [ ] 运行所有打卡相关测试

**验证标准**:
- ✅ 所有打卡测试通过
- ✅ 打卡领域事件正确发布
- ✅ 打卡规则和记录功能正常

---

### 阶段 5：事件管理模块迁移（1周）

**优先级**: ⭐⭐⭐ 中

**原因**: 事件管理是社区核心功能，相对独立。

**影响范围**:
- `src/app/modules/events/routes.py`
- `wxcloudrun/community_event_service.py`

**迁移任务**:
- [ ] 实现所有事件 UseCase
  - [ ] CreateEventUseCase ✅ (已实现)
  - [ ] SupportEventUseCase ✅ (已实现)
  - [ ] CloseEventUseCase ✅ (已实现)
  - [ ] GetEventDetailsUseCase ✅ (已实现)
  - [ ] GetCommunityEventsUseCase ✅ (已实现)
  - [ ] GetPendingEventsUseCase ✅ (已实现)
  - [ ] AddEventMessageUseCase ✅ (已实现)
  - [ ] UpdateEventLocationUseCase ✅ (已实现)
- [ ] 为所有事件 UseCase 编写单元测试
- [ ] 重构 `events/routes.py`
- [ ] 启用 CommunityEventAggregate（聚合根）
- [ ] 发布事件领域事件
- [ ] 运行所有事件相关测试

**验证标准**:
- ✅ 所有事件测试通过
- ✅ 事件领域事件正确发布
- ✅ 事件创建、支持、关闭功能正常

---

### 阶段 6：监督管理模块迁移（1周）

**优先级**: ⭐⭐ 中

**原因**: 监督管理是重要功能，但相对独立。

**影响范围**:
- `src/app/modules/supervision/routes.py`
- `wxcloudrun/user_service.py` (监督相关方法)

**迁移任务**:
- [ ] 实现所有监督 UseCase
  - [ ] InviteSupervisorUseCase ✅ (已实现)
  - [ ] SendInternalInvitationUseCase ✅ (已实现)
  - [ ] GetSupervisedUsersUseCase ✅ (已实现)
  - [ ] GetGuardiansUseCase ✅ (已实现)
  - [ ] GetSupervisionRecordsUseCase ✅ (已实现)
  - [ ] GetTodaySupervisionDataUseCase ✅ (已实现)
- [ ] 为所有监督 UseCase 编写单元测试
- [ ] 重构 `supervision/routes.py`
- [ ] 运行所有监督相关测试

**验证标准**:
- ✅ 所有监督测试通过
- ✅ 监督邀请和关系管理功能正常

---

### 阶段 7：分享链接模块迁移（1周）

**优先级**: ⭐⭐ 低

**原因**: 分享链接是辅助功能，使用频率较低。

**影响范围**:
- `src/app/modules/share/routes.py`
- `wxcloudrun/user_service.py` (分享相关方法)
- `wxcloudrun/checkin_rule_service.py` (分享相关方法)

**迁移任务**:
- [ ] 实现所有分享 UseCase
  - [ ] CreateShareLinkUseCase ✅ (已实现)
  - [ ] ResolveShareLinkUseCase ✅ (已实现)
- [ ] 为所有分享 UseCase 编写单元测试
- [ ] 重构 `share/routes.py`
- [ ] 运行所有分享相关测试

**验证标准**:
- ✅ 所有分享测试通过
- ✅ 分享链接创建和解析功能正常

---

### 阶段 8：其他模块迁移（1周）

**优先级**: ⭐ 低

**原因**: 其他模块功能简单，影响小。

**影响范围**:
- `src/app/modules/sms/routes.py`
- `src/app/modules/misc/routes.py`
- `src/app/modules/community_dashboard/routes.py`

**迁移任务**:
- [ ] 实现所有剩余 UseCase
  - [ ] SendVerificationCodeUseCase ✅ (已实现)
  - [ ] GetEnvironmentsUseCase ✅ (已实现)
  - [ ] CounterUseCase ✅ (已实现)
  - [ ] UploadMediaUseCase ✅ (已实现)
  - [ ] GetTrendDataUseCase ✅ (已实现)
  - [ ] GetAbnormalUsersUseCase ✅ (已实现)
  - [ ] GetCommunityStatsUseCase ✅ (已实现)
  - [ ] GetPendingEventsUseCase ✅ (已实现)
  - [ ] GetUserAbnormalityDetailUseCase ✅ (已实现)
- [ ] 为所有剩余 UseCase 编写单元测试
- [ ] 重构所有剩余路由
- [ ] 运行所有测试

**验证标准**:
- ✅ 所有测试通过
- ✅ 所有功能正常

---

### 阶段 9：清理旧代码（1周）

**优先级**: ⭐⭐⭐⭐ 高

**原因**: 清理旧代码，减少技术债务。

**任务**:
- [ ] 删除所有 `wxcloudrun.*_Service` 旧服务类
- [ ] 删除未使用的导入和代码
- [ ] 更新文档和注释
- [ ] 统一常量定义
- [ ] 代码格式化和优化

**验证标准**:
- ✅ 无旧服务引用
- ✅ 代码风格统一
- ✅ 文档完整

---

### 阶段 10：聚合边界优化（2-3周）

**优先级**: ⭐⭐⭐ 中

**原因**: 优化聚合边界，符合 DDD 最佳实践。

**任务**:
- [ ] 拆分 User 聚合（20+ 关联关系）
  - [ ] 提取 Medical 聚合（UserMedicalHistory）
  - [ ] 提取 Supervision 聚合（SupervisionRuleRelation）
  - [ ] 提取 Event 聚合（CommunityEvent）
  - [ ] 提取 Checkin 聚合（CheckinRule, CheckinRecord）
- [ ] 优化 Community 聚合（8+ 关联关系）
- [ ] 更新所有相关 UseCase
- [ ] 运行所有测试

**验证标准**:
- ✅ 所有测试通过
- ✅ 聚合边界清晰
- ✅ 性能提升

---

## 详细执行计划

### 每周工作安排

#### 第 1-2 周：准备工作

**Week 1**:
- [ ] 完成 20 个核心 UseCase 的单元测试
- [ ] 设置 CI/CD 管道
- [ ] 创建迁移分支 `feature/ddd-migration-phase-1`

**Week 2**:
- [ ] 完成所有 UseCase 的单元测试
- [ ] 编写集成测试（如有必要）
- [ ] 代码审查和测试

#### 第 3 周：认证模块迁移

**Day 1-2**: 实现/完善认证 UseCase
**Day 3-4**: 重构认证路由
**Day 5**: 测试和验证

#### 第 4-5 周：用户管理模块迁移

**Week 4**:
- [ ] 实现用户管理 UseCase
- [ ] 编写单元测试

**Week 5**:
- [ ] 重构用户路由
- [ ] 启用聚合根和领域事件
- [ ] 测试和验证

#### 第 6-7 周：社区管理模块迁移

**Week 6**:
- [ ] 实现社区管理 UseCase
- [ ] 编写单元测试

**Week 7**:
- [ ] 重构社区路由
- [ ] 重构社区子模块
- [ ] 启用聚合根和领域事件
- [ ] 测试和验证

#### 第 8-9 周：打卡管理模块迁移

**Week 8**:
- [ ] 实现打卡 UseCase
- [ ] 编写单元测试

**Week 9**:
- [ ] 重构打卡路由
- [ ] 启用聚合根和领域事件
- [ ] 测试和验证

#### 第 10 周：事件管理模块迁移

**Week 10**:
- [ ] 实现事件 UseCase
- [ ] 重构事件路由
- [ ] 启用聚合根和领域事件
- [ ] 测试和验证

#### 第 11 周：监督管理模块迁移

**Week 11**:
- [ ] 实现监督 UseCase
- [ ] 重构监督路由
- [ ] 测试和验证

#### 第 12 周：分享链接和其他模块迁移

**Week 12**:
- [ ] 实现分享 UseCase
- [ ] 重构分享路由
- [ ] 重构其他路由
- [ ] 测试和验证

#### 第 13 周：清理旧代码

**Week 13**:
- [ ] 删除旧服务类
- [ ] 清理未使用的代码
- [ ] 更新文档

#### 第 14-16 周：聚合边界优化

**Week 14-16**:
- [ ] 拆分 User 聚合
- [ ] 优化 Community 聚合
- [ ] 测试和验证

---

## 风险评估

### 高风险项

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 生产环境故障 | 高 | 低 | 充分测试，分阶段发布，准备回滚方案 |
| 性能下降 | 高 | 中 | 性能测试，优化查询，使用缓存 |
| 数据不一致 | 高 | 低 | 事务管理，数据验证，集成测试 |
| 前端兼容性 | 中 | 中 | API 兼容性测试，前端联调 |

### 中风险项

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 测试覆盖不足 | 中 | 中 | 强制测试覆盖率 ≥ 80% |
| 代码审查不充分 | 中 | 中 | 强制代码审查，至少 2 人审核 |
| 文档不完整 | 低 | 高 | 同步更新文档，代码注释 |

### 低风险项

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 开发延期 | 低 | 中 | 合理安排时间，预留缓冲期 |
| 人员变动 | 低 | 低 | 知识共享，代码注释 |

---

## 回滚策略

### 回滚触发条件

1. **生产环境故障**
   - 任何影响用户体验的故障
   - 数据不一致或丢失
   - 性能严重下降（> 50%）

2. **测试失败**
   - 关键测试用例失败
   - 测试覆盖率 < 80%
   - 集成测试失败

3. **性能问题**
   - API 响应时间 > 2s
   - 数据库查询时间 > 1s
   - 内存泄漏

### 回滚步骤

1. **紧急回滚**（5分钟内）
   ```bash
   # 回滚到上一个稳定版本
   git revert <commit-hash>
   # 或
   git checkout <stable-branch>
   ```

2. **部分回滚**（30分钟内）
   ```bash
   # 回滚特定模块
   git revert <module-commits>
   # 恢复旧服务
   git checkout <stable-branch> -- src/wxcloudrun/
   ```

3. **完整回滚**（2小时内）
   ```bash
   # 回滚整个迁移
   git reset --hard <stable-branch>
   # 重新部署
   ./deploy.sh
   ```

### 回滚验证

- [ ] 所有测试通过
- [ ] 生产环境功能正常
- [ ] 性能指标正常
- [ ] 用户反馈良好

---

## 成功标准

### 技术指标

- ✅ 所有测试通过（单元测试 + 集成测试）
- ✅ 测试覆盖率 ≥ 80%
- ✅ 代码审查通过率 100%
- ✅ 性能无明显下降（< 10%）
- ✅ 零生产事故

### 架构指标

- ✅ 所有路由使用 UseCase
- ✅ 删除所有旧服务类
- ✅ 启用所有聚合根
- ✅ 发布所有领域事件
- ✅ 代码风格统一

### 业务指标

- ✅ 所有功能正常
- ✅ 用户体验无变化
- ✅ 无数据丢失或不一致

---

## 附录

### A. 模块优先级矩阵

| 模块 | 业务重要性 | 技术复杂度 | 依赖关系 | 优先级 |
|------|-----------|-----------|---------|--------|
| 认证 | ⭐⭐⭐⭐⭐ | ⭐⭐ | 无 | P0 |
| 用户管理 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 认证 | P0 |
| 社区管理 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 用户 | P1 |
| 打卡管理 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 用户、社区 | P1 |
| 事件管理 | ⭐⭐⭐⭐ | ⭐⭐⭐ | 社区 | P2 |
| 监督管理 | ⭐⭐⭐ | ⭐⭐⭐ | 用户 | P2 |
| 分享链接 | ⭐⭐ | ⭐⭐ | 用户、打卡 | P3 |
| 其他 | ⭐ | ⭐ | 无 | P3 |

### B. UseCase 清单

#### 认证模块（3个）
- [x] LoginWeChatUseCase
- [x] RefreshTokenUseCase
- [x] LogoutUseCase

#### 用户管理模块（5个）
- [x] UpdateProfileUseCase
- [x] ChangePasswordUseCase
- [x] UploadAvatarUseCase
- [x] SearchUsersUseCase
- [ ] GetUserDetailsUseCase

#### 社区管理模块（8个）
- [x] CreateCommunityUseCase
- [x] JoinCommunityUseCase
- [x] LeaveCommunityUseCase
- [x] GetCommunityDetailsUseCase
- [x] UpdateCommunityUseCase
- [x] DeleteCommunityUseCase
- [x] SearchCommunityUseCase
- [x] ListCommunityUsersUseCase

#### 打卡管理模块（8个）
- [x] CreateCheckinRuleUseCase
- [x] PerformCheckinUseCase
- [x] GetTodayCheckinsUseCase
- [x] UpdateCheckinRuleUseCase
- [x] DeleteCheckinRuleUseCase
- [x] CancelCheckinUseCase
- [x] GetCheckinHistoryUseCase
- [x] ReportMissCheckinUseCase

#### 事件管理模块（8个）
- [x] CreateEventUseCase
- [x] SupportEventUseCase
- [x] CloseEventUseCase
- [x] GetEventDetailsUseCase
- [x] GetCommunityEventsUseCase
- [x] GetPendingEventsUseCase
- [x] AddEventMessageUseCase
- [x] UpdateEventLocationUseCase

#### 监督管理模块（6个）
- [x] InviteSupervisorUseCase
- [x] SendInternalInvitationUseCase
- [x] GetSupervisedUsersUseCase
- [x] GetGuardiansUseCase
- [x] GetSupervisionRecordsUseCase
- [x] GetTodaySupervisionDataUseCase

#### 分享链接模块（2个）
- [x] CreateShareLinkUseCase
- [x] ResolveShareLinkUseCase

#### 其他模块（9个）
- [x] SendVerificationCodeUseCase
- [x] GetEnvironmentsUseCase
- [x] CounterUseCase
- [x] UploadMediaUseCase
- [x] GetTrendDataUseCase
- [x] GetAbnormalUsersUseCase
- [x] GetCommunityStatsUseCase
- [x] GetPendingEventsUseCase
- [x] GetUserAbnormalityDetailUseCase

**总计**: 68 个 UseCase，67 个已实现，1 个待实现

### C. 路由迁移清单

| 模块 | 路由文件 | 旧服务引用 | 优先级 |
|------|---------|-----------|--------|
| 认证 | auth/routes.py | UserService | P0 |
| 用户管理 | user/routes.py | UserService, MedicalHistoryService, CommunityEventService | P0 |
| 社区管理 | community/routes.py | CommunityService, UserService, CommunityStaffService | P1 |
| 打卡管理 | checkin/routes.py | UserService, CheckinRuleService, CheckinRecordService | P1 |
| 用户打卡 | user_checkin/routes.py | UserService, CheckinRuleService | P1 |
| 社区打卡 | community_checkin/routes.py | CommunityService, CheckinRuleService | P1 |
| 事件管理 | events/routes.py | CommunityEventService, CommunityService | P2 |
| 监督管理 | supervision/routes.py | UserService, CheckinRuleService, CheckinRecordService | P2 |
| 分享链接 | share/routes.py | UserService, CheckinRuleService | P3 |
| 短信验证 | sms/routes.py | 无 | P3 |
| 杂项 | misc/routes.py | 无 | P3 |
| 社区仪表板 | community_dashboard/routes.py | 无 | P3 |

**总计**: 12 个路由文件，35 处旧服务引用

### D. 旧服务类清单

| 服务类 | 文件路径 | 引用次数 | 优先级 |
|--------|---------|---------|--------|
| UserService | wxcloudrun/user_service.py | 15+ | P0 |
| CommunityService | wxcloudrun/community_service.py | 10+ | P1 |
| CheckinRuleService | wxcloudrun/checkin_rule_service.py | 5+ | P1 |
| CheckinRecordService | wxcloudrun/checkin_record_service.py | 3+ | P1 |
| CommunityEventService | wxcloudrun/community_event_service.py | 5+ | P2 |
| CommunityStaffService | wxcloudrun/community_staff_service.py | 3+ | P1 |
| MedicalHistoryService | wxcloudrun/medical_history_service.py | 4+ | P0 |
| UserTransferService | wxcloudrun/user_transfer_service.py | 1+ | P2 |

**总计**: 8 个旧服务类

---

**文档版本**: v1.0
**最后更新**: 2026-01-15
**维护者**: 开发团队