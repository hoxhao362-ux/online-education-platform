"""
课程数据访问对象
封装 course 表的增删改查与教师授课课程关联查询。
"""
from app.models.course import Course
from app.utils.db import execute, fetch_all, fetch_one


class CourseDao:
    """课程表数据访问"""

    @staticmethod
    def find_by_id(course_id: str) -> Course | None:
        """按课程号查询课程"""
        row = fetch_one(
            "SELECT * FROM dbo.course WHERE course_id = ?", (course_id,)
        )
        return Course.from_row(row) if row else None

    @staticmethod
    def exists(course_id: str) -> bool:
        """判断课程号是否已存在"""
        return fetch_one(
            "SELECT 1 AS flag FROM dbo.course WHERE course_id = ?", (course_id,)
        ) is not None

    @staticmethod
    def find_detail(course_id: str) -> dict | None:
        """查询课程详情（含授课教师姓名）"""
        return fetch_one(
            """
            SELECT c.course_id, c.course_name, c.credit, c.hours,
                   c.course_type, c.dept, c.prereq_id, c.teacher_id,
                   t.name AS teacher_name, c.status, c.created_at
            FROM dbo.course c
            LEFT JOIN dbo.teacher t ON c.teacher_id = t.teacher_id
            WHERE c.course_id = ?
            """,
            (course_id,)
        )

    @staticmethod
    def list(keyword: str = None, teacher_id: str = None,
             status: int = None) -> list:
        """课程列表查询（关联教师姓名，支持名称/课程号模糊搜索）"""
        sql = """
            SELECT c.course_id, c.course_name, c.credit, c.hours,
                   c.course_type, c.dept, c.prereq_id, c.teacher_id,
                   t.name AS teacher_name, c.status, c.created_at
            FROM dbo.course c
            LEFT JOIN dbo.teacher t ON c.teacher_id = t.teacher_id
            WHERE 1 = 1
        """
        params = []
        if status is not None:
            sql += " AND c.status = ?"
            params.append(status)
        if teacher_id:
            sql += " AND c.teacher_id = ?"
            params.append(teacher_id)
        if keyword:
            sql += " AND (c.course_name LIKE ? OR c.course_id LIKE ?)"
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        sql += " ORDER BY c.course_id"
        return fetch_all(sql, tuple(params))

    @staticmethod
    def create(course: Course) -> int:
        """新增课程"""
        return execute(
            """
            INSERT INTO dbo.course
                (course_id, course_name, credit, hours, course_type,
                 dept, prereq_id, teacher_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                course.course_id, course.course_name, course.credit,
                course.hours, course.course_type, course.dept,
                course.prereq_id, course.teacher_id, course.status
            )
        )

    @staticmethod
    def update(course_id: str, fields: dict) -> int:
        """修改课程信息（字段白名单由 Service 层控制）"""
        allowed = ("course_name", "credit", "hours", "course_type",
                   "dept", "prereq_id", "status")
        keys = [k for k in fields if k in allowed]
        if not keys:
            return 0
        sql = "UPDATE dbo.course SET " + ", ".join(f"{k} = ?" for k in keys)
        sql += " WHERE course_id = ?"
        params = tuple(fields[k] for k in keys) + (course_id,)
        return execute(sql, params)

    @staticmethod
    def delete(course_id: str) -> int:
        """删除课程"""
        return execute("DELETE FROM dbo.course WHERE course_id = ?", (course_id,))

    @staticmethod
    def count_scores(course_id: str) -> int:
        """统计课程下已有的选课/成绩记录数"""
        row = fetch_one(
            "SELECT COUNT(*) AS cnt FROM dbo.score WHERE course_id = ?", (course_id,)
        )
        return int(row["cnt"])

    @staticmethod
    def count_prereq_refs(course_id: str) -> int:
        """统计以该课程作为先修课的课程数"""
        row = fetch_one(
            "SELECT COUNT(*) AS cnt FROM dbo.course WHERE prereq_id = ?", (course_id,)
        )
        return int(row["cnt"])
