"""
Score 实体类
映射数据表 score。该表同时承载"选课"关系：
    - score 为 None 表示学生已选课但成绩未录入
    - score 有值表示成绩已录入
主键为（student_id, course_id, term, exam_type）复合主键。
"""


class Score:
    """成绩实体，对应 score 数据表"""

    def __init__(self, student_id=None, course_id=None, term=None,
                 exam_type=None, score=None, exam_time=None, comment=None,
                 recorder_id=None, created_at=None, updated_at=None):
        """
        :param student_id:  学号（复合主键之一，外键 → student）
        :param course_id:   课程号（复合主键之一，外键 → course）
        :param term:        学期，如 2025-2026-1（复合主键之一）
        :param exam_type:   考试类型：期中/期末/补考/重修（复合主键之一）
        :param score:       分数（0~100，None 表示未录入）
        :param exam_time:   考试时间
        :param comment:     评语
        :param recorder_id: 录入人工号（外键 → teacher）
        :param created_at:  创建时间
        :param updated_at:  更新时间
        """
        self.student_id = student_id
        self.course_id = course_id
        self.term = term
        self.exam_type = exam_type
        self.score = score
        self.exam_time = exam_time
        self.comment = comment
        self.recorder_id = recorder_id
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        """转为字典（用于 JSON 响应）"""
        return {
            "student_id": self.student_id,
            "course_id": self.course_id,
            "term": self.term,
            "exam_type": self.exam_type,
            "score": float(self.score) if self.score is not None else None,
            "exam_time": str(self.exam_time) if self.exam_time else None,
            "comment": self.comment,
            "recorder_id": self.recorder_id,
            "created_at": str(self.created_at) if self.created_at else None
        }

    @classmethod
    def from_row(cls, row: dict):
        """由数据库字典行构造实体"""
        return cls(**row)

    def __repr__(self):
        return (f"<Score student_id={self.student_id} course_id={self.course_id} "
                f"term={self.term} score={self.score}>")
