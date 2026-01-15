# DDD 迁移回滚方案

## 概述

本文档定义了 DDD 迁移过程中的回滚策略和步骤，确保在出现问题时能够快速、安全地回滚到稳定状态。

## 回滚触发条件

### 立即回滚（P0 - 严重）

- 生产环境不可用
- 数据丢失或损坏
- 安全漏洞被利用
- 性能严重下降（响应时间 > 5s）
- 关键功能失效（登录、支付等）

### 计划回滚（P1 - 高）

- 非关键功能失效
- 性能下降（响应时间 2-5s）
- 测试覆盖率下降到 60% 以下
- 频繁出现 Bug

### 评估回滚（P2 - 中）

- 性能轻微下降（响应时间 1-2s）
- 非频繁出现 Bug
- 用户体验下降

## 回滚策略

### 策略 1：代码回滚

适用于：代码错误、功能失效

```bash
# 1. 确定回滚的提交
git log --oneline -10

# 2. 回退到上一个稳定的提交
git revert <commit-hash>

# 3. 推送到远程
git push origin develop

# 4. 重新运行测试
cd backend
make ut
make it
```

### 策略 2：分支回滚

适用于：整个阶段迁移失败

```bash
# 1. 创建回滚分支
git checkout develop
git checkout -b rollback/ddd-migration-phase-{N}

# 2. 回退到迁移前的状态
git revert <migration-start-commit>..<migration-end-commit>

# 3. 推送到远程
git push origin rollback/ddd-migration-phase-{N}

# 4. 创建 PR 并合并
# - 从 rollback/ddd-migration-phase-{N} 到 develop
# - 要求代码审查
# - 要求所有测试通过
```

### 策略 3：数据库回滚

适用于：数据库迁移失败

```bash
# 1. 回退数据库迁移
cd backend/src
alembic downgrade -1

# 2. 验证数据库状态
alembic current

# 3. 检查数据完整性
python3 << EOF
from database.flask_models import db, User, Community
from app import create_app

app = create_app()
with app.app_context():
    # 检查关键数据
    user_count = db.session.query(User).count()
    community_count = db.session.query(Community).count()
    print(f"Users: {user_count}, Communities: {community_count}")
EOF
```

### 策略 4：配置回滚

适用于：配置错误

```bash
# 1. 回退配置文件
git checkout HEAD~1 -- config.py
git checkout HEAD~1 -- .env

# 2. 重启服务
./localrun.sh

# 3. 验证配置
curl http://localhost:9999/api/health
```

## 回滚步骤

### 阶段 1：评估（5 分钟）

1. **确认问题**
   - 检查日志：`tail -f logs/app.log`
   - 检查监控：查看性能指标
   - 检查错误率：查看错误日志

2. **确定影响范围**
   - 受影响的用户数量
   - 受影响的功能模块
   - 数据损坏情况

3. **评估回滚风险**
   - 回滚是否会导致其他问题
   - 是否需要数据迁移
   - 回滚时间估算

### 阶段 2：准备（10 分钟）

1. **通知团队**
   - 发送警报：Slack/钉钉
   - 通知相关人员：开发、测试、运维
   - 更新状态页面

2. **备份当前状态**
   ```bash
   # 备份数据库
   cp data.db data.db.backup.$(date +%Y%m%d_%H%M%S)
   
   # 备份代码
   git tag backup-$(date +%Y%m%d_%H%M%S)
   git push origin --tags
   ```

3. **准备回滚脚本**
   ```bash
   # 创建回滚脚本
   cat > rollback.sh << 'EOF'
   #!/bin/bash
   echo "开始回滚..."
   
   # 回退代码
   git revert <commit-hash>
   git push origin develop
   
   # 回退数据库
   cd backend/src
   alembic downgrade -1
   
   # 重启服务
   cd ../..
   ./localrun.sh
   
   echo "回滚完成"
   EOF
   
   chmod +x rollback.sh
   ```

### 阶段 3：执行（15 分钟）

1. **执行回滚**
   ```bash
   # 执行回滚脚本
   ./rollback.sh
   ```

2. **验证回滚**
   ```bash
   # 检查服务状态
   curl http://localhost:9999/api/health
   
   # 运行测试
   cd backend
   make ut
   make it
   
   # 检查日志
   tail -f logs/app.log
   ```

3. **监控指标**
   - 响应时间
   - 错误率
   - 吞吐量
   - 资源使用率

### 阶段 4：验证（10 分钟）

1. **功能验证**
   - 测试关键功能
   - 测试用户流程
   - 测试 API 端点

2. **数据验证**
   - 检查数据完整性
   - 检查数据一致性
   - 检查数据备份

3. **性能验证**
   - 运行性能测试
   - 检查响应时间
   - 检查资源使用

### 阶段 5：总结（10 分钟）

