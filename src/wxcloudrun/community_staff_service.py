import logging
import os
import json
from datetime import datetime
from hashlib import sha256
from .dao import get_db
from wxcloudrun.user_service import UserService
from database.models import User, Community, CommunityStaff,CommunityApplication, UserAuditLog
from const_default import DEFUALT_COMMUNITY_NAME,DEFUALT_COMMUNITY_ID
logger = logging.getLogger('CommunityService')

class CommunityStaffService:
    @staticmethod
    def is_admin_of_commu(commu_id,user_id):
        user_data = UserService.query_user_by_id(user_id)
        if user_data.role == 4:  # 超级管理员
            return user_data
        db = get_db()
        with db.get_session() as session:
            if not commu_id:
                raise ValueError(f'Invalid community ID, {commu_id}')

            any_manager = session.query(CommunityStaff).filter_by(
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
        db = get_db()
        with db.get_session() as session:
            staff_record = session.query(CommunityStaff).filter_by(
                user_id=user_id
            ).first()
            return staff_record is not None

    @staticmethod
    def add_staff(operator_user_id, community_id, user_ids, role='staff'):
        """
        添加社区工作人员
        
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
        from database.models import UserAuditLog
        
        # 参数验证
        if not community_id:
            raise ValueError('缺少社区ID')
        
        if not user_ids or not isinstance(user_ids, list):
            raise ValueError('用户ID列表不能为空')
        
        if role not in ['manager', 'staff']:
            raise ValueError('角色参数错误，必须是manager或staff')
        
        db = get_db()
        with db.get_session() as session:
            # 检查社区是否存在
            community = session.query(Community).get(community_id)
            if not community:
                raise ValueError('社区不存在')
            
            # 权限检查
            operator_user = session.query(User).get(operator_user_id)
            if not operator_user:
                raise ValueError('操作者用户不存在')
            
            # 检查操作者权限
            if operator_user.role != 4:  # 不是超级管理员
                staff_record = session.query(CommunityStaff).filter_by(
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
                existing_manager = session.query(CommunityStaff).filter_by(
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
                    target_user = session.query(User).get(uid)
                    if not target_user:
                        failed.append({'user_id': uid, 'reason': '用户不存在'})
                        continue
                    
                    # 检查用户是否已在当前社区任职
                    existing_in_current_community = session.query(CommunityStaff).filter_by(
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
                    session.add(staff)
                    
                    # 记录审计日志
                    audit_log = UserAuditLog(
                        user_id=operator_user_id,
                        action="add_community_staff",
                        detail=f"添加用户{uid}为社区{community_id}的{role}"
                    )
                    session.add(audit_log)
                    
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
            session.commit()
            
            return {
                'success_count': added_count,
                'failed': failed,
                'added_users': added_users_info
            }