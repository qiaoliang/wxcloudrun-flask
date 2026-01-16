"""
搜索用户用例
支持按手机号和昵称搜索用户
"""
import logging
from sqlalchemy import or_, and_

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from database.flask_models import db, User, Community


class SearchUsersUseCase(BaseUseCase):
    """搜索用户用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def _validate(self, keyword: str, page: int, per_page: int, search_type: str = 'all', exclude_blackroom: bool = False) -> UseCaseResult:
        """验证参数"""
        if not keyword or not keyword.strip():
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='搜索关键词不能为空'
            )

        if page < 1:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='页码必须大于0'
            )

        if per_page < 1 or per_page > 100:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='每页数量必须在1-100之间'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, keyword: str, page: int, per_page: int, search_type: str = 'all', exclude_blackroom: bool = False) -> UseCaseResult:
        """
        执行搜索用户逻辑

        Args:
            keyword: 搜索关键词
            page: 页码
            per_page: 每页数量
            search_type: 搜索类型 (all, phone, nickname)
            exclude_blackroom: 是否排除黑名单房间

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 计算偏移量
            offset = (page - 1) * per_page

            # 构建查询
            query = db.session.query(User)

            # 根据搜索类型构建查询条件
            if search_type == 'phone':
                # 按手机号搜索
                query = query.filter(
                    User.phone_number.like(f'%{keyword}%')
                )
            elif search_type == 'nickname':
                # 按昵称搜索
                query = query.filter(
                    User.nickname.like(f'%{keyword}%')
                )
            else:
                # 全局搜索：手机号或昵称
                query = query.filter(
                    or_(
                        User.phone_number.like(f'%{keyword}%'),
                        User.nickname.like(f'%{keyword}%')
                    )
                )

            # 如果需要排除黑名单房间
            if exclude_blackroom:
                # 排除社区名称包含"黑名单"的用户
                query = query.outerjoin(Community, User.community_id == Community.community_id)
                query = query.filter(
                    or_(
                        Community.name.notlike('%黑名单%'),
                        Community.name.is_(None)
                    )
                )

            # 获取总数
            total = query.count()

            # 分页查询
            users = query.order_by(User.created_at.desc()).offset(offset).limit(per_page).all()

            # 构造返回数据
            users_data = []
            for user in users:
                user_data = {
                    'user_id': user.user_id,
                    'wechat_openid': user.wechat_openid,
                    'phone_number': user.phone_number,
                    'nickname': user.nickname,
                    'name': user.name,
                    'avatar_url': user.avatar_url,
                    'role_name': user.role_name,
                    'community_id': user.community_id,
                    'community_name': user.community.name if user.community else None,
                    'status': user.status,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
                users_data.append(user_data)

            self.logger.info(f'搜索用户成功: keyword={keyword}, type={search_type}, count={len(users_data)}, total={total}')

            # 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='搜索成功',
                data={
                    'users': users_data,
                    'total': total,
                    'page': page,
                    'per_page': per_page,
                    'has_next': len(users_data) == per_page
                }
            )

        except Exception as e:
            self.logger.error(f'搜索用户失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'搜索失败: {str(e)}'
            )