"""
用户认证业务
负责学生/教师注册、登录身份校验、个人资料查询与修改。
安全要点：密码 bcrypt 加密存储、账号唯一性校验、登录错误提示不区分账号是否存在。
"""
from app.dao.student_dao import StudentDao
from app.dao.teacher_dao import TeacherDao
from app.models.student import Student
from app.models.teacher import Teacher
from app.utils import validators
from app.utils.auth_helper import (
    ROLE_STUDENT, ROLE_TEACHER, set_login_session, clear_login_session,
    get_current_user
)
from app.utils.db import commit
from app.utils.exceptions import (
    BusinessException, DuplicateException, NotFoundException,
    UnauthorizedException
)
from app.utils.security import hash_password, verify_password


class AuthService:
    """用户身份模块业务逻辑"""

    # ---------- 注册 ----------
    @staticmethod
    def register_student(data: dict) -> dict:
        """学生注册：参数校验 → 账号唯一性 → 密码加密 → 入库"""
        student_id = validators.validate_student_id(
            validators.get_string(data, "student_id", "学号", max_len=12)
        )
        name = validators.get_string(data, "name", "姓名", max_len=30)
        gender = validators.validate_gender(
            validators.get_string(data, "gender", "性别", max_len=2)
        )
        password = validators.validate_password(
            validators.get_string(data, "password", "密码", max_len=32)
        )
        enroll_year = validators.get_int(
            data, "enroll_year", "入学年份", min_value=2000, max_value=2100
        )
        email = validators.validate_email(
            validators.get_string(data, "email", "邮箱", required=False, max_len=60)
        )
        major = validators.get_string(data, "major", "专业", required=False, max_len=50)
        class_name = validators.get_string(
            data, "class_name", "班级", required=False, max_len=30
        )

        if StudentDao.exists(student_id):
            raise DuplicateException("该学号已注册，请直接登录")
        if email and StudentDao.find_by_email(email):
            raise DuplicateException("该邮箱已被使用")

        student = Student(
            student_id=student_id, name=name, gender=gender, email=email,
            enroll_year=enroll_year, major=major, class_name=class_name,
            status=1, password_hash=hash_password(password)
        )
        StudentDao.create(student)
        commit()
        return student.to_dict()

    @staticmethod
    def register_teacher(data: dict) -> dict:
        """教师注册：参数校验 → 账号唯一性 → 密码加密 → 入库"""
        teacher_id = validators.validate_teacher_id(
            validators.get_string(data, "teacher_id", "工号", max_len=10)
        )
        name = validators.get_string(data, "name", "姓名", max_len=30)
        gender = validators.validate_gender(
            validators.get_string(data, "gender", "性别", max_len=2)
        )
        password = validators.validate_password(
            validators.get_string(data, "password", "密码", max_len=32)
        )
        email = validators.validate_email(
            validators.get_string(data, "email", "邮箱", required=False, max_len=60)
        )
        title = validators.get_string(data, "title", "职称", required=False, max_len=20)
        department = validators.get_string(
            data, "department", "所属院系", required=False, max_len=50
        )
        hire_date = validators.get_optional_date(data, "hire_date", "入职日期")

        if TeacherDao.exists(teacher_id):
            raise DuplicateException("该工号已注册，请直接登录")
        if email and TeacherDao.find_by_email(email):
            raise DuplicateException("该邮箱已被使用")

        teacher = Teacher(
            teacher_id=teacher_id, name=name, gender=gender, title=title,
            department=department, email=email, hire_date=hire_date,
            password_hash=hash_password(password)
        )
        TeacherDao.create(teacher)
        commit()
        return teacher.to_dict()

    # ---------- 登录 / 退出 ----------
    @staticmethod
    def login(data: dict) -> dict:
        """
        登录：支持通过 role 指定身份；未指定时按账号格式自动识别。
        登录成功后写入 Session 并返回角色标识。
        """
        account = validators.get_string(data, "account", "账号", max_len=12)
        if not account.isdigit():
            account = account.upper()  # 工号统一大写，避免大小写差异
        password = validators.get_string(data, "password", "密码", max_len=32)

        role = data.get("role")
        if role is not None:
            if role not in (ROLE_STUDENT, ROLE_TEACHER):
                raise BusinessException("角色只能为 student 或 teacher")
        else:
            # 学号为 12 位数字，工号为字母开头，可据此自动识别身份
            role = ROLE_STUDENT if account.isdigit() else ROLE_TEACHER

        if role == ROLE_STUDENT:
            user = StudentDao.find_by_id(account)
            if user is None or not verify_password(password, user.password_hash):
                raise UnauthorizedException("账号或密码错误")
            user_info = user.to_dict()
        else:
            user = TeacherDao.find_by_id(account)
            if user is None or not verify_password(password, user.password_hash):
                raise UnauthorizedException("账号或密码错误")
            user_info = user.to_dict()

        set_login_session(
            user_id=account, role=role, username=account, name=user_info["name"]
        )
        return {"role": role, "user": user_info}

    @staticmethod
    def logout():
        """退出登录"""
        clear_login_session()

    # ---------- 个人资料 ----------
    @staticmethod
    def get_profile() -> dict:
        """查询当前登录用户资料"""
        user = get_current_user()
        if user["role"] == ROLE_STUDENT:
            student = StudentDao.find_by_id(user["user_id"])
            if student is None:
                raise NotFoundException("学生账号不存在")
            return {"role": ROLE_STUDENT, "user": student.to_dict()}
        teacher = TeacherDao.find_by_id(user["user_id"])
        if teacher is None:
            raise NotFoundException("教师账号不存在")
        return {"role": ROLE_TEACHER, "user": teacher.to_dict()}

    @staticmethod
    def update_profile(data: dict) -> dict:
        """修改当前登录用户基础信息（按角色限制可修改字段）"""
        user = get_current_user()
        fields = {}
        for key, label, max_len in (
            ("name", "姓名", 30), ("email", "邮箱", 60),
            ("major", "专业", 50), ("class_name", "班级", 30),
            ("title", "职称", 20), ("department", "所属院系", 50)
        ):
            value = validators.get_string(
                data, key, label, required=False, max_len=max_len
            )
            if value is not None:
                fields[key] = value
        if "email" in fields:
            validators.validate_email(fields["email"])
        if not fields:
            raise BusinessException("没有需要修改的字段")

        if user["role"] == ROLE_STUDENT:
            allowed = {"name", "email", "major", "class_name"}
            fields = {k: v for k, v in fields.items() if k in allowed}
            if not fields:
                raise BusinessException("学生仅可修改姓名、邮箱、专业、班级")
            StudentDao.update_profile(user["user_id"], fields)
        else:
            allowed = {"name", "email", "title", "department"}
            fields = {k: v for k, v in fields.items() if k in allowed}
            if not fields:
                raise BusinessException("教师仅可修改姓名、邮箱、职称、院系")
            TeacherDao.update_profile(user["user_id"], fields)

        commit()
        return AuthService.get_profile()
