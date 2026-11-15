"""
课程管理业务（教师权限）
教师只能新增、编辑、下架、删除本人授课的课程；
学生仅可查询开放课程。
"""
from app.dao.course_dao import CourseDao
from app.models.course import Course
from app.utils import validators
from app.utils.db import commit
from app.utils.exceptions import (
    BusinessException, ConflictException, DuplicateException,
    ForbiddenException, NotFoundException
)


class CourseService:
    """课程模块业务逻辑"""

    @staticmethod
    def list_courses(keyword: str = None, teacher_id: str = None,
                     status: int = None) -> list:
        """课程列表查询（公开接口默认只返回开课状态）"""
        return CourseDao.list(keyword=keyword, teacher_id=teacher_id, status=status)

    @staticmethod
    def get_course(course_id: str) -> dict:
        """课程详情"""
        course_id = validators.validate_course_id(course_id)
        detail = CourseDao.find_detail(course_id)
        if detail is None:
            raise NotFoundException("课程不存在")
        return detail

    @staticmethod
    def list_teacher_courses(teacher_id: str) -> list:
        """查询教师本人授课的全部课程（含已下架）"""
        return CourseDao.list(teacher_id=teacher_id)

    @staticmethod
    def create_course(teacher_id: str, data: dict) -> dict:
        """新增课程：课程号唯一、学分/学时/类型校验、先修课必须存在"""
        course_id = validators.validate_course_id(
            validators.get_string(data, "course_id", "课程号", max_len=10)
        )
        course_name = validators.get_string(data, "course_name", "课程名称", max_len=60)
        credit = validators.get_decimal(
            data, "credit", "学分", min_value=0.1, max_value=10
        )
        hours = validators.get_int(data, "hours", "学时", min_value=1, max_value=1000)
        course_type = validators.validate_course_type(
            validators.get_string(data, "course_type", "课程类型", max_len=4)
        )
        dept = validators.get_string(data, "dept", "开课院系", required=False, max_len=50)
        prereq_id = validators.get_string(
            data, "prereq_id", "先修课程号", required=False, max_len=10
        )
        status = validators.get_int(
            data, "status", "课程状态", required=False, min_value=0, max_value=1
        )
        if prereq_id:
            prereq_id = validators.validate_course_id(prereq_id)
            if prereq_id == course_id:
                raise BusinessException("先修课程不能是课程本身")
            if not CourseDao.exists(prereq_id):
                raise NotFoundException("先修课程不存在")

        if CourseDao.exists(course_id):
            raise DuplicateException("课程号已存在")

        course = Course(
            course_id=course_id, course_name=course_name, credit=credit,
            hours=hours, course_type=course_type, dept=dept,
            prereq_id=prereq_id, teacher_id=teacher_id,
            status=status if status is not None else 1
        )
        CourseDao.create(course)
        commit()
        return CourseDao.find_detail(course_id)

    @staticmethod
    def update_course(teacher_id: str, course_id: str, data: dict) -> dict:
        """编辑课程：必须先校验课程归属当前教师"""
        course_id = validators.validate_course_id(course_id)
        course = CourseDao.find_by_id(course_id)
        if course is None:
            raise NotFoundException("课程不存在")
        if course.teacher_id != teacher_id:
            raise ForbiddenException("只能修改本人授课的课程")

        fields = {}
        course_name = validators.get_string(
            data, "course_name", "课程名称", required=False, max_len=60
        )
        if course_name is not None:
            fields["course_name"] = course_name
        credit = validators.get_decimal(
            data, "credit", "学分", required=False, min_value=0.1, max_value=10
        )
        if credit is not None:
            fields["credit"] = credit
        hours = validators.get_int(
            data, "hours", "学时", required=False, min_value=1, max_value=1000
        )
        if hours is not None:
            fields["hours"] = hours
        course_type = validators.get_string(
            data, "course_type", "课程类型", required=False, max_len=4
        )
        if course_type is not None:
            fields["course_type"] = validators.validate_course_type(course_type)
        dept = validators.get_string(
            data, "dept", "开课院系", required=False, max_len=50
        )
        if dept is not None:
            fields["dept"] = dept
        prereq_id = validators.get_string(
            data, "prereq_id", "先修课程号", required=False, max_len=10
        )
        if prereq_id is not None:
            prereq_id = validators.validate_course_id(prereq_id)
            if prereq_id == course_id:
                raise BusinessException("先修课程不能是课程本身")
            if not CourseDao.exists(prereq_id):
                raise NotFoundException("先修课程不存在")
            fields["prereq_id"] = prereq_id
        status = validators.get_int(
            data, "status", "课程状态", required=False, min_value=0, max_value=1
        )
        if status is not None:
            fields["status"] = status

        if not fields:
            raise BusinessException("没有需要修改的字段")

        CourseDao.update(course_id, fields)
        commit()
        return CourseDao.find_detail(course_id)

    @staticmethod
    def delete_course(teacher_id: str, course_id: str) -> dict:
        """删除课程：有选课/成绩或被其他课程引用时禁止删除，建议改为下架"""
        course_id = validators.validate_course_id(course_id)
        course = CourseDao.find_by_id(course_id)
        if course is None:
            raise NotFoundException("课程不存在")
        if course.teacher_id != teacher_id:
            raise ForbiddenException("只能删除本人授课的课程")
        if CourseDao.count_scores(course_id) > 0:
            raise ConflictException("该课程已有学生选课或成绩记录，不能删除，请改为下架")
        if CourseDao.count_prereq_refs(course_id) > 0:
            raise ConflictException("该课程已被其他课程设为先修课程，不能删除")

        CourseDao.delete(course_id)
        commit()
        return {"course_id": course_id}
