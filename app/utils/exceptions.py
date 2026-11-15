"""
自定义业务异常类
所有 Service 层的业务错误均通过这里的异常向上传递，
Controller 统一捕获并返回规范响应，不暴露底层数据库异常。
"""


class BusinessException(Exception):
    """业务逻辑异常（参数非法、权限不足、数据冲突等）"""

    def __init__(self, message: str, code: int = 400):
        """
        :param message: 用户友好的错误提示
        :param code: HTTP 状态码语义（400 参数错误 / 403 无权限 / 404 不存在 / 409 冲突）
        """
        super().__init__(message)
        self.message = message
        self.code = code


class UnauthorizedException(BusinessException):
    """未登录或身份验证失败"""

    def __init__(self, message: str = "请先登录"):
        super().__init__(message, code=401)


class ForbiddenException(BusinessException):
    """已登录但无权限操作"""

    def __init__(self, message: str = "权限不足，禁止操作"):
        super().__init__(message, code=403)


class NotFoundException(BusinessException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, code=404)


class DuplicateException(BusinessException):
    """数据重复冲突（如重复选课、重复账号）"""

    def __init__(self, message: str = "数据已存在，请勿重复提交"):
        super().__init__(message, code=409)


class ConflictException(BusinessException):
    """业务状态冲突（如课程已有成绩不可删除）"""

    def __init__(self, message: str = "当前数据状态不允许该操作"):
        super().__init__(message, code=409)
