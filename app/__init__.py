"""
应用工厂
负责创建 Flask 应用、注册蓝图、注册统一异常处理与数据库生命周期管理。
"""
from flask import Flask, request
from werkzeug.exceptions import HTTPException

from app.config import Config
from app.utils.db import close_db, fetch_one
from app.utils.exceptions import BusinessException
from app.utils.response import fail, success


def create_app(config_class=Config) -> Flask:
    """创建并配置 Flask 应用"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.json.ensure_ascii = False  # 返回中文而不是 \uXXXX

    # 请求结束自动关闭数据库连接
    app.teardown_appcontext(close_db)

    _register_error_handlers(app)
    _register_blueprints(app)

    @app.after_request
    def add_security_headers(response):
        """代码评审补充：统一安全响应头，禁止缓存含个人信息的数据"""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/health")
    def health():
        """健康检查：验证应用与数据库连通性"""
        fetch_one("SELECT 1 AS ok")
        return success({"status": "ok", "database": "connected"})

    return app


def _register_blueprints(app: Flask):
    """注册各模块控制器蓝图"""
    from app.controller.auth_controller import auth_bp
    from app.controller.course_controller import course_bp
    from app.controller.enrollment_controller import enrollment_bp
    from app.controller.score_controller import score_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(enrollment_bp)
    app.register_blueprint(score_bp)


def _register_error_handlers(app: Flask):
    """统一异常处理：业务异常返回友好提示，未知异常不暴露底层细节"""

    @app.errorhandler(BusinessException)
    def handle_business_exception(error: BusinessException):
        return fail(error.message, error.code)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        return fail(error.description or "请求错误", error.code or 500)

    @app.errorhandler(Exception)
    def handle_unknown_exception(error: Exception):
        # 记录完整堆栈到日志，对外仅返回通用提示，避免泄露数据库/代码细节
        app.logger.exception("未处理异常: %s", error)
        return fail("服务器内部错误，请稍后重试", 500)
