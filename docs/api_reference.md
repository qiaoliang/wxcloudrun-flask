# API参考文档（后端与前端封装对齐）

## 说明
- 前端封装位置：`frontend/api/auth.js`
- 所有接口统一返回结构：`{ code: 1|-1, data: {...}, msg: 'success|error' }`
- 鉴权：除登录外均需`Authorization: Bearer {token}`（通过`request.js`自动附加）

## 认证
- `POST /api/login`
  - 入参：
    - 非首次登录：`{ code: string }`
    - 首次登录：`{ code: string, nickname?: string, avatar_url?: string }`
  - 出参：`{ token, user }`
- `POST /api/logout`

## 用户资料
- `GET /api/user/profile`
  - 出参（关键字段）：
    - `user_id, wechat_openid, phone_number, nickname, avatar_url`
    - `role`（字符串：`solo|supervisor|community`）
    - `status`（字符串）
    - 权限组合：`is_solo_user, is_supervisor, is_community_worker`
  - 前端字段映射：`avatar_url→avatarUrl, nickname→nickName, phone_number→phoneNumber, community_id→communityId`
- `POST /api/user/profile`
  - 入参（可选）：`nickname, avatar_url, phone_number, role, community_id, status, is_solo_user, is_supervisor, is_community_worker`

## 打卡
- `GET /api/checkin/today`
- `POST /api/checkin`
  - 入参：`{ rule_id, timestamp? }`
- `POST /api/checkin/cancel`
  - 入参：`{ record_id }`
- `GET /api/checkin/history`
  - 入参：`{ start_date?, end_date?, page?, page_size? }`
- `GET /api/checkin/rules`
- `POST /api/checkin/rules`
- `PUT /api/checkin/rules`
- `DELETE /api/checkin/rules`

## 监督关系
- 搜索用户：`GET /api/users/search`（入参：`nickname, limit?`；出参：`{ users: [{ user_id, nickname, avatar_url, is_supervisor }] }`）
- 邀请监护人：`POST /api/rules/supervision/invite`
  - 入参示例：`{ target_openid, rule_ids: number[] }`（`rule_id=NULL`表示全规则邀请）
- 查看邀请列表：`GET /api/rules/supervision/invitations?type=received|sent`
  - 出参：`{ type, invitations: [{ relation_id, solo_user, rule, status, created_at }] }`
- 接受邀请：`POST /api/rules/supervision/accept`
  - 入参：`{ relation_id }`
- 拒绝邀请：`POST /api/rules/supervision/reject`
  - 入参：`{ relation_id }`
- 我监督的用户：`GET /api/rules/supervision/my_supervised`
- 我的监护人：`GET /api/rules/supervision/my_guardians`
- 被监督用户记录：`GET /api/rules/supervision/records`
  - 入参：`{ solo_user_id?, rule_id?, start_date?, end_date? }`

## 社区身份验证
- `POST /api/community/verify`
  - 入参：`{ name, workId, workProof }`
  - 出参：`{ message, verification_status: 'pending' }`

## 错误码约定
- `code=1`：成功
- `code=-1`：失败（`msg`包含错误说明）

## 前端封装函数映射
- `authApi.getUserProfile` → `GET /api/user/profile`（含字段驼峰转换）
- `authApi.updateUserProfile` → `POST /api/user/profile`
- `authApi.getTodayCheckinItems` → `GET /api/checkin/today`
- `authApi.performCheckin` → `POST /api/checkin`
- `authApi.cancelCheckin` → `POST /api/checkin/cancel`
- `authApi.getCheckinHistory` → `GET /api/checkin/history`
- `authApi.getCheckinRules` → `GET /api/checkin/rules`
- `authApi.createCheckinRule` → `POST /api/checkin/rules`
- `authApi.updateCheckinRule` → `PUT /api/checkin/rules`
- `authApi.deleteCheckinRule` → `DELETE /api/checkin/rules`
- `authApi.searchUsers` → `GET /api/users/search`
- `authApi.inviteSupervisor` → `POST /api/rules/supervision/invite`
- `authApi.getSupervisionInvitations` → `GET /api/rules/supervision/invitations`
- `authApi.acceptSupervisionInvitation` → `POST /api/rules/supervision/accept`
- `authApi.rejectSupervisionInvitation` → `POST /api/rules/supervision/reject`
- `authApi.getMySupervisedUsers` → `GET /api/rules/supervision/my_supervised`
- `authApi.getMyGuardians` → `GET /api/rules/supervision/my_guardians`
- `authApi.getSupervisedRecords` → `GET /api/rules/supervision/records`
