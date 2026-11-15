"""
课程接口
GET    /api/courses              课程列表（公开，默认只返回开课课程）
GET    /api/courses/mine         教师本人授课课程
GET    /api/courses/<course_id>  课程详情（公开）
POST   /api/courses              新增课程（教师）
PUT    /api/courses/<course_id>  编辑课程（教师，仅本人课程）
DELETE /api/courses/<course_id>  删除课程（教师，仅本人课程）
"""
from flask import Blueprint, request

from app.service.course_service import CourseService
from app.utils.auth_helper import get_current_user, teacher_required
from app.utils.exceptions import BusinessException
from app.utils.response import success
from app.utils.validators import require_json

course_bp = Blueprint("course", __name__, url_prefix="/api/courses")


@course_bp.get("")
def list_courses():
    """课程列表：所有人可查，默认只展示开放课程"""
    keyword = request.args.get("keyword")
    teacher_id = request.args.get("teacher_id")
    status_arg = request.args.get("status", "1")
    if status_arg not in ("0", "1"):
        raise BusinessException("status 只能为 0 或 1")
    return success(CourseService.list_courses(
        keyword=keyword, teacher_id=teacher_id, status=int(status_arg)
    ))


@course_bp.get("/mine")
@teacher_required
def list_my_courses():
    """教师查询本人全部课程（含已下架）"""
    user = get_current_user()
    return success(CourseService.list_teacher_courses(user["user_id"]))


@course_bp.get("/<course_id>")
def get_course(course_id: str):
    """课程详情"""
    return success(CourseService.get_course(course_id))


@course_bp.post("")
@teacher_required
def create_course():
    """新增课程"""
    user = get_current_user()
    data = require_json()
    return success(CourseService.create_course(user["user_id"], data),
                   "课程新增成功", 201)


@course_bp.put("/<course_id>")
@teacher_required
def update_course(course_id: str):
    """编辑课程"""
    user = get_current_user()
    data = require_json()
    return success(CourseService.update_course(user["user_id"], course_id, data),
                   "课程修改成功")


@course_bp.delete("/<course_id>")
@teacher_required
def delete_course(course_id: str):
    """删除课程"""
    user = get_current_user()
    return success(CourseService.delete_course(user["user_id"], course_id),
                   "课程删除成功")
