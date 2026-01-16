# 聚合边界优化方案

## 当前状态

### 测试覆盖率
- **当前覆盖率**: 56%
- **目标覆盖率**: 80%+
- **单元测试**: 546个通过，23个失败
- **集成测试**: 68个通过，10个失败

### 现有聚合设计

#### 1. CommunityAggregate
**聚合边界**:
- CommunityEntity（社区实体）
- CommunityCheckinRuleEntity（社区的打卡规则）
- CommunityEventEntity（社区的事件）

**业务不变性**:
- 社区必须有至少一个主管
- 社区成员数量不能超过限制（如果有）
- 社区打卡规则的启用/禁用必须符合业务规则
- 社区事件的处理必须符合权限要求

#### 2. UserAggregate
**聚合边界**:
- UserEntity（用户实体）
- CheckinRuleEntity（用户的打卡规则）
- CheckinRecordEntity（用户的打卡记录）

**业务不变性**:
- 用户必须至少有一个有效的联系方式（手机号或微信）
- 用户只能属于一个社区
- 用户的打卡规则必须符合其角色权限

## 识别的问题

### 1. 聚合边界重叠
- UserAggregate中的CheckinRuleEntity和CommunityAggregate中的CommunityCheckinRuleEntity存在概念重叠
- 用户打卡规则和社区打卡规则之间的关系不清晰

### 2. 聚合边界过大
- CommunityAggregate包含了CommunityEventEntity，但事件的处理可能更适合作为独立的聚合
- UserAggregate包含了CheckinRecordEntity，但打卡记录可能更适合作为独立的聚合

### 3. 聚合边界不清晰
- UserCommunityRuleEntity（用户社区规则关联）没有明确的聚合归属
- CommunityStaffEntity（社区工作人员）没有明确的聚合归属

## 优化方案

### 方案1：拆分CommunityEventAggregate
将CommunityEventEntity从CommunityAggregate中分离出来，创建独立的CommunityEventAggregate。

**优点**:
- 聚合边界更清晰
- 事件处理逻辑更独立
- 更符合单一职责原则

**缺点**:
- 需要修改现有代码
- 可能影响性能

### 方案2：引入UserCommunityRuleAggregate
将UserCommunityRuleEntity从UserAggregate和CommunityAggregate中分离出来，创建独立的UserCommunityRuleAggregate。

**优点**:
- 解决聚合边界重叠问题
- 用户社区规则关联逻辑更清晰

**缺点**:
- 增加聚合数量
- 可能增加复杂性

### 方案3：简化聚合边界
移除一些实体，简化聚合边界。

**优点**:
- 减少复杂性
- 更容易维护

**缺点**:
- 可能失去一些业务不变性保证

## 推荐方案

采用**方案1 + 方案2**的组合：

1. **拆分CommunityEventAggregate**
   - 将CommunityEventEntity从CommunityAggregate中分离
   - 创建独立的CommunityEventAggregate
   - 通过事件ID关联到CommunityAggregate

2. **引入UserCommunityRuleAggregate**
   - 将UserCommunityRuleEntity作为独立聚合
   - 通过用户ID和社区ID关联到UserAggregate和CommunityAggregate

3. **保持UserAggregate和CommunityAggregate的边界**
   - UserAggregate：UserEntity + CheckinRecordEntity
   - CommunityAggregate：CommunityEntity + CommunityCheckinRuleEntity

## 实施步骤

### 阶段1：创建新的聚合
1. 创建CommunityEventAggregate
2. 创建UserCommunityRuleAggregate

### 阶段2：重构现有聚合
1. 从CommunityAggregate中移除CommunityEventEntity
2. 从UserAggregate中移除CheckinRuleEntity（如果需要）

### 阶段3：更新Repository和UseCase
1. 更新Repository接口
2. 更新UseCase实现

### 阶段4：更新测试
1. 更新单元测试
2. 更新集成测试

### 阶段5：验证
1. 运行测试套件
2. 验证业务不变性
3. 性能测试

## 预期结果

- 聚合边界更清晰
- 代码更易维护
- 测试覆盖率提升到80%+
- 业务不变性得到更好的保证