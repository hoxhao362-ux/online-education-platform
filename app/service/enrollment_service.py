"""
选课业务（学生权限）
学生在开放课程中选课，校验课程状态与重复选课；
选课关系直接写入 score 表（score 为空表示未录入成绩）。
"""
from flask import current_app

from app.dao.course_dao import CourseDao
from app.dao.score_dao import ScoreDao
from app.utils import validators
from app.utils.db import commit
from app.utils.exceptions import BusinessException, DuplicateException, NotFoundException


class EnrollmentService:
    """选课模块业务逻辑"""

    @staticmethod
    def enroll(student_id: str, data: dict) -> dict:
        """学生选课：课程须存在且开放，同一学期不能重复选课"""
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

        course = CourseDao.find_by_id(course_id)
        if course is None:
            raise NotFoundException("课程不存在")
        if course.status != 1:
            raise BusinessException("该课程已下架，暂不可选")

        if ScoreDao.find_by_course_term(student_id, course_id, term) is not None:
            raise DuplicateException("该学期已选过该课程，请勿重复选课")

        ScoreDao.create_selection(student_id, course_id, term, exam_type)
        commit()

        return {
            "student_id": student_id,
            "course_id": course_id,
            "course_name": course.course_name,
            "teacher_id": course.teacher_id,
            "term": term,
            "exam_type": exam_type,
            "score": None
        }

    @staticmethod
    def list_my_courses(student_id: str) -> list:
        """查询本人已选课程及成绩状态"""
        return ScoreDao.list_courses_by_student(student_id)
