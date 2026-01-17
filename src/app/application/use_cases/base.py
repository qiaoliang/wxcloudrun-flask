"""
用例基类和结果对象

提供用例执行的通用基础设施。
"""
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict
from enum import Enum


class UseCaseStatus(Enum):
    """用例执行状态"""
    SUCCESS = "success"
    FAILURE = "failure"
    VALIDATION_ERROR = "validation_error"
    BUSINESS_ERROR = "business_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"


@dataclass
class UseCaseResult:
    """用例执行结果"""
    status: UseCaseStatus
    message: str
    data: Any = None
    errors: List[str] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        """是否成功"""
        return self.status == UseCaseStatus.SUCCESS

    @property
    def is_failure(self) -> bool:
        """是否失败"""
        return self.status != UseCaseStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'status': self.status.value,
            'message': self.message,
            'data': self.data,
            'errors': self.errors
        }

    @staticmethod
    def success(data: Any = None, message: str = "操作成功") -> 'UseCaseResult':
        """创建成功结果"""
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message=message,
            data=data
        )

    @staticmethod
    def fail(message: str, status: UseCaseStatus = UseCaseStatus.FAILURE) -> 'UseCaseResult':
        """创建失败结果"""
        return UseCaseResult(
            status=status,
            message=message
        )


class UseCaseError(Exception):
    """用例执行异常"""
    def __init__(self, message: str, status: UseCaseStatus = UseCaseStatus.BUSINESS_ERROR):
        self.message = message
        self.status = status
        super().__init__(message)


class BaseUseCase:
    """用例基类"""

    def execute(self, *args, **kwargs) -> UseCaseResult:
        """
        执行用例

        子类应该实现 _validate 和 _execute 方法

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 参数验证
            validation_result = self._validate(*args, **kwargs)
            if not validation_result.is_success:
                return validation_result

            # 执行业务逻辑
            return self._execute(*args, **kwargs)

        except UseCaseError as e:
            return UseCaseResult(
                status=e.status,
                message=e.message
            )
        except Exception as e:
            # 记录未预期的异常
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"用例执行异常: {str(e)}", exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f"系统错误: {str(e)}"
            )

    def _validate(self, *args, **kwargs) -> UseCaseResult:
        """
        验证参数

        子类可以重写此方法实现自定义验证逻辑

        Returns:
            UseCaseResult: 验证结果
        """
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, *args, **kwargs) -> UseCaseResult:
        """
        执行业务逻辑

        子类必须实现此方法

        Returns:
            UseCaseResult: 执行结果
        """
        raise NotImplementedError("子类必须实现 _execute 方法")