"""
用户认证接口
POST /api/auth/student/register  学生注册
POST /api/auth/teacher/register  教师注册
POST /api/auth/login             账号登录
POST /api/auth/logout            退出登录
GET  /api/auth/me                查询当前登录用户
PUT  /api/auth/profile           修改个人资料
"""
from flask import Blueprint

from app.service.auth_service import AuthService
from app.utils.auth_helper import login_required
from app.utils.response import success
from app.utils.validators import require_json

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/student/register")
def register_student():
    """学生注册"""
    data = require_json()
    return success(AuthService.register_student(data), "学生注册成功", 201)


@auth_bp.post("/teacher/register")
def register_teacher():
    """教师注册"""
    data = require_json()
    return success(AuthService.register_teacher(data), "教师注册成功", 201)


@auth_bp.post("/login")
def login():
    """登录：返回角色标识与用户信息"""
    data = require_json()
    return success(AuthService.login(data), "登录成功")


@auth_bp.post("/logout")
def logout():
    """退出登录"""
    AuthService.logout()
    return success(None, "已退出登录")


@auth_bp.get("/me")
@login_required
def me():
    """查询当前登录用户资料"""
    return success(AuthService.get_profile())


@auth_bp.put("/profile")
@login_required
def update_profile():
    """修改当前登录用户基础信息"""
    data = require_json()
    return success(AuthService.update_profile(data), "资料修改成功")
