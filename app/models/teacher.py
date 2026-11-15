"""
Teacher 实体类
映射数据表 teacher，封装教师基础信息字段。
"""


class Teacher:
    """教师实体，对应 teacher 数据表"""

    def __init__(self, teacher_id=None, name=None, gender=None,
                 title=None, department=None, phone=None, email=None,
                 id_card=None, hire_date=None, password_hash=None,
                 created_at=None, updated_at=None):
        """
        :param teacher_id:    工号（主键，兼登录账号）
        :param name:          姓名
        :param gender:        性别（男/女）
        :param title:         职称
        :param department:    所属院系
        :param phone:         手机号（掩码）
        :param email:         邮箱
        :param id_card:       身份证号密文（不对外暴露）
        :param hire_date:     入职日期
        :param password_hash: bcrypt 密码哈希（不对外暴露）
        :param created_at:    创建时间
        :param updated_at:    更新时间
        """
        self.teacher_id = teacher_id
        self.name = name
        self.gender = gender
        self.title = title
        self.department = department
        self.phone = phone
        self.email = email
        self.id_card = id_card
        self.hire_date = hire_date
        self.password_hash = password_hash
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        """转为字典（用于 JSON 响应，不包含密码与身份证字段）"""
        return {
            "teacher_id": self.teacher_id,
            "name": self.name,
            "gender": self.gender,
            "title": self.title,
            "department": self.department,
            "phone": self.phone,
            "email": self.email,
            "hire_date": str(self.hire_date) if self.hire_date else None,
            "created_at": str(self.created_at) if self.created_at else None
        }

    @classmethod
    def from_row(cls, row: dict):
        """由数据库字典行构造实体"""
        return cls(**row)

    def __repr__(self):
        return f"<Teacher teacher_id={self.teacher_id} name={self.name}>"
