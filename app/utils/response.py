"""
统一响应封装工具
所有 Controller 接口均调用此模块返回格式统一的 JSON 响应。

响应格式：
{
    "code": 200,
    "message": "success",
    "data": { ... }
}
"""
from datetime import date, datetime, time
from decimal import Decimal

from flask import jsonify


def _jsonable(value):
    """递归转换 Decimal / 日期等不可直接序列化的类型"""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def success(data=None, message: str = "success", code: int = 200):
    """
    返回成功响应
    :param data:    响应数据（字典、列表等可序列化对象）
    :param message: 提示信息
    :param code:    HTTP 状态码
    """
    return jsonify({
        "code": code,
        "message": message,
        "data": _jsonable(data)
    }), code


def fail(message: str = "操作失败", code: int = 400, data=None):
    """
    返回失败响应
    :param message: 错误提示信息
    :param code:    HTTP 状态码
    :param data:    可选附加信息（如字段校验错误详情）
    """
    return jsonify({
        "code": code,
        "message": message,
        "data": _jsonable(data)
    }), code
