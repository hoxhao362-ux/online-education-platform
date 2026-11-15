"""
成绩接口
POST /api/scores                       教师录入成绩
PUT  /api/scores                       教师修改成绩
GET  /api/scores/mine                  学生查询本人成绩单
GET  /api/scores/course/<course_id>    教师查询本人课程成绩与统计
"""
from flask import Blueprint, request

from app.service.score_service import ScoreService
from app.utils.auth_helper import get_current_user, student_required, teacher_required
from app.utils.response import success
from app.utils.validators import require_json

score_bp = Blueprint("score", __name__, url_prefix="/api/scores")


@score_bp.post("")
@teacher_required
def record_score():
    """教师录入成绩（学生须已选课）"""
    user = get_current_user()
    data = require_json()
    return success(ScoreService.record_score(user["user_id"], data),
                   "成绩录入成功", 201)


@score_bp.put("")
@teacher_required
def update_score():
    """教师修改已录入的成绩"""
    user = get_current_user()
    data = require_json()
    return success(ScoreService.update_score(user["user_id"], data),
                   "成绩修改成功")


@score_bp.get("/mine")
@student_required
def list_my_scores():
    """学生查询本人成绩单"""
    user = get_current_user()
    return success(ScoreService.list_my_scores(user["user_id"]))


@score_bp.get("/course/<course_id>")
@teacher_required
def list_course_scores(course_id: str):
    """教师查询本人课程成绩与统计"""
    user = get_current_user()
    term = request.args.get("term")
    return success(ScoreService.list_course_scores(user["user_id"], course_id, term))
