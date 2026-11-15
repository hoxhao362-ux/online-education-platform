"""
教师数据访问对象
封装 teacher 表的查询、注册、信息修改等基础操作。
"""
from app.models.teacher import Teacher
from app.utils.db import execute, fetch_one


class TeacherDao:
    """教师表数据访问"""

    @staticmethod
    def find_by_id(teacher_id: str) -> Teacher | None:
        """按工号查询教师（含密码哈希，供登录校验使用）"""
        row = fetch_one(
            "SELECT * FROM dbo.teacher WHERE teacher_id = ?", (teacher_id,)
        )
        return Teacher.from_row(row) if row else None

    @staticmethod
    def find_by_email(email: str) -> Teacher | None:
        """按邮箱查询教师（用于唯一性校验）"""
        row = fetch_one("SELECT * FROM dbo.teacher WHERE email = ?", (email,))
        return Teacher.from_row(row) if row else None

    @staticmethod
    def exists(teacher_id: str) -> bool:
        """判断工号是否已注册"""
        return fetch_one(
            "SELECT 1 AS flag FROM dbo.teacher WHERE teacher_id = ?", (teacher_id,)
        ) is not None

    @staticmethod
    def create(teacher: Teacher) -> int:
        """新增教师（注册）"""
        return execute(
            """
            INSERT INTO dbo.teacher
                (teacher_id, name, gender, title, department, phone,
                 email, hire_date, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                teacher.teacher_id, teacher.name, teacher.gender,
                teacher.title, teacher.department, teacher.phone,
                teacher.email, teacher.hire_date, teacher.password_hash
            )
        )

    @staticmethod
    def update_profile(teacher_id: str, fields: dict) -> int:
        """修改教师基础信息（字段白名单由 Service 层控制）"""
        allowed = ("name", "title", "department", "email")
        keys = [k for k in fields if k in allowed]
        if not keys:
            return 0
        sql = "UPDATE dbo.teacher SET " + ", ".join(f"{k} = ?" for k in keys)
        sql += " WHERE teacher_id = ?"
        params = tuple(fields[k] for k in keys) + (teacher_id,)
        return execute(sql, params)
