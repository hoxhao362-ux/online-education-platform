"""
数据库连接工具
- 统一根据配置拼装 ODBC 连接串
- Flask 请求内使用 flask.g 复用连接，请求结束自动关闭
- 脚本可直接调用 get_connection() 获取独立连接
"""
import pyodbc
from flask import g

from app.config import Config


def build_connection_string(database: str = None) -> str:
    """根据配置拼装 ODBC 连接字符串"""
    parts = [
        f"DRIVER={{{Config.DB_DRIVER}}}",
        f"SERVER={Config.DB_SERVER}",
        f"DATABASE={database or Config.DB_NAME}",
    ]
    if Config.DB_TRUSTED:
        parts.append("Trusted_Connection=yes")
    else:
        parts.append(f"UID={Config.DB_USER}")
        parts.append(f"PWD={Config.DB_PASSWORD}")
    if Config.DB_TRUST_CERT:
        parts.append("TrustServerCertificate=yes")
    return ";".join(parts)


def get_connection(database: str = None) -> pyodbc.Connection:
    """创建新连接（脚本/初始化使用）"""
    return pyodbc.connect(build_connection_string(database), timeout=8, autocommit=False)


def get_db() -> pyodbc.Connection:
    """获取当前请求的数据库连接（惰性创建）"""
    if "db" not in g:
        g.db = get_connection()
    return g.db


def close_db(exception=None):
    """请求结束时关闭连接；未提交的事务统一回滚"""
    db = g.pop("db", None)
    committed = g.pop("db_committed", False)
    if db is None:
        return
    try:
        if exception is not None or not committed:
            db.rollback()
    finally:
        db.close()


def commit():
    """提交当前请求事务"""
    get_db().commit()
    g.db_committed = True


def rollback():
    """回滚当前请求事务"""
    get_db().rollback()


def fetch_all(sql: str, params: tuple = ()) -> list:
    """执行查询并返回字典列表"""
    cursor = get_db().cursor()
    try:
        cursor.execute(sql, params)
        columns = [col[0] for col in cursor.description]
        # CHAR 类型定长字段会被填充空格，统一去除尾部空格
        return [
            {k: (v.rstrip() if isinstance(v, str) else v) for k, v in zip(columns, row)}
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()


def fetch_one(sql: str, params: tuple = ()) -> dict | None:
    """执行查询并返回单行字典"""
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql: str, params: tuple = ()) -> int:
    """执行增删改，返回受影响行数"""
    cursor = get_db().cursor()
    try:
        cursor.execute(sql, params)
        return cursor.rowcount
    finally:
        cursor.close()
