"""
Course 实体类
映射数据表 course，封装课程基础信息字段。
"""


class Course:
    """课程实体，对应 course 数据表"""

    def __init__(self, course_id=None, course_name=None, credit=None,
                 hours=None, course_type=None, dept=None, prereq_id=None,
                 teacher_id=None, status=1, created_at=None, updated_at=None):
        """
        :param course_id:   课程号（主键）
        :param course_name: 课程名称
        :param credit:      学分（DECIMAL(3,1)）
        :param hours:       学时
        :param course_type: 课程类型（必修/选修/实践）
        :param dept:        开课院系
        :param prereq_id:   先修课程号（外键，自引用）
        :param teacher_id:  主讲教师工号（外键 → teacher.teacher_id）
        :param status:      课程状态（1 开课 / 0 停开）
        :param created_at:  创建时间
        :param updated_at:  更新时间
        """
        self.course_id = course_id
        self.course_name = course_name
        self.credit = credit
        self.hours = hours
        self.course_type = course_type
        self.dept = dept
        self.prereq_id = prereq_id
        self.teacher_id = teacher_id
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        """转为字典（用于 JSON 响应）"""
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "credit": float(self.credit) if self.credit is not None else None,
            "hours": self.hours,
            "course_type": self.course_type,
            "dept": self.dept,
            "prereq_id": self.prereq_id,
            "teacher_id": self.teacher_id,
            "status": self.status,
            "created_at": str(self.created_at) if self.created_at else None
        }

    @classmethod
    def from_row(cls, row: dict):
        """由数据库字典行构造实体"""
        return cls(**row)

    def __repr__(self):
        return f"<Course course_id={self.course_id} name={self.course_name}>"
