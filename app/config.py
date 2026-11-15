"""
全局配置 - 从 .env 读取数据库连接与 Flask 配置
数据库：Microsoft SQL Server（复用实验三 edu_platform 库）
"""
import os
from dotenv import load_dotenv

# 加载项目根目录下的 .env
load_dotenv()


class Config:
    """项目全局配置类"""

    # ---------- Flask ----------
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-please-change")
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    JSON_AS_ASCII = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # ---------- SQL Server 连接 ----------
    DB_DRIVER = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")
    # 命名管道方式可避开工作组环境下 TCP 集成认证失败的问题；
    # 也可改为 "127.0.0.1,1433" 等 TCP 地址
    DB_SERVER = os.getenv("DB_SERVER", r"np:\\.\pipe\MSSQL$WXYSQL\sql\query")
    DB_NAME = os.getenv("DB_NAME", "edu_platform")
    DB_TRUSTED = os.getenv("DB_TRUSTED_CONNECTION", "yes").lower() == "yes"
    DB_USER = os.getenv("DB_USER", "")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_TRUST_CERT = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes").lower() == "yes"

    # ---------- 业务默认值 ----------
    # 选课/成绩默认学期（演示数据使用 2025-2026-1）
    DEFAULT_TERM = os.getenv("DEFAULT_TERM", "2025-2026-1")
    DEFAULT_EXAM_TYPE = os.getenv("DEFAULT_EXAM_TYPE", "期末")
