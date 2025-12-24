# API契约验证报告
生成时间: 2025-12-24 23:21:02

✅ **验证结果**: 通过

## 统计信息
- 契约端点数量: 47
- 后端实现端点: 88
- 错误数量: 0
- 警告数量: 0

## ⚠️ 契约中定义但后端未实现
- POST /community-checkin/rules/{rule_id}/enable
- PUT /checkin/rules
- GET /user-checkin/rules/{rule_id}
- POST /supervision/reject
- GET /supervision/my_supervised
- POST /checkin/cancel
- POST /checkin/rules
- GET /share/checkin/resolve
- POST /supervision/invite
- DELETE /checkin/rules
- POST /supervision/accept
- POST /community-checkin/rules
- GET /checkin/history
- GET /supervision/my_guardians
- PUT /community-checkin/rules/{rule_id}
- GET /community-checkin/rules/{rule_id}
- GET /communities/{community_id}/users
- POST /supervision/invite_link
- GET /community-checkin/rules
- POST /community-checkin/rules/{rule_id}/disable
- POST /checkin
- POST /share/checkin/create
- GET /supervision/records
- GET /supervision/invite/resolve
- GET /communities/{community_id}
- GET /checkin/rules
- DELETE /community-checkin/rules/{rule_id}
- GET /supervision/invitations

## ⚠️ 后端已实现但契约中缺失
- GET /check-in (src/app/modules/share/routes.py:145)
- POST /accept (src/app/modules/supervision/routes.py:227)
- GET /user/search-all-excluding-blackroom (src/app/modules/community/routes.py:1147)
- GET /checkin/resolve (src/app/modules/share/routes.py:80)
- GET /communities (src/app/modules/community/routes.py:91)
- POST /community/create (src/app/modules/community/routes.py:881)
- GET /communities/<int:community_id>/users (src/app/modules/community/routes.py:159)
- POST /events/<int:event_id>/support (src/app/modules/events/routes.py:121)
- GET /my_guardians (src/app/modules/supervision/routes.py:331)
- POST /community/delete (src/app/modules/community/routes.py:1033)
- POST /community/toggle-status (src/app/modules/community/routes.py:988)
- PUT /rules/<int:rule_id> (src/app/modules/community_checkin/routes.py:160)
- PUT /community/applications/<int:application_id>/approve (src/app/modules/community/routes.py:364)
- GET /invite/resolve (src/app/modules/supervision/routes.py:149)
- DELETE /communities/<int:community_id>/users/<int:target_user_id> (src/app/modules/community/routes.py:219)
- PUT /rules (src/app/modules/checkin/routes.py:273)
- GET /records (src/app/modules/supervision/routes.py:375)
- POST /checkin/create (src/app/modules/share/routes.py:22)
- GET /community/applications (src/app/modules/community/routes.py:257)
- POST /cancel (src/app/modules/checkin/routes.py:170)
- GET /user-checkin/rules/<int:rule_id> (src/app/modules/user_checkin/routes.py:136)
- POST /community/remove-user (src/app/modules/community/routes.py:833)
- GET /community/users (src/app/modules/community/routes.py:734)
- GET /rules (src/app/modules/checkin/routes.py:273)
- GET /rules (src/app/modules/community_checkin/routes.py:89)
- POST /user/switch-community (src/app/modules/community/routes.py:1482)
- POST /reject (src/app/modules/supervision/routes.py:256)
- GET /my_supervised (src/app/modules/supervision/routes.py:287)
- GET /communities/<int:community_id>/events (src/app/modules/events/routes.py:68)
- POST /user/bind_wechat (src/app/modules/user/routes.py:344)
- GET /communities/<int:community_id> (src/app/modules/community/routes.py:1393)
- GET /communities/<int:community_id>/stats (src/app/modules/events/routes.py:156)
- POST /community/update (src/app/modules/community/routes.py:942)
- POST /auth/login_phone_code (src/app/modules/auth/routes.py:496)
- POST /user/community/verify (src/app/modules/user/routes.py:432)
- POST /logout (src/app/modules/auth/routes.py:392)
- DELETE /rules/<int:rule_id> (src/app/modules/community_checkin/routes.py:252)
- GET / (src/app/modules/misc/routes.py:18)
- POST /miss (src/app/modules/checkin/routes.py:112)
- POST /events (src/app/modules/events/routes.py:17)
- GET /communities/ankafamily/users/search (src/app/modules/community/routes.py:1209)
- POST /rules/<int:rule_id>/enable (src/app/modules/community_checkin/routes.py:194)
- DELETE /rules (src/app/modules/checkin/routes.py:273)
- GET /user/community (src/app/modules/community/routes.py:427)
- POST /rules/<int:rule_id>/disable (src/app/modules/community_checkin/routes.py:223)
- POST /community/add-users (src/app/modules/community/routes.py:786)
- GET /env (src/app/modules/misc/routes.py:27)
- GET /communities/available (src/app/modules/community/routes.py:497)
- GET /communities/manage/<int:community_id>/access-check (src/app/modules/community/routes.py:1357)
- GET /community/staff/list (src/app/modules/community/routes.py:528)
- GET /rules/<int:rule_id> (src/app/modules/community_checkin/routes.py:284)
- POST /user-checkin/rules/source-info (src/app/modules/user_checkin/routes.py:245)
- POST /auth/login_phone_password (src/app/modules/auth/routes.py:583)
- POST /invite_link (src/app/modules/supervision/routes.py:104)
- POST /invite (src/app/modules/supervision/routes.py:23)
- GET /invitations (src/app/modules/supervision/routes.py:179)
- GET /history (src/app/modules/checkin/routes.py:217)
- GET /community/communities/manage/list (src/app/modules/community/routes.py:1271)
- POST /community/create-user (src/app/modules/community/routes.py:1431)
- GET /communities/manage/search (src/app/modules/community/routes.py:1307)
- POST /rules (src/app/modules/checkin/routes.py:273)
- POST /rules (src/app/modules/community_checkin/routes.py:120)
- POST /community/applications (src/app/modules/community/routes.py:313)
- GET /today (src/app/modules/checkin/routes.py:22)
- GET /events/<int:event_id> (src/app/modules/events/routes.py:99)
- POST /auth/login_phone (src/app/modules/auth/routes.py:663)
- POST  (src/app/modules/checkin/routes.py:54)
- PUT /community/applications/<int:application_id>/reject (src/app/modules/community/routes.py:392)

## 🔧 修复建议
### 补充后端实现
1. 实现契约中定义但缺失的API
2. 确保所有API都有对应的业务逻辑

### 补充契约定义
1. 将后端已实现的API添加到契约中
2. 确保API文档与实现同步
