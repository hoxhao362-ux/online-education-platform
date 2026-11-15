-- ============================================================
-- 在线教育平台 学生/教师/课程/成绩 模块 建库建表脚本
-- 复用实验三物理模型，补充登录密码字段 password_hash
-- 目标数据库：Microsoft SQL Server 2025 (兼容 SQL Server 2019+)
-- ============================================================
IF DB_ID(N'edu_platform') IS NOT NULL
    DROP DATABASE edu_platform;
GO
CREATE DATABASE edu_platform;
GO
USE edu_platform;
GO

-- 1. 教师表 teacher -----------------------------------------
CREATE TABLE dbo.teacher (
    teacher_id    CHAR(10)        NOT NULL,              -- 工号（兼登录账号）
    name          NVARCHAR(30)    NOT NULL,              -- 姓名
    gender        NVARCHAR(2)     NOT NULL,              -- 性别
    title         NVARCHAR(20)        NULL,              -- 职称
    department    NVARCHAR(50)        NULL,              -- 所属院系
    phone         VARCHAR(20)         NULL,              -- 手机号（掩码）
    email         VARCHAR(60)         NULL,              -- 邮箱
    id_card       VARBINARY(128)      NULL,              -- 身份证号密文
    hire_date     DATE                NULL,              -- 入职日期
    password_hash NVARCHAR(100)   NOT NULL,              -- 登录密码（bcrypt 哈希）
    created_at    DATETIME2(0)    NOT NULL
        CONSTRAINT df_teacher_created DEFAULT SYSDATETIME(),
    updated_at    DATETIME2(0)    NOT NULL
        CONSTRAINT df_teacher_updated DEFAULT SYSDATETIME(),
    CONSTRAINT pk_teacher PRIMARY KEY (teacher_id),
    CONSTRAINT ck_teacher_gender CHECK (gender IN (N'男', N'女'))
);
CREATE UNIQUE INDEX uk_teacher_idcard ON dbo.teacher(id_card)
    WHERE id_card IS NOT NULL;
CREATE INDEX idx_teacher_name ON dbo.teacher(name);
GO

-- 2. 学生表 student -----------------------------------------
CREATE TABLE dbo.student (
    student_id    CHAR(12)        NOT NULL,              -- 学号（兼登录账号）
    name          NVARCHAR(30)    NOT NULL,              -- 姓名
    gender        NVARCHAR(2)     NOT NULL,              -- 性别
    birth_date    DATE                NULL,              -- 出生日期
    id_card       VARBINARY(128)      NULL,              -- 身份证号密文
    phone         VARCHAR(20)         NULL,              -- 手机号（掩码）
    email         VARCHAR(60)         NULL,              -- 邮箱
    enroll_year   SMALLINT        NOT NULL,              -- 入学年份
    major         NVARCHAR(50)        NULL,              -- 专业
    class_name    NVARCHAR(30)        NULL,              -- 班级
    status        TINYINT         NOT NULL
        CONSTRAINT df_student_status DEFAULT 1,          -- 学籍状态
    password_hash NVARCHAR(100)   NOT NULL,              -- 登录密码（bcrypt 哈希）
    created_at    DATETIME2(0)    NOT NULL
        CONSTRAINT df_student_created DEFAULT SYSDATETIME(),
    updated_at    DATETIME2(0)    NOT NULL
        CONSTRAINT df_student_updated DEFAULT SYSDATETIME(),
    CONSTRAINT pk_student PRIMARY KEY (student_id),
    CONSTRAINT ck_student_gender CHECK (gender IN (N'男', N'女')),
    CONSTRAINT ck_student_year CHECK (enroll_year BETWEEN 2000 AND 2100),
    CONSTRAINT ck_student_status CHECK (status BETWEEN 1 AND 4)
);
CREATE UNIQUE INDEX uk_student_idcard ON dbo.student(id_card)
    WHERE id_card IS NOT NULL;
CREATE UNIQUE INDEX uk_student_email ON dbo.student(email)
    WHERE email IS NOT NULL;
CREATE INDEX idx_student_name ON dbo.student(name);
CREATE INDEX idx_student_class ON dbo.student(class_name);
CREATE INDEX idx_student_major ON dbo.student(major);
GO

