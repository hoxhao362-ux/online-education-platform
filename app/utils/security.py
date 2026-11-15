"""
密码安全工具
使用 bcrypt 对密码进行单向哈希存储，数据库中不保存明文密码。
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """生成 bcrypt 密码哈希"""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """校验明文密码与哈希是否匹配"""
    if not plain_password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), password_hash.encode("utf-8")
        )
    except ValueError:
        # 哈希格式非法时不向调用方暴露细节
        return False