1. **记录回滚原因**
   ```bash
   # 创建回滚报告
   cat > rollback-report-$(date +%Y%m%d_%H%M%S).md << EOF
   # 回滚报告
   
   ## 回滚时间
   $(date)
   
   ## 回滚原因
   - 问题描述：{问题描述}
   - 影响范围：{影响范围}
   - 严重程度：{P0/P1/P2}
   
   ## 回滚步骤
   1. {步骤 1}
   2. {步骤 2}
   3. {步骤 3}
   
   ## 回滚结果
   - 回滚是否成功：{是/否}
   - 是否有遗留问题：{是/否}
   - 遗留问题描述：{描述}
   
   ## 后续行动
   - 问题分析：{分析结果}
   - 修复计划：{修复计划}
   - 预防措施：{预防措施}
   
   ## 联系人
   - 执行人：{姓名}
   - 审批人：{姓名}
   - 通知人：{姓名}
   EOF
   ```

2. **更新文档**
   - 更新迁移计划
   - 更新回滚方案
   - 更新技术文档

3. **团队复盘**
   - 召开复盘会议
   - 分析根本原因
   - 制定改进措施

## 回滚检查清单

### 回滚前

- [ ] 已确认问题严重程度
- [ ] 已评估回滚风险
- [ ] 已备份当前状态
- [ ] 已通知相关人员
- [ ] 已准备回滚脚本
- [ ] 已确定回滚策略

### 回滚中

- [ ] 已执行回滚脚本
- [ ] 已验证服务状态
- [ ] 已运行测试
- [ ] 已检查日志
- [ ] 已监控指标

### 回滚后

- [ ] 已验证功能
- [ ] 已验证数据
- [ ] 已验证性能
- [ ] 已记录回滚原因
- [ ] 已更新文档
- [ ] 已团队复盘

## 回滚时间目标

| 严重程度 | 评估时间 | 准备时间 | 执行时间 | 验证时间 | 总时间 |
|---------|---------|---------|---------|---------|--------|
| P0 - 严重 | 5 分钟 | 5 分钟 | 10 分钟 | 5 分钟 | 25 分钟 |
| P1 - 高 | 10 分钟 | 10 分钟 | 15 分钟 | 10 分钟 | 45 分钟 |
| P2 - 中 | 15 分钟 | 15 分钟 | 20 分钟 | 15 分钟 | 65 分钟 |

## 回滚后恢复

### 恢复步骤

1. **分析问题**
   - 查看日志
   - 分析代码
   - 复现问题

2. **修复问题**
   - 编写修复代码
   - 编写测试
   - 代码审查

3. **重新迁移**
   - 修复后重新迁移
   - 充分测试
   - 逐步部署

### 预防措施

1. **加强测试**
   - 增加单元测试
   - 增加集成测试
   - 增加性能测试

2. **改进流程**
   - 改进代码审查
   - 改进部署流程
   - 改进监控告警

3. **文档更新**
   - 更新技术文档
   - 更新操作手册
   - 更新应急预案

## 联系方式

### 紧急联系

- 技术负责人：{姓名} - {电话}
- DevOps 团队：{邮箱} - {电话}
- 项目经理：{姓名} - {电话}

### 非紧急联系

- 开发团队：{邮箱}
- 测试团队：{邮箱}
- 运维团队：{邮箱}

## 工具和脚本

### 回滚脚本模板

```bash
#!/bin/bash
# DDD 迁移回滚脚本
# 用途：快速回滚 DDD 迁移

set -e

# 配置
PHASE=${1:-"1"}  # 默认回滚阶段 1
BACKUP_DIR="./backups"
LOG_FILE="./logs/rollback-$(date +%Y%m%d_%H%M%S).log"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 记录日志
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

# 备份数据库
backup_database() {
    log "备份数据库..."
    cp data.db $BACKUP_DIR/data.db.backup.$(date +%Y%m%d_%H%M%S)
    log "数据库备份完成"
}

# 回退代码
rollback_code() {
    log "回退代码..."
    git revert HEAD~1
    git push origin develop
    log "代码回退完成"
}

# 回退数据库
rollback_database() {
    log "回退数据库..."
    cd backend/src
    alembic downgrade -1
    cd ../..
    log "数据库回退完成"
}

# 重启服务
restart_service() {
    log "重启服务..."
    pkill -f "python.*localrun.sh" || true
    sleep 2
    ./localrun.sh &
    log "服务重启完成"
}

# 验证服务
verify_service() {
    log "验证服务..."
    sleep 5
    curl -f http://localhost:9999/api/health || {
        log "服务验证失败"
        exit 1
    }
    log "服务验证成功"
}

# 主流程
main() {
    log "开始回滚阶段 $PHASE..."
    
    backup_database
    rollback_code
    rollback_database
    restart_service
    verify_service
    
    log "回滚完成"
}

# 执行主流程
main
```

---

**文档版本**: 1.0
**最后更新**: 2026-01-15
**维护者**: DDD 迁移团队