-- 3. 课程表 course ------------------------------------------
CREATE TABLE dbo.course (
    course_id     CHAR(10)        NOT NULL,              -- 课程号
    course_name   NVARCHAR(60)    NOT NULL,              -- 课程名称
    credit        DECIMAL(3,1)    NOT NULL,              -- 学分
    hours         SMALLINT        NOT NULL,              -- 学时
    course_type   NVARCHAR(4)     NOT NULL,              -- 必修/选修/实践
    dept          NVARCHAR(50)        NULL,              -- 开课院系
    prereq_id     CHAR(10)            NULL,              -- 先修课程号
    teacher_id    CHAR(10)            NULL,              -- 主讲教师工号
    status        TINYINT         NOT NULL
        CONSTRAINT df_course_status DEFAULT 1,           -- 1 开课 0 停开
    created_at    DATETIME2(0)    NOT NULL
        CONSTRAINT df_course_created DEFAULT SYSDATETIME(),
    updated_at    DATETIME2(0)    NOT NULL
        CONSTRAINT df_course_updated DEFAULT SYSDATETIME(),
    CONSTRAINT pk_course PRIMARY KEY (course_id),
    CONSTRAINT ck_course_type
        CHECK (course_type IN (N'必修', N'选修', N'实践')),
    CONSTRAINT ck_course_credit CHECK (credit > 0 AND credit <= 10),
    CONSTRAINT ck_course_hours  CHECK (hours > 0),
    CONSTRAINT ck_course_status CHECK (status IN (0, 1)),
    CONSTRAINT fk_course_teacher FOREIGN KEY (teacher_id)
        REFERENCES dbo.teacher(teacher_id) ON UPDATE CASCADE,
    CONSTRAINT fk_course_prereq FOREIGN KEY (prereq_id)
        REFERENCES dbo.course(course_id)
);
CREATE INDEX idx_course_name ON dbo.course(course_name);
CREATE INDEX idx_course_teacher ON dbo.course(teacher_id);
GO

-- 4. 成绩表 score（同时承载选课关系，score 为空表示已选课未录入成绩）----
CREATE TABLE dbo.score (
    student_id    CHAR(12)        NOT NULL,              -- 学号
    course_id     CHAR(10)        NOT NULL,              -- 课程号
    term          CHAR(11)        NOT NULL,              -- 学期
    exam_type     NVARCHAR(4)     NOT NULL,              -- 考试类型
    score         DECIMAL(5,2)        NULL,              -- 分数（0~100，空为未录入）
    exam_time     DATE                NULL,              -- 考试时间
    [comment]     NVARCHAR(200)       NULL,              -- 评语
    recorder_id   CHAR(10)            NULL,              -- 录入人工号
    created_at    DATETIME2(0)    NOT NULL
        CONSTRAINT df_score_created DEFAULT SYSDATETIME(),
    updated_at    DATETIME2(0)    NOT NULL
        CONSTRAINT df_score_updated DEFAULT SYSDATETIME(),
    CONSTRAINT pk_score
        PRIMARY KEY (student_id, course_id, term, exam_type),
    CONSTRAINT ck_score_exam_type
        CHECK (exam_type IN (N'期中', N'期末', N'补考', N'重修')),
    CONSTRAINT ck_score_range
        CHECK (score IS NULL OR (score >= 0 AND score <= 100)),
    CONSTRAINT fk_score_student FOREIGN KEY (student_id)
        REFERENCES dbo.student(student_id) ON UPDATE CASCADE,
    CONSTRAINT fk_score_course FOREIGN KEY (course_id)
        REFERENCES dbo.course(course_id) ON UPDATE CASCADE,
    -- 注意：SQL Server 禁止多重级联路径，录入人外键不设置 ON UPDATE CASCADE
    CONSTRAINT fk_score_recorder FOREIGN KEY (recorder_id)
        REFERENCES dbo.teacher(teacher_id)
);
CREATE INDEX idx_score_course ON dbo.score(course_id);
CREATE INDEX idx_score_term ON dbo.score(term);
GO

-- 5. 更新时间触发器 ------------------------------------------
CREATE TRIGGER trg_teacher_updated ON dbo.teacher AFTER UPDATE AS
BEGIN
    SET NOCOUNT ON;
    UPDATE t SET updated_at = SYSDATETIME()
    FROM dbo.teacher t JOIN inserted i ON t.teacher_id = i.teacher_id;
END;
GO
CREATE TRIGGER trg_student_updated ON dbo.student AFTER UPDATE AS
BEGIN
    SET NOCOUNT ON;
    UPDATE s SET updated_at = SYSDATETIME()
    FROM dbo.student s JOIN inserted i ON s.student_id = i.student_id;
END;
GO
CREATE TRIGGER trg_course_updated ON dbo.course AFTER UPDATE AS
BEGIN
    SET NOCOUNT ON;
    UPDATE c SET updated_at = SYSDATETIME()
    FROM dbo.course c JOIN inserted i ON c.course_id = i.course_id;
END;
GO
CREATE TRIGGER trg_score_updated ON dbo.score AFTER UPDATE AS
BEGIN
    SET NOCOUNT ON;
    UPDATE sc SET updated_at = SYSDATETIME()
    FROM dbo.score sc
    JOIN inserted i ON sc.student_id = i.student_id
        AND sc.course_id = i.course_id
        AND sc.term = i.term
        AND sc.exam_type = i.exam_type;
END;
GO

-- 6. 脱敏视图（敏感字段保护，供查询角色使用）----------------
CREATE VIEW dbo.v_student_masked AS
SELECT student_id, name, gender, major, class_name,
       CONCAT(LEFT(CONVERT(VARCHAR(20),
              DECRYPTBYPASSPHRASE(N'edu_key', id_card)), 6), '********',
              RIGHT(CONVERT(VARCHAR(20),
              DECRYPTBYPASSPHRASE(N'edu_key', id_card)), 4)) AS id_card_masked,
       CONCAT(LEFT(phone, 3), '****', RIGHT(phone, 4)) AS phone_masked
FROM dbo.student;
GO
