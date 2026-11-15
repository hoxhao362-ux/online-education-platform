"""
数据库初始化脚本
1. 执行 sql/init_db.sql 创建 edu_platform 库与四张表（复用实验三模型）
2. 写入演示数据，并为演示账号设置 bcrypt 加密密码（统一为 123456）

用法（在项目根目录执行）：
    python scripts/init_db.py --force
"""
import argparse
import os
import sys

import bcrypt
import pyodbc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config  # noqa: E402
from app.utils.db import build_connection_string  # noqa: E402

SQL_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sql", "init_db.sql"
)
DEMO_PASSWORD = "123456"


def split_batches(script: str):
    """按 GO 分隔符拆分 T-SQL 批处理"""
    batch, batches = [], []
    for line in script.splitlines():
        if line.strip().upper() == "GO":
            if batch:
                batches.append("\n".join(batch))
                batch = []
        else:
            batch.append(line)
    if batch:
        batches.append("\n".join(batch))
    return batches


def main():
    parser = argparse.ArgumentParser(description="初始化在线教育平台数据库")
    parser.add_argument("--force", action="store_true", help="数据库已存在时强制重建（会清空数据）")
    args = parser.parse_args()

    master = pyodbc.connect(
        build_connection_string("master"), timeout=8, autocommit=True
    )
    cur = master.cursor()
    exists = cur.execute(
        "SELECT 1 FROM sys.databases WHERE name = ?", Config.DB_NAME
    ).fetchone()
    if exists and not args.force:
        print(f"数据库 {Config.DB_NAME} 已存在；如需重建请加 --force（会清空数据）")
        master.close()
        return 1
    master.close()

    with open(SQL_FILE, "r", encoding="utf-8") as f:
        batches = split_batches(f.read())

    conn = pyodbc.connect(
        build_connection_string("master"), timeout=8, autocommit=True
    )
    for batch in batches:
        conn.cursor().execute(batch)
    conn.close()
    print(f"已创建数据库 {Config.DB_NAME} 及 teacher / student / course / score 表")

    # ---------- 演示数据 ----------
    password_hash = bcrypt.hashpw(DEMO_PASSWORD.encode(), bcrypt.gensalt()).decode()

    conn = pyodbc.connect(build_connection_string(Config.DB_NAME), timeout=8, autocommit=False)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO dbo.teacher
            (teacher_id, name, gender, title, department, phone, email,
             id_card, hire_date, password_hash)
        VALUES
            ('T2001', N'张伟', N'男', N'教授', N'计算机学院', '138****0001',
             'zhangwei@wit.edu.cn',
             EncryptByPassPhrase(N'edu_key', N'330304198001011234'), '2010-09-01', ?),
            ('T2002', N'李娜', N'女', N'副教授', N'计算机学院', '139****0002',
             'lina@wit.edu.cn',
             EncryptByPassPhrase(N'edu_key', N'330304198505052345'), '2014-07-15', ?)
        """, password_hash, password_hash
    )

    cur.execute(
        """
        INSERT INTO dbo.student
            (student_id, name, gender, birth_date, id_card, phone, email,
             enroll_year, major, class_name, status, password_hash)
        VALUES
            ('202301010001', N'王小明', N'男', '2005-03-12',
             EncryptByPassPhrase(N'edu_key', N'330304200503121234'),
             '137****1001', 'wxm@stu.wit.edu.cn', 2023, N'软件工程', N'软工2301', 1, ?),
            ('202301010002', N'赵敏', N'女', '2005-07-20',
             EncryptByPassPhrase(N'edu_key', N'330304200507201234'),
             '137****1002', 'zhaomin@stu.wit.edu.cn', 2023, N'软件工程', N'软工2301', 1, ?),
            ('202301010003', N'孙浩', N'男', '2004-11-02',
             EncryptByPassPhrase(N'edu_key', N'330304200411021234'),
             '137****1003', 'sunhao@stu.wit.edu.cn', 2023, N'计算机科学', N'计科2302', 1, ?)
        """, password_hash, password_hash, password_hash
    )

    cur.execute(
        """
        INSERT INTO dbo.course
            (course_id, course_name, credit, hours, course_type, dept,
             prereq_id, teacher_id, status)
        VALUES
            ('C001', N'数据库原理与应用', 4.0, 64, N'必修', N'计算机学院', NULL, 'T2001', 1),
            ('C002', N'软件设计与体系结构', 3.0, 48, N'必修', N'计算机学院', NULL, 'T2002', 1),
            ('C003', N'数据结构', 4.0, 64, N'必修', N'计算机学院', NULL, 'T2001', 1)
        """
    )

    cur.execute(
        """
        INSERT INTO dbo.score
            (student_id, course_id, term, exam_type, score, exam_time,
             [comment], recorder_id)
        VALUES
            ('202301010001', 'C001', '2025-2026-1', N'期末', 92.50, '2026-01-10', N'掌握扎实', 'T2001'),
            ('202301010002', 'C001', '2025-2026-1', N'期末', 85.00, '2026-01-10', N'良好', 'T2001'),
            ('202301010003', 'C001', '2025-2026-1', N'期末', 78.00, '2026-01-10', N'基本掌握', 'T2001'),
            ('202301010001', 'C002', '2025-2026-1', N'期末', 88.00, '2026-01-12', N'设计思路清晰', 'T2002'),
            ('202301010002', 'C002', '2025-2026-1', N'期末', NULL, NULL, NULL, NULL),
            ('202301010003', 'C003', '2025-2026-1', N'期末', NULL, NULL, NULL, NULL)
        """
    )
    conn.commit()

    counts = {}
    for table in ("teacher", "student", "course", "score"):
        counts[table] = cur.execute(f"SELECT COUNT(*) FROM dbo.{table}").fetchval()
    conn.close()

    print("演示数据写入完成：" + "，".join(f"{k}={v}" for k, v in counts.items()))
    print(f"演示账号密码统一为 {DEMO_PASSWORD}：")
    print("  教师：T2001 / T2002    学生：202301010001 / 202301010002 / 202301010003")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
