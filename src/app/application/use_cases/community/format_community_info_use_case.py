"""
格式化社区信息用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class FormatCommunityInfoUseCase(BaseUseCase):
    """格式化社区信息用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_staff_repository = RepositoryFactory.get_community_staff_repository()

    def execute(
        self,
        community,
        include_worker_stats: bool = False
    ) -> UseCaseResult:
        """
        执行格式化社区信息用例

        Args:
            community: Community对象
            include_worker_stats: 是否包含工作人员统计信息

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 获取创建者信息
            creator = None
            if community.creator_id:
                creator_user = self.user_repository.find_by_id(community.creator_id)
                if creator_user:
                    creator = {
                        'user_id': creator_user.user_id,
                        'nickname': creator_user.nickname,
                        'avatar_url': creator_user.avatar_url
                    }

            # 2. 获取主管信息
            manager = None
            self.logger.info(f'_format_community_info - 社区{community.community_id}的manager_id: {community.manager_id}')
            if community.manager_id:
                manager_user = self.user_repository.find_by_id(community.manager_id)
                if manager_user:
                    # 诊断日志：记录用户的 nickname 和 name 字段
                    self.logger.info(
                        f'_format_community_info - 找到主管用户: user_id={manager_user.user_id}, '
                        f'nickname="{manager_user.nickname}", name="{manager_user.name}"'
                    )
                    manager = {
                        'user_id': manager_user.user_id,
                        'nickname': manager_user.nickname,
                        'avatar_url': manager_user.avatar_url
                    }
                    self.logger.info(f'_format_community_info - 成功获取主管信息: {manager}')

                    # Layer 3: 数据一致性验证
                    # 检查 CommunityStaff 表中是否存在该主管关系
                    try:
                        from sqlalchemy import select
                        from database.flask_models import CommunityStaff, db
                        stmt = select(CommunityStaff).where(
                            CommunityStaff.community_id == community.community_id,
                            CommunityStaff.user_id == community.manager_id,
                            CommunityStaff.role == 'manager',
                            CommunityStaff.removed_at.is_(None)
                        )
                        staff_relation = db.session.execute(stmt).scalar_one_or_none()

                        if not staff_relation:
                            # 数据不一致：manager_id 存在但 CommunityStaff 关系不存在
                            self.logger.warning(
                                f'Layer 3 数据不一致检测: 社区{community.community_id}的manager_id={community.manager_id} '
                                f'但在CommunityStaff表中未找到对应的主管关系'
                            )
                    except Exception as e:
                        # 验证失败不影响主流程，只记录日志
                        self.logger.error(f'Layer 3 数据一致性验证失败: {str(e)}')
                else:
                    self.logger.warning(f'_format_community_info - manager_id={community.manager_id}对应的用户不存在')
            else:
                self.logger.info(f'_format_community_info - 社区{community.community_id}未设置主管')

            # 3. 获取工作人员数量统计
            manager_count = 0
            staff_count = 0
            worker_count = 0
            user_count = 0  # 普通成员数量（不包括工作人员）
            if include_worker_stats:
                # 统计主管
                managers = self.community_staff_repository.find_by_community_and_role(
                    community_id=community.community_id,
                    role='manager'
                )
                manager_count = len(managers)

                # 统计专员（不包括主管）
                staff = self.community_staff_repository.find_by_community_and_role(
                    community_id=community.community_id,
                    role='staff'
                )
                staff_count = len(staff)
                worker_count = manager_count + staff_count  # 工作人员总数 = 主管 + 专员

                # 获取所有工作人员的用户ID列表
                all_staff = self.community_staff_repository.find_by_community_id(
                    community_id=community.community_id,
                    include_removed=False
                )
                staff_user_ids = [s.user_id for s in all_staff]

                # 统计普通成员（不包括工作人员）
                if staff_user_ids:
                    # 获取所有社区用户
                    all_users = self.user_repository.find_by_community_id(community.community_id)
                    # 排除工作人员
                    user_count = len([u for u in all_users if u.user_id not in staff_user_ids])
                else:
                    # 如果没有工作人员，统计所有社区用户
                    all_users = self.user_repository.find_by_community_id(community.community_id)
                    user_count = len(all_users)

            # 4. 构造返回数据
            result_data = {
                'community_id': community.community_id,
                'name': community.name,
                'description': community.description,
                'location': community.location or '',
                'location_lat': community.location_lat,
                'location_lon': community.location_lon,
                'province': community.province,
                'city': community.city,
                'district': community.district,
                'street': community.street,
                'creator_id': community.creator_id,
                'creator': creator,
                'manager_id': community.manager_id,
                'manager': manager,
                'manager_name': manager['nickname'] if manager else None,  # 主管昵称（用于前端显示）
                'status': community.status,
                'is_default': community.is_default,
                'is_blackhouse': community.is_blackhouse,
                'created_at': community.created_at.isoformat() if community.created_at else None,
                'updated_at': community.updated_at.isoformat() if community.updated_at else None,
                'manager_count': manager_count,  # 主管数量
                'worker_count': worker_count,  # 工作人员总数（主管+专员）
                'staff_count': staff_count,  # 专员数量（不包括主管）
                'user_count': user_count  # 普通成员数量（不包括工作人员）
            }

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='格式化社区信息成功',
                data=result_data
            )

        except Exception as e:
            self.logger.error(f'格式化社区信息失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'格式化社区信息失败: {str(e)}'
            )