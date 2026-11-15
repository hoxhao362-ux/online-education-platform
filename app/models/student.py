"""
Student 实体类
映射数据表 student，封装学生基础信息字段。
"""


class Student:
    """学生实体，对应 student 数据表"""

    def __init__(self, student_id=None, name=None, gender=None,
                 birth_date=None, id_card=None, phone=None, email=None,
                 enroll_year=None, major=None, class_name=None, status=1,
                 password_hash=None, created_at=None, updated_at=None):
        """
        :param student_id:    学号（主键，兼登录账号）
        :param name:          姓名
        :param gender:        性别（男/女）
        :param birth_date:    出生日期
        :param id_card:       身份证号密文（不对外暴露）
        :param phone:         手机号（掩码）
        :param email:         邮箱
        :param enroll_year:   入学年份
        :param major:         专业
        :param class_name:    班级
        :param status:        学籍状态（1~4）
        :param password_hash: bcrypt 密码哈希（不对外暴露）
        :param created_at:    创建时间
        :param updated_at:    更新时间
        """
        self.student_id = student_id
        self.name = name
        self.gender = gender
        self.birth_date = birth_date
        self.id_card = id_card
        self.phone = phone
        self.email = email
        self.enroll_year = enroll_year
        self.major = major
        self.class_name = class_name
        self.status = status
        self.password_hash = password_hash
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        """转为字典（用于 JSON 响应，不包含密码与身份证字段）"""
        return {
            "student_id": self.student_id,
            "name": self.name,
            "gender": self.gender,
            "birth_date": str(self.birth_date) if self.birth_date else None,
            "phone": self.phone,
            "email": self.email,
            "enroll_year": self.enroll_year,
            "major": self.major,
            "class_name": self.class_name,
            "status": self.status,
            "created_at": str(self.created_at) if self.created_at else None
        }

    @classmethod
    def from_row(cls, row: dict):
        """由数据库字典行构造实体"""
        return cls(**row)

    def __repr__(self):
        return f"<Student student_id={self.student_id} name={self.name}>"
