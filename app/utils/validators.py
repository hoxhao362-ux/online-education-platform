"""
参数校验工具
Controller 层统一调用，所有校验失败均抛出 BusinessException（HTTP 400），
保证业务层不直接处理原始请求数据。
"""
import re
from datetime import date
from decimal import Decimal, InvalidOperation

from flask import request

from app.utils.exceptions import BusinessException

# ---------- 业务枚举 ----------
GENDERS = ("男", "女")
COURSE_TYPES = ("必修", "选修", "实践")
EXAM_TYPES = ("期中", "期末", "补考", "重修")

# ---------- 格式正则 ----------
STUDENT_ID_RE = re.compile(r"^\d{12}$")
TEACHER_ID_RE = re.compile(r"^[A-Za-z]\d{3,9}$")
COURSE_ID_RE = re.compile(r"^[A-Za-z0-9]{2,10}$")
TERM_RE = re.compile(r"^\d{4}-\d{4}-[12]$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def require_json() -> dict:
    """获取并校验 JSON 请求体"""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise BusinessException("请求体必须为 JSON 对象")
    return data


def get_string(data: dict, key: str, label: str, required: bool = True,
               min_len: int = 1, max_len: int = 100) -> str | None:
    """读取字符串参数，自动去除首尾空格并校验长度"""
    value = data.get(key)
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise BusinessException(f"{label}不能为空")
        return None
    if not isinstance(value, str):
        raise BusinessException(f"{label}必须为字符串")
    value = value.strip()
    if not (min_len <= len(value) <= max_len):
        raise BusinessException(f"{label}长度需在 {min_len}~{max_len} 个字符之间")
    return value


def get_int(data: dict, key: str, label: str, required: bool = True,
            min_value: int = None, max_value: int = None) -> int | None:
    """读取整数参数并校验范围"""
    value = data.get(key)
    if value is None or value == "":
        if required:
            raise BusinessException(f"{label}不能为空")
        return None
    if isinstance(value, bool):
        raise BusinessException(f"{label}必须为整数")
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise BusinessException(f"{label}必须为整数")
    if isinstance(value, float) and not value.is_integer():
        raise BusinessException(f"{label}必须为整数")
    if min_value is not None and number < min_value:
        raise BusinessException(f"{label}不能小于 {min_value}")
    if max_value is not None and number > max_value:
        raise BusinessException(f"{label}不能大于 {max_value}")
    return number


def get_decimal(data: dict, key: str, label: str, required: bool = True,
                min_value: float = None, max_value: float = None) -> Decimal | None:
    """读取数值参数（学分、分数）并校验范围"""
    value = data.get(key)
    if value is None or value == "":
        if required:
            raise BusinessException(f"{label}不能为空")
        return None
    if isinstance(value, bool):
        raise BusinessException(f"{label}必须为数值")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError):
        raise BusinessException(f"{label}必须为数值")
    if not number.is_finite():
        raise BusinessException(f"{label}必须为有效数值")
    if min_value is not None and number < Decimal(str(min_value)):
        raise BusinessException(f"{label}不能小于 {min_value}")
    if max_value is not None and number > Decimal(str(max_value)):
        raise BusinessException(f"{label}不能大于 {max_value}")
    return number


def get_optional_date(data: dict, key: str, label: str):
    """读取可选日期参数（YYYY-MM-DD）"""
    value = get_string(data, key, label, required=False, max_len=10)
    if value is None:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise BusinessException(f"{label}格式应为 YYYY-MM-DD")


def validate_password(password: str) -> str:
    """密码强度校验：6~32 位，且同时包含字母和数字"""
    if not (6 <= len(password) <= 32):
        raise BusinessException("密码长度需在 6~32 位之间")
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise BusinessException("密码必须同时包含字母和数字")
    return password


def validate_gender(gender: str) -> str:
    """性别只能是 男 / 女"""
    if gender not in GENDERS:
        raise BusinessException("性别只能为 男 或 女")
    return gender


def validate_email(email: str | None) -> str | None:
    """邮箱格式校验（可选字段）"""
    if email is None:
        return None
    if len(email) > 60 or not EMAIL_RE.match(email):
        raise BusinessException("邮箱格式不正确")
    return email


def validate_student_id(student_id: str) -> str:
    """学号格式：12 位数字（与 CHAR(12) 主键一致）"""
    if not STUDENT_ID_RE.match(student_id):
        raise BusinessException("学号必须为 12 位数字")
    return student_id


def validate_teacher_id(teacher_id: str) -> str:
    """工号格式：字母开头 + 3~9 位数字，最长 10 位"""
    teacher_id = teacher_id.upper()
    if not TEACHER_ID_RE.match(teacher_id):
        raise BusinessException("工号格式应为字母开头加 3~9 位数字，如 T2001")
    return teacher_id


def validate_course_id(course_id: str) -> str:
    """课程号格式：2~10 位字母或数字"""
    course_id = course_id.upper()
    if not COURSE_ID_RE.match(course_id):
        raise BusinessException("课程号应为 2~10 位字母或数字")
    return course_id


def validate_term(term: str) -> str:
    """学期格式：YYYY-YYYY-N（N 为 1 或 2）"""
    if not TERM_RE.match(term):
        raise BusinessException("学期格式应为 YYYY-YYYY-1 或 YYYY-YYYY-2")
    return term


def validate_exam_type(exam_type: str) -> str:
    """考试类型校验"""
    if exam_type not in EXAM_TYPES:
        raise BusinessException("考试类型只能为 期中/期末/补考/重修")
    return exam_type


def validate_course_type(course_type: str) -> str:
    """课程类型校验"""
    if course_type not in COURSE_TYPES:
        raise BusinessException("课程类型只能为 必修/选修/实践")
    return course_type


def validate_score(value: Decimal) -> Decimal:
    """分数范围校验：0~100"""
    if value < 0 or value > 100:
        raise BusinessException("分数必须在 0~100 之间")
    return value
