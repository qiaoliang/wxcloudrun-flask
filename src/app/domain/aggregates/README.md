# 聚合边界分析

## 当前问题

### User 聚合（过大）
User 聚合包含 20+ 个关联关系，违反了聚合应保持小而简单的原则。

**当前关联：**
- community → Community (多对一)
- checkin_rules → CheckinRule (一对多)
- checkin_records → CheckinRecord (一对多)
- solo_checkin_records → CheckinRecord (一对多，作为打卡用户)
- audit_logs → UserAuditLog (一对多)
- supervised_by_relations → SupervisionRuleRelation (一对多，作为被监督者)
- supervising_relations → SupervisionRuleRelation (一对多，作为监督者)
- staff_roles → CommunityStaff (一对多)
- community_applications → CommunityApplication (一对多，作为申请人)
- processed_applications → CommunityApplication (一对多，作为处理人)
- share_links → ShareLink (一对多)
- created_communities → Community (一对多，作为创建者)
- created_events → CommunityEvent (一对多)
- targeted_events → CommunityEvent (一对多，作为目标用户)
- supports → EventMessage (一对多)
- user_community_rules → UserCommunityRule (一对多)
- medical_histories → UserMedicalHistory (一对多)

### Community 聚合（较大）
Community 聚合包含 8+ 个关联关系。

**当前关联：**
- users → User (一对多)
- creator → User (多对一)
- manager → User (多对一)
- checkin_rules → CheckinRule (一对多)
- staff_members → CommunityStaff (一对多)
- community_checkin_rules → CommunityCheckinRule (一对多)
- applications → CommunityApplication (一对多)
- events → CommunityEvent (一对多)

### 实体与值对象边界不清
以下应该是值对象，但拥有独立主键被当作实体：
- SupervisionRuleRelation
- CommunityStaff
- CommunityApplication
- UserAuditLog
- ShareLink
- UserMedicalHistory
- UserCommunityRule
- UserDailyAbnormality
- ProfileViewLog

## DDD 聚合设计原则

1. **聚合根（Aggregate Root）**：聚合的唯一入口，通过聚合根访问聚合内的实体和值对象
2. **聚合边界**：聚合应该保持小而简单，只包含必须一起修改的实体
3. **一致性边界**：聚合内的所有实体必须保持事务一致性
4. **值对象**：没有身份标识，不可变的对象
5. **实体**：有身份标识，可变的对象

## 建议的聚合重构

### 方案 1：保持当前结构，优化加载策略
**优点**：改造成本低，风险小
**缺点**：仍然违反 DDD 原则，性能问题未解决

### 方案 2：拆分 User 聚合（推荐）
**User 聚合**（核心）：
- 基本信息（user_id, nickname, avatar_url, phone_number, role, status）
- 当前社区（community_id）

**Checkin 聚合**：
- CheckinRule（聚合根）
- CheckinRecord（实体）

**Event 聚合**：
- CommunityEvent（聚合根）
- EventMessage（实体）

**Supervision 聚合**：
- SupervisionRuleRelation（聚合根）

**Medical 聚合**：
- UserMedicalHistory（聚合根）

**优点**：符合 DDD 原则，性能更好
**缺点**：改造成本高，需要重构大量代码

### 方案 3：渐进式拆分
先拆分最独立的聚合，逐步推进：

**第一阶段**：
- 拆分 Medical 聚合（UserMedicalHistory）

**第二阶段**：
- 拆分 Supervision 聚合（SupervisionRuleRelation）

**第三阶段**：
- 拆分 Event 聚合（CommunityEvent, EventMessage）

**第四阶段**：
- 拆分 Checkin 聚合（CheckinRule, CheckinRecord）

**优点**：风险可控，逐步推进
**缺点**：周期较长

## 建议

考虑到项目的实际情况，建议采用**方案 3：渐进式拆分**。

**原因**：
1. 风险可控，可以逐步验证
2. 不影响现有功能
3. 可以根据实际情况调整优先级

**实施顺序**：
1. Medical 聚合（最独立，影响最小）
2. Supervision 聚合（相对独立）
3. Event 聚合（业务逻辑较多）
4. Checkin 聚合（核心功能，影响最大）