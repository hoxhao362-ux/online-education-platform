"""
成绩数据访问对象
封装 score 表的选课记录维护、成绩录入/修改与多表关联查询。
score 同时承载选课关系：score 为 NULL 表示已选课未录入成绩。
"""
from app.models.score import Score
from app.utils.db import execute, fetch_all, fetch_one


class ScoreDao:
    """成绩/选课表数据访问"""

    @staticmethod
    def find(student_id: str, course_id: str, term: str,
             exam_type: str) -> Score | None:
        """按复合主键查询一条成绩记录"""
        row = fetch_one(
            """
            SELECT * FROM dbo.score
            WHERE student_id = ? AND course_id = ? AND term = ? AND exam_type = ?
            """,
            (student_id, course_id, term, exam_type)
        )
        return Score.from_row(row) if row else None

    @staticmethod
    def find_by_course_term(student_id: str, course_id: str,
                            term: str) -> Score | None:
        """查询学生在某学期是否已选过某课程（用于重复选课校验）"""
        row = fetch_one(
            """
            SELECT TOP 1 * FROM dbo.score
            WHERE student_id = ? AND course_id = ? AND term = ?
            """,
            (student_id, course_id, term)
        )
        return Score.from_row(row) if row else None

    @staticmethod
    def exists_by_course(student_id: str, course_id: str) -> bool:
        """判断学生是否已选过某课程（任意学期）"""
        return fetch_one(
            """
            SELECT 1 AS flag FROM dbo.score
            WHERE student_id = ? AND course_id = ?
            """,
            (student_id, course_id)
        ) is not None

    @staticmethod
    def create_selection(student_id: str, course_id: str,
                         term: str, exam_type: str) -> int:
        """新增选课记录（成绩为空）"""
        return execute(
            """
            INSERT INTO dbo.score (student_id, course_id, term, exam_type, score)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (student_id, course_id, term, exam_type)
        )

    @staticmethod
    def update_score(student_id: str, course_id: str, term: str, exam_type: str,
                     score, exam_time, comment, recorder_id: str) -> int:
        """录入/修改成绩，同时记录录入教师"""
        return execute(
            """
            UPDATE dbo.score
            SET score = ?, exam_time = ?, [comment] = ?, recorder_id = ?
            WHERE student_id = ? AND course_id = ? AND term = ? AND exam_type = ?
            """,
            (score, exam_time, comment, recorder_id,
             student_id, course_id, term, exam_type)
        )

    @staticmethod
    def list_by_student(student_id: str) -> list:
        """查询学生成绩单（学生 × 课程 × 成绩三表关联）"""
        return fetch_all(
            """
            SELECT sc.student_id, s.name AS student_name,
                   sc.course_id, c.course_name, c.credit, c.course_type,
                   c.teacher_id, t.name AS teacher_name,
                   sc.term, sc.exam_type, sc.score, sc.exam_time,
                   sc.[comment], sc.recorder_id
            FROM dbo.score sc
            JOIN dbo.student s ON sc.student_id = s.student_id
            JOIN dbo.course c ON sc.course_id = c.course_id
            LEFT JOIN dbo.teacher t ON c.teacher_id = t.teacher_id
            WHERE sc.student_id = ?
            ORDER BY sc.term, sc.course_id, sc.exam_type
            """,
            (student_id,)
        )

    @staticmethod
    def list_by_course(course_id: str, term: str = None) -> list:
        """查询课程下所有学生的选课与成绩"""
        sql = """
            SELECT sc.student_id, s.name AS student_name, s.class_name,
                   sc.course_id, sc.term, sc.exam_type, sc.score,
                   sc.exam_time, sc.[comment], sc.recorder_id
            FROM dbo.score sc
            JOIN dbo.student s ON sc.student_id = s.student_id
            WHERE sc.course_id = ?
        """
        params = [course_id]
        if term:
            sql += " AND sc.term = ?"
            params.append(term)
        sql += " ORDER BY s.class_name, sc.student_id, sc.exam_type"
        return fetch_all(sql, tuple(params))

    @staticmethod
    def course_stats(course_id: str, term: str = None) -> dict:
        """课程成绩统计：人数、平均分、最高分、最低分（多表关联 + 聚合）"""
        sql = """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN score IS NOT NULL THEN 1 ELSE 0 END) AS scored,
                   AVG(score) AS avg_score,
                   MAX(score) AS max_score,
                   MIN(score) AS min_score
            FROM dbo.score
            WHERE course_id = ?
        """
        params = [course_id]
        if term:
            sql += " AND term = ?"
            params.append(term)
        return fetch_one(sql, tuple(params))

    @staticmethod
    def list_courses_by_student(student_id: str) -> list:
        """查询学生已选课程（选课 × 课程 × 教师关联）"""
        return fetch_all(
            """
            SELECT sc.course_id, c.course_name, c.credit, c.course_type,
                   c.dept, t.name AS teacher_name,
                   sc.term, sc.exam_type, sc.score
            FROM dbo.score sc
            JOIN dbo.course c ON sc.course_id = c.course_id
            LEFT JOIN dbo.teacher t ON c.teacher_id = t.teacher_id
            WHERE sc.student_id = ?
            ORDER BY sc.term, sc.course_id
            """,
            (student_id,)
        )

    @staticmethod
    def list_teachers_by_course(course_id: str) -> list:
        """查询课程的授课教师信息（用于权限归属校验）"""
        return fetch_all(
            """
            SELECT c.course_id, c.teacher_id, t.name AS teacher_name
            FROM dbo.course c
            LEFT JOIN dbo.teacher t ON c.teacher_id = t.teacher_id
            WHERE c.course_id = ?
            """,
            (course_id,)
        )
