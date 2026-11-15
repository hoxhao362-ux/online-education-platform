# 在线教育平台 - Online Education Platform

## 项目简介
基于 Python Flask + SQL Server + MVC 三层架构实现的在线教育平台后端系统，
覆盖学生/教师注册登录、课程管理、学生选课、成绩录入与查询业务。
数据库复用《实验三：数据库设计与建模》的 `edu_platform` 模型（teacher / student / course / score）。

## 技术栈
- Python 3.10+
- Flask 3（蓝图、Session 鉴权）
- pyodbc + ODBC Driver 18 for SQL Server
- bcrypt（密码单向哈希）
- Microsoft SQL Server 2019+（本机验证版本：SQL Server 2025）

## 项目结构
```
online_education_platform/
├── run.py                    # 启动入口
├── requirements.txt
├── sql/init_db.sql           # 建库建表脚本（复用实验三物理模型）
├── scripts/init_db.py        # 建库 + 演示数据初始化
├── tests/smoke_test.py       # 接口冒烟测试
└── app/
    ├── __init__.py           # 应用工厂、蓝图注册、统一异常处理
    ├── config.py             # 配置（数据库、Session、业务默认值）
    ├── models/               # 实体类 Student / Teacher / Course / Score
    ├── dao/                  # 数据访问层
    ├── service/              # 业务逻辑层
    ├── controller/           # 控制层（Flask 蓝图）
    └── utils/                # 数据库、校验、密码、鉴权、响应、异常
```

## 分层职责
### Service 层
- 封装业务规则，调用一个或多个 DAO 完成业务组合
- 负责账号唯一性、密码加密、课程归属、重复选课、分数范围等校验
- 业务失败统一抛出 BusinessException 子类，不向 Controller 暴露数据库异常

## 快速启动

```bash
# 1. 启动 SQL Server 实例（Windows 服务）
Start-Service 'MSSQL$WXYSQL'

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置数据库连接（复制并修改 .env）
copy .env.example .env

# 4. 初始化数据库与演示数据（--force 会重建库）
python scripts/init_db.py --force

# 5. 启动服务
python run.py
```

默认地址：`http://127.0.0.1:5000`，健康检查：`GET /api/health`。

### 演示账号（密码统一为 123456）
| 角色 | 账号 |
| --- | --- |
| 教师 | T2001（张伟）、T2002（李娜） |
| 学生 | 202301010001、202301010002、202301010003 |

## 接口清单

### 用户认证
| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | /api/auth/student/register | 公开 | 学生注册 |
| POST | /api/auth/teacher/register | 公开 | 教师注册 |
| POST | /api/auth/login | 公开 | 登录并返回角色标识 |
| POST | /api/auth/logout | 公开 | 退出登录 |
| GET | /api/auth/me | 登录 | 当前用户资料 |
| PUT | /api/auth/profile | 登录 | 修改个人资料 |

### 课程管理
| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | /api/courses | 公开 | 开放课程列表 |
| GET | /api/courses/mine | 教师 | 本人授课课程 |
| GET | /api/courses/{course_id} | 公开 | 课程详情 |
| POST | /api/courses | 教师 | 新增课程 |
| PUT | /api/courses/{course_id} | 教师（本人课程） | 编辑课程 |
| DELETE | /api/courses/{course_id} | 教师（本人课程） | 删除课程 |

### 选课
| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | /api/enrollments | 学生 | 选课 |
| GET | /api/enrollments/mine | 学生 | 本人已选课程 |

### 成绩
| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | /api/scores | 教师（本人课程） | 录入成绩 |
| PUT | /api/scores | 教师（本人课程） | 修改成绩 |
| GET | /api/scores/mine | 学生 | 本人成绩单 |
| GET | /api/scores/course/{course_id} | 教师（本人课程） | 课程成绩与统计 |

## 接口返回规范
```json
{ "code": 200, "message": "success", "data": {} }
```
业务异常统一返回 400/401/403/404/409，未知异常返回 500 且不暴露数据库细节。

## 安全设计
- 密码使用 bcrypt 加盐哈希存储，任何响应均不返回密码字段
- 全部 SQL 使用参数化查询，防止 SQL 注入
- 基于 Session 的角色鉴权 + 资源归属校验，拦截学生越权与教师跨课程操作
- Controller 统一参数校验，Service 统一抛出业务异常
- 身份证号等敏感字段不通过接口收集与返回，数据库保留加密列与脱敏视图

## Git 分支规范
- `main`：主分支，保持稳定可运行
- `dev/dao`：实体类与 DAO 层（陈涛）
- `dev/service`：Service 业务层（王彭凯）
- `dev/controller`：Controller 层与测试（刘德宇）

## 提交规范
```
feat(模块): 功能描述
fix(模块): 修复描述
refactor(模块): 重构描述
test(模块): 测试描述
```

## 运行测试
```bash
python tests/smoke_test.py
```
