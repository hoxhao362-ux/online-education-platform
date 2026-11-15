"""
学生数据访问对象
封装 student 表的查询、注册、信息修改等基础操作。
"""
from app.models.student import Student
from app.utils.db import execute, fetch_all, fetch_one


class StudentDao:
    """学生表数据访问"""

    @staticmethod
    def find_by_id(student_id: str) -> Student | None:
        """按学号查询学生（含密码哈希，供登录校验使用）"""
        row = fetch_one(
            "SELECT * FROM dbo.student WHERE student_id = ?", (student_id,)
        )
        return Student.from_row(row) if row else None

    @staticmethod
    def find_by_email(email: str) -> Student | None:
        """按邮箱查询学生（用于唯一性校验）"""
        row = fetch_one("SELECT * FROM dbo.student WHERE email = ?", (email,))
        return Student.from_row(row) if row else None

    @staticmethod
    def exists(student_id: str) -> bool:
        """判断学号是否已注册"""
        return fetch_one(
            "SELECT 1 AS flag FROM dbo.student WHERE student_id = ?", (student_id,)
        ) is not None

    @staticmethod
    def create(student: Student) -> int:
        """新增学生（注册）"""
        return execute(
            """
            INSERT INTO dbo.student
                (student_id, name, gender, birth_date, phone, email,
                 enroll_year, major, class_name, status, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                student.student_id, student.name, student.gender,
                student.birth_date, student.phone, student.email,
                student.enroll_year, student.major, student.class_name,
                student.status, student.password_hash
            )
        )

    @staticmethod
    def update_profile(student_id: str, fields: dict) -> int:
        """修改学生基础信息（字段白名单由 Service 层控制）"""
        allowed = ("name", "email", "major", "class_name")
        keys = [k for k in fields if k in allowed]
        if not keys:
            return 0
        sql = "UPDATE dbo.student SET " + ", ".join(f"{k} = ?" for k in keys)
        sql += " WHERE student_id = ?"
        params = tuple(fields[k] for k in keys) + (student_id,)
        return execute(sql, params)

    @staticmethod
    def list_by_course(course_id: str) -> list:
        """查询选修某门课程的学生名单（教师查看选课情况）"""
        return fetch_all(
            """
            SELECT s.student_id, s.name, s.gender, s.major, s.class_name
            FROM dbo.score sc
            JOIN dbo.student s ON sc.student_id = s.student_id
            WHERE sc.course_id = ?
            ORDER BY s.class_name, s.student_id
            """,
            (course_id,)
        )
