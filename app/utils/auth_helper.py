"""
鉴权辅助工具
基于 Flask Session 实现登录状态维护与角色权限校验。
Session 中存储：
    - user_id   : 学号 / 工号（数据库主键）
    - role      : 角色标识 ("student" | "teacher")
    - username  : 登录账号（学号 / 工号）
    - name      : 真实姓名
"""
from functools import wraps

from flask import session

from app.utils.exceptions import UnauthorizedException, ForbiddenException

ROLE_STUDENT = "student"
ROLE_TEACHER = "teacher"


def set_login_session(user_id: str, role: str, username: str, name: str):
    """登录成功后写入 Session"""
    session.clear()
    session["user_id"] = user_id
    session["role"] = role
    session["username"] = username
    session["name"] = name


def clear_login_session():
    """退出登录，清空 Session"""
    session.clear()


def get_current_user() -> dict:
    """
    获取当前登录用户信息（从 Session 中读取）
    :return: dict {"user_id": str, "role": str, "username": str, "name": str}
    :raises UnauthorizedException: 未登录时抛出
    """
    if "user_id" not in session:
        raise UnauthorizedException("请先登录")
    return {
        "user_id": session["user_id"],
        "role": session["role"],
        "username": session.get("username"),
        "name": session.get("name")
    }


def login_required(f):
    """
    装饰器：要求接口必须登录后才能访问。
    未登录则返回 401。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        get_current_user()  # 未登录会抛出 UnauthorizedException
        return f(*args, **kwargs)
    return decorated


def teacher_required(f):
    """
    装饰器：要求接口必须是教师角色。
    未登录返回 401，非教师返回 403。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if user["role"] != ROLE_TEACHER:
            raise ForbiddenException("该接口仅限教师操作")
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    """
    装饰器：要求接口必须是学生角色。
    未登录返回 401，非学生返回 403。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if user["role"] != ROLE_STUDENT:
            raise ForbiddenException("该接口仅限学生操作")
        return f(*args, **kwargs)
    return decorated
