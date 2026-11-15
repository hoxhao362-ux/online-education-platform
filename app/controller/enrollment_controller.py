"""
选课接口（学生权限）
POST /api/enrollments       学生选课
GET  /api/enrollments/mine  查询本人已选课程
"""
from flask import Blueprint

from app.service.enrollment_service import EnrollmentService
from app.utils.auth_helper import get_current_user, student_required
from app.utils.response import success
from app.utils.validators import require_json

enrollment_bp = Blueprint("enrollment", __name__, url_prefix="/api/enrollments")


@enrollment_bp.post("")
@student_required
def enroll():
    """学生选课"""
    user = get_current_user()
    data = require_json()
    return success(EnrollmentService.enroll(user["user_id"], data),
                   "选课成功", 201)


@enrollment_bp.get("/mine")
@student_required
def list_my_courses():
    """查询本人已选课程"""
    user = get_current_user()
    return success(EnrollmentService.list_my_courses(user["user_id"]))
