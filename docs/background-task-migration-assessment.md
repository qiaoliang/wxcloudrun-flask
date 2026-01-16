# 后台任务迁移方案评估

## 概述

本文档评估将后台任务从当前的三层架构迁移到DDD架构的方案。

## 当前后台任务分析

### 任务列表

| 任务ID | 任务名称 | 执行频率 | 当前状态 | 代码位置 |
|--------|----------|----------|----------|----------|
| 1 | 异常值计算 | 每分钟 | 使用AbnormalityCalculator类 | app/__init__.py |
| 2 | 全天规则检查 | 每天0点 | 使用background_tasks.py函数 | app/__init__.py + wxcloudrun/background_tasks.py |
| 3 | 缺失打卡检查 | 每5分钟 | 使用background_tasks.py函数 | app/__init__.py + wxcloudrun/background_tasks.py |
| 4 | 邀请过期检查 | 每天0:30 | 使用Repository | app/__init__.py |

### 当前架构问题

1. **直接使用db.session**
   - `background_tasks.py` 中大量使用 `db.session.get()` 和 `db.session.execute()`
   - 不符合DDD的Repository模式

2. **业务逻辑分散**
   - 打卡逻辑分散在多个函数中
   - 缺少统一的业务规则管理

3. **代码重复**
   - 个人规则和社区规则的处理逻辑相似但分别实现
   - 缺少抽象层

4. **事务管理不一致**
   - 部分使用 `with transaction()` 上下文管理器
   - 部分直接使用 `db.session.commit()`

## 迁移方案评估

### 方案1：完全迁移到UseCase（推荐）

#### 架构设计

```
后台任务调度器
    ↓
后台任务UseCase层
    ↓
Repository层
    ↓
数据库
```

#### 需要创建的UseCase

1. **CheckMissedCheckinUseCase**
   - 检查并标记未打卡记录
   - 支持个人规则和社区规则
   - 支持全天规则和常规规则

2. **UpdateAbnormalityValuesUseCase**
   - 封装现有的AbnormalityCalculator
   - 提供统一的接口

3. **CheckExpiredInvitationsUseCase**
   - 检查并更新过期邀请
   - 已经使用Repository，只需封装

#### 优点
- 完全符合DDD架构
- 业务逻辑集中管理
- 易于测试和维护
- 代码复用性高

#### 缺点
- 工作量大（预计3-5天）
- 需要重构大量代码
- 可能引入新的bug

#### 适用性
- 适合长期维护的项目
- 适合需要频繁修改的业务逻辑

### 方案2：部分迁移到UseCase

#### 架构设计

```
后台任务调度器
    ↓
部分UseCase + 直接Repository访问
    ↓
Repository层
    ↓
数据库
```

#### 迁移策略

1. **优先迁移复杂任务**
   - 缺失打卡检查（最复杂）
   - 全天规则检查

2. **保持简单任务现状**
   - 异常值计算（已经封装在类中）
   - 邀请过期检查（已经使用Repository）

#### 优点
- 工作量适中（预计2-3天）
- 风险较低
- 可以逐步迁移

#### 缺点
- 代码风格不统一
- 部分代码仍不符合DDD

#### 适用性
- 适合时间有限的项目
- 适合需要快速见效的场景

### 方案3：仅迁移到Repository

#### 架构设计

```
后台任务调度器
    ↓
直接使用Repository（替换db.session）
    ↓
数据库
```

#### 迁移策略

1. **替换所有db.session调用**
   - `db.session.get(User, user_id)` → `user_repository.find_by_id(user_id)`
   - `db.session.execute(select(...))` → `repository.find_by_xxx(...)`

2. **保持函数结构不变**
   - 不创建新的UseCase
   - 只修改数据访问层

#### 优点
- 工作量最小（预计1-2天）
- 风险最低
- 改动范围小

#### 缺点
- 不符合完整的DDD架构
- 业务逻辑仍然分散
- 难以测试

#### 适用性
- 适合短期项目
- 适合快速修复问题

## 推荐方案

### 推荐方案：方案2（部分迁移到UseCase）

#### 理由

1. **平衡了工作量与收益**
   - 迁移最复杂的任务（缺失打卡检查）
   - 保持简单任务现状

2. **风险可控**
   - 可以逐步验证每个迁移
   - 出现问题容易回滚

3. **符合当前项目状态**
   - 其他模块已经部分迁移到UseCase
   - 保持架构一致性

#### 实施步骤

**阶段1：迁移缺失打卡检查（优先级：高）**
1. 创建 `CheckMissedCheckinUseCase`
2. 将 `_process_missed_for_today` 和 `_process_community_missed_for_today` 的逻辑迁移到UseCase
3. 更新 `background_tasks.py` 调用新的UseCase
4. 编写单元测试

**阶段2：迁移全天规则检查（优先级：中）**
1. 创建 `CheckDailyCheckinUseCase`
2. 将 `daily_check` 的逻辑迁移到UseCase
3. 更新 `background_tasks.py` 调用新的UseCase
4. 编写单元测试

**阶段3：保持简单任务现状（优先级：低）**
1. 保持 `AbnormalityCalculator` 不变
2. 保持邀请过期检查不变（已经使用Repository）
3. 只需要确保它们使用Repository而不是db.session

#### 预期收益

1. **代码质量提升**
   - 业务逻辑更清晰
   - 更易测试

2. **维护性提升**
   - 减少代码重复
   - 统一错误处理

3. **架构一致性**
   - 与其他模块保持一致
   - 符合DDD最佳实践

## 总结

后台任务迁移是一个重要的架构改进，但需要平衡工作量与收益。

**推荐采用方案2（部分迁移到UseCase）**，理由如下：
1. 工作量适中（2-3天）
2. 风险可控
3. 能够获得主要的架构改进收益

**不建议采用方案1（完全迁移）**，因为：
1. 工作量过大（3-5天）
2. 风险较高
3. 收益与投入不成正比

**不建议采用方案3（仅迁移Repository）**，因为：
1. 不符合完整的DDD架构
2. 无法解决业务逻辑分散的问题
3. 长期维护成本高

## 下一步行动

1. 与团队讨论并确认迁移方案
2. 制定详细的迁移计划
3. 开始实施阶段1（迁移缺失打卡检查）
4. 逐步完成其他阶段