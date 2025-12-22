"""
社区工作人员服务模块 - Flask-SQLAlchemy版本
"""
import logging
import os
import json
from datetime import datetime
from hashlib import sha256
from wxcloudrun.user_service import UserService
from database.flask_models import db, User, Community, CommunityStaff, CommunityApplication, UserAuditLog
from const_default import DEFUALT_COMMUNITY_NAME, DEFUALT_COMMUNITY_ID
logger = logging.getLogger('CommunityService')


class CommunityStaffService:
    @staticmethod
    def is_admin_of_commu(commu_id, user_id):
        """检查用户是否是社区管理员"""
        user_data = UserService.query_user_by_id(user_id)
        if user_data.role == 4:  # 超级管理员
            return user_data
        
        if not commu_id:
            raise ValueError(f'Invalid community ID, {commu_id}')

        any_manager = db.session.query(CommunityStaff).filter_by(
            community_id=commu_id,
            user_id=user_id
        ).first()

        if any_manager:
            user_data = UserService.query_user_by_id(any_manager.user_id)
            return user_data
        else:
            return None

    @staticmethod
    def check_user_is_staff(user_id):
        """
        检查用户是否是任何社区的工作人员
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            bool: 如果是工作人员返回True，否则返回False
        """
        staff_record = db.session.query(CommunityStaff).filter_by(
            user_id=user_id
        ).first()
        return staff_record is not None

    @staticmethod
    def add_staff(operator_user_id, community_id, user_ids, role='staff'):
        """
        添加社区工作人员（支持批量操作）
        
        Args:
            operator_user_id (int): 操作者用户ID
            community_id (int): 社区ID
            user_ids (list): 要添加的用户ID列表
            role (str): 角色，'manager' 或 'staff'
            
        Returns:
            dict: 包含添加结果的字典
            {
                'success_count': int,
                'failed': list,
                'added_users': list
            }
            
        Raises:
            ValueError: 当参数无效或权限不足时
        """
        # 参数验证
        if not community_id:
            raise ValueError('缺少社区ID')
        
        if not user_ids or not isinstance(user_ids, list):
            raise ValueError('用户ID列表不能为空')
        
        if role not in ['manager', 'staff']:
            raise ValueError('角色参数错误，必须是manager或staff')
        
        # 检查社区是否存在
        community = db.session.get(Community, community_id)
        if not community:
            raise ValueError('社区不存在')
        
        # 检查操作用户是否存在
        operator_user = db.session.get(User, operator_user_id)
        if not operator_user:
            raise ValueError('操作者用户不存在')
        
        # 检查操作者权限
        if operator_user.role != 4:  # 不是超级管理员
            staff_record = db.session.query(CommunityStaff).filter_by(
                community_id=community_id,
                user_id=operator_user_id
            ).first()
            if not staff_record:
                raise ValueError('权限不足，需要社区工作人员权限')
                
            # 如果是专员（非主管）尝试添加主管，则拒绝
            if staff_record.role == 'staff' and role == 'manager':
                raise ValueError('专员不能添加主管，需要主管权限')
        
        # 如果是添加主管,只能添加一个
        if role == 'manager' and len(user_ids) > 1:
            raise ValueError('主管只能添加一个')
        
        # 检查是否已有主管
        if role == 'manager':
            existing_manager = db.session.query(CommunityStaff).filter_by(
                community_id=community_id,
                role='manager'
            ).first()
            if existing_manager:
                raise ValueError('该社区已有主管')
        
        added_count = 0
        failed = []
        
        # 验证并处理用户ID
        processed_user_ids = []
        for uid in user_ids:
            try:
                # 尝试转换为整数
                if isinstance(uid, str):
                    uid_int = int(uid)
                elif isinstance(uid, int):
                    uid_int = uid
                else:
                    failed.append({'user_id': uid, 'reason': f'无效的用户ID类型: {type(uid).__name__}'})
                    continue
                
                # 验证整数是否有效（正数）
                if uid_int <= 0:
                    failed.append({'user_id': uid, 'reason': '用户ID必须为正整数'})
                    continue
                
                processed_user_ids.append(uid_int)
            except (ValueError, TypeError) as e:
                failed.append({'user_id': uid, 'reason': f'无效的用户ID格式: {str(e)}'})
                continue
        
        # 如果没有有效的用户ID，抛出异常
        if not processed_user_ids:
            raise ValueError(f'所有用户ID都无效: {failed}')
        
        added_users_info = []
        
        for uid in processed_user_ids:
            try:
                # 检查用户是否存在
                target_user = db.session.get(User, uid)
                if not target_user:
                    failed.append({'user_id': uid, 'reason': '用户不存在'})
                    continue
                
                # 检查用户是否已在当前社区任职
                existing_in_current_community = db.session.query(CommunityStaff).filter_by(
                    community_id=community_id,
                    user_id=uid
                ).first()
                
                if existing_in_current_community:
                    failed.append({'user_id': uid, 'reason': '用户已在当前社区任职'})
                    continue
                
                # 添加工作人员
                staff = CommunityStaff(
                    community_id=community_id,
                    user_id=uid,
                    role=role
                )
                db.session.add(staff)
                
                # 记录审计日志
                audit_log = UserAuditLog(
                    user_id=operator_user_id,
                    action="add_community_staff",
                    detail=f"添加用户{uid}为社区{community_id}的{role}"
                )
                db.session.add(audit_log)
                
                added_count += 1
                
                # 添加成功用户信息
                added_users_info.append({
                    'user_id': uid,
                    'nickname': target_user.nickname,
                    'phone_number': target_user.phone_number,
                    'role': role
                })
                
                logger.info(f'成功添加工作人员: 社区{community_id}, 用户{uid}, 角色{role}')
                
            except Exception as e:
                logger.error(f'添加工作人员失败 user_id={uid}: {str(e)}')
                failed.append({'user_id': uid, 'reason': str(e)})
        
        if added_count == 0:
            raise ValueError('添加失败')
        
        # 提交事务
        db.session.commit()
        
        return {
            'success_count': added_count,
            'failed': failed,
            'added_users': added_users_info
        }

    @staticmethod
    def add_staff_single(community_id, user_id, role='staff', operator_id=None):
        """
        添加单个社区工作人员（保持向后兼容）
        
        Args:
            community_id (int): 社区ID
            user_id (int): 用户ID
            role (str): 角色 ('manager' 或 'staff')
            operator_id (int): 操作者ID
            
        Returns:
            CommunityStaff: 工作人员记录
        """
        # 检查是否已经是工作人员
        existing = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()
        
        if existing:
            raise ValueError("用户已经是该社区的工作人员")
        
        # 创建工作人员记录
        staff = CommunityStaff(
            community_id=community_id,
            user_id=user_id,
            role=role
        )
        db.session.add(staff)
        
        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=operator_id or user_id,
            action="add_staff",
            detail=f"添加社区工作人员: 社区ID={community_id}, 用户ID={user_id}, 角色={role}"
        )
        db.session.add(audit_log)
        
        db.session.commit()
        logger.info(f"社区工作人员添加成功: 社区ID={community_id}, 用户ID={user_id}")
        return staff

    @staticmethod
    def remove_staff(community_id, user_id, operator_id=None):
        """
        移除社区工作人员
        
        Args:
            community_id (int): 社区ID
            user_id (int): 用户ID
            operator_id (int): 操作者ID
            
        Returns:
            bool: 是否成功
        """
        staff = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()
        
        if not staff:
            raise ValueError("用户不是该社区的工作人员")
        
        db.session.delete(staff)
        
        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=operator_id or user_id,
            action="remove_staff",
            detail=f"移除社区工作人员: 社区ID={community_id}, 用户ID={user_id}"
        )
        db.session.add(audit_log)
        
        db.session.commit()
        logger.info(f"社区工作人员移除成功: 社区ID={community_id}, 用户ID={user_id}")
        return True

    @staticmethod
    def get_community_staff(community_id, role=None):
        """
        获取社区工作人员列表
        
        Args:
            community_id (int): 社区ID
            role (str): 角色筛选 (可选)
            
        Returns:
            list: 工作人员列表
        """
        query = db.session.query(CommunityStaff).filter_by(community_id=community_id)
        
        if role:
            query = query.filter_by(role=role)
        
        return query.all()

    @staticmethod
    def handle_user_community_change(user_id, old_community_id, new_community_id):
        """
        处理用户社区变更时的规则管理
        
        Args:
            user_id (int): 用户ID
            old_community_id (int): 原社区ID（可能为None）
            new_community_id (int): 新社区ID
            
        Returns:
            dict: 处理结果
        """
        try:
            from datetime import datetime
            
            # 0. 更新用户的社区归属
            user = db.session.get(User, user_id)
            if not user:
                raise ValueError(f'用户不存在: {user_id}')
            
            old_user_community_id = user.community_id
            user.community_id = new_community_id
            if new_community_id != old_user_community_id:
                user.community_joined_at = datetime.now()
            
            # 1. 停用旧社区的社区规则
            deactivated_count = 0
            if old_community_id:
                deactivated_count = CommunityStaffService._deactivate_old_community_rules(
                    user_id, old_community_id
                )
            
            # 2. 激活新社区的社区规则
            activated_count = CommunityStaffService._activate_new_community_rules(
                user_id, new_community_id
            )
            
            # 3. 处理工作人员关系
            # 移除旧社区的工作人员关系
            if old_community_id:
                db.session.query(CommunityStaff).filter_by(
                    community_id=old_community_id,
                    user_id=user_id
                ).delete()
            
            # 如果新社区存在，检查是否需要添加工作人员关系
            if new_community_id:
                if user and user.role >= 2:  # 如果是管理员或以上
                    staff = CommunityStaff(
                        community_id=new_community_id,
                        user_id=user_id,
                        role='manager' if user.role >= 3 else 'staff'
                    )
                    db.session.add(staff)
            
            db.session.commit()
            
            logger.info(f"用户{user_id}社区切换完成: 停用{deactivated_count}个旧规则，激活{activated_count}个新规则")
            
            return {
                'success': True,
                'deactivated_count': deactivated_count,
                'activated_count': activated_count,
                'message': f'成功停用{deactivated_count}个旧规则，激活{activated_count}个新规则'
            }
            
        except Exception as e:
            logger.error(f"处理用户社区切换失败: {str(e)}")
            raise ValueError(f"处理社区切换失败: {str(e)}")

    @staticmethod
    def _deactivate_old_community_rules(user_id, old_community_id):
        """
        停用旧社区的规则
        
        Args:
            user_id (int): 用户ID
            old_community_id (int): 原社区ID
            
        Returns:
            int: 停用的规则数量
        """
        from database.flask_models import UserCommunityRule, CommunityCheckinRule
        
        # 查找用户与旧社区规则的激活映射记录
        old_mappings = db.session.query(UserCommunityRule).join(CommunityCheckinRule).filter(
            UserCommunityRule.user_id == user_id,
            CommunityCheckinRule.community_id == old_community_id,
            UserCommunityRule.is_active == True
        ).all()
        
        # 将这些规则标记为停用
        deactivated_count = 0
        for mapping in old_mappings:
            mapping.is_active = False
            deactivated_count += 1
        
        logger.info(f"用户{user_id}的{deactivated_count}个旧社区规则已停用")
        return deactivated_count

    @staticmethod
    def _activate_new_community_rules(user_id, new_community_id):
        """
        激活新社区的规则
        
        Args:
            user_id (int): 用户ID
            new_community_id (int): 新社区ID
            
        Returns:
            int: 激活的规则数量
        """
        from database.flask_models import UserCommunityRule, CommunityCheckinRule
        
        # 获取新社区的所有启用规则
        new_community_rules = db.session.query(CommunityCheckinRule).filter(
            CommunityCheckinRule.community_id == new_community_id,
            CommunityCheckinRule.status == 1  # 启用状态
        ).all()
        
        activated_count = 0
        
        # 为用户创建或激活规则映射
        for rule in new_community_rules:
            # 查找是否已存在映射记录
            existing_mapping = db.session.query(UserCommunityRule).filter_by(
                user_id=user_id,
                community_rule_id=rule.community_rule_id
            ).first()
            
            if existing_mapping:
                # 如果存在且当前是停用状态，重新激活
                if not existing_mapping.is_active:
                    existing_mapping.is_active = True
                    activated_count += 1
            else:
                # 如果不存在，创建新映射
                new_mapping = UserCommunityRule(
                    user_id=user_id,
                    community_rule_id=rule.community_rule_id,
                    is_active=True
                )
                db.session.add(new_mapping)
                activated_count += 1
        
        logger.info(f"用户{user_id}已激活{activated_count}个新社区规则")
        return activated_count