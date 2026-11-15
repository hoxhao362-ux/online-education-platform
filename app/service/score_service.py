"""
成绩管理业务
教师只能为本人授课的课程录入/修改成绩，且学生必须已选课；
分数范围 0~100；学生只能查询本人成绩。
"""
from flask import current_app

from app.dao.course_dao import CourseDao
from app.dao.score_dao import ScoreDao
from app.dao.student_dao import StudentDao
from app.utils import validators
from app.utils.db import commit
from app.utils.exceptions import (
    BusinessException, DuplicateException, ForbiddenException, NotFoundException
)


class ScoreService:
    """成绩模块业务逻辑"""

    @staticmethod
    def _parse_params(data: dict):
        """解析成绩录入/修改的公共参数"""
        student_id = validators.validate_student_id(
            validators.get_string(data, "student_id", "学号", max_len=12)
        )
        course_id = validators.validate_course_id(
            validators.get_string(data, "course_id", "课程号", max_len=10)
        )
        term = validators.validate_term(
            validators.get_string(
                data, "term", "学期", required=False, max_len=11
            ) or current_app.config["DEFAULT_TERM"]
        )
        exam_type = validators.validate_exam_type(
            validators.get_string(
                data, "exam_type", "考试类型", required=False, max_len=4
            ) or current_app.config["DEFAULT_EXAM_TYPE"]
        )
        score = validators.validate_score(
            validators.get_decimal(data, "score", "分数", min_value=0, max_value=100)
        )
        exam_time = validators.get_optional_date(data, "exam_time", "考试时间")
        comment = validators.get_string(
            data, "comment", "评语", required=False, max_len=200
        )
        return student_id, course_id, term, exam_type, score, exam_time, comment

    @staticmethod
    def _get_owned_course(teacher_id: str, course_id: str):
        """校验课程存在且归属当前教师"""
        course = CourseDao.find_by_id(course_id)
        if course is None:
            raise NotFoundException("课程不存在")
        if course.teacher_id != teacher_id:
            raise ForbiddenException("只能操作本人授课课程的成绩")
        return course

    @staticmethod
    def record_score(teacher_id: str, data: dict) -> dict:
        """录入成绩：学生必须已选课，且该记录尚未录入成绩"""
        (student_id, course_id, term, exam_type,
         score, exam_time, comment) = ScoreService._parse_params(data)

        ScoreService._get_owned_course(teacher_id, course_id)
        if StudentDao.find_by_id(student_id) is None:
            raise NotFoundException("学生不存在")

        record = ScoreDao.find(student_id, course_id, term, exam_type)
        if record is None:
            raise BusinessException("该学生未选修本课程，不能录入成绩")
        if record.score is not None:
            raise DuplicateException("该成绩已录入，请使用修改接口")

        ScoreDao.update_score(
            student_id, course_id, term, exam_type,
            score, exam_time, comment, teacher_id
        )
        commit()
        return ScoreDao.find(student_id, course_id, term, exam_type).to_dict()

    @staticmethod
    def update_score(teacher_id: str, data: dict) -> dict:
        """修改成绩：记录必须存在且已录入过成绩"""
        (student_id, course_id, term, exam_type,
         score, exam_time, comment) = ScoreService._parse_params(data)

        ScoreService._get_owned_course(teacher_id, course_id)
        record = ScoreDao.find(student_id, course_id, term, exam_type)
        if record is None:
            raise NotFoundException("成绩记录不存在")
        if record.score is None:
            raise BusinessException("该记录尚未录入成绩，请使用录入接口")

        ScoreDao.update_score(
            student_id, course_id, term, exam_type,
            score, exam_time, comment, teacher_id
        )
        commit()
        return ScoreDao.find(student_id, course_id, term, exam_type).to_dict()

    @staticmethod
    def list_my_scores(student_id: str) -> list:
        """学生查询本人成绩单"""
        return ScoreDao.list_by_student(student_id)

    @staticmethod
    def list_course_scores(teacher_id: str, course_id: str,
                           term: str = None) -> dict:
        """教师查询本人课程的学生成绩与统计信息"""
        course_id = validators.validate_course_id(course_id)
        course = ScoreService._get_owned_course(teacher_id, course_id)
        if term:
            term = validators.validate_term(term)

        stats = ScoreDao.course_stats(course_id, term)
        for key in ("avg_score", "max_score", "min_score"):
            if stats.get(key) is not None:
                stats[key] = round(float(stats[key]), 2)

        return {
            "course": {
                "course_id": course.course_id,
                "course_name": course.course_name,
                "credit": float(course.credit),
                "teacher_id": course.teacher_id
            },
            "stats": stats,
            "records": ScoreDao.list_by_course(course_id, term)
        }
