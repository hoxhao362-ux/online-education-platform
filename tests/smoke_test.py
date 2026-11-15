"""
接口冒烟测试
覆盖注册登录、课程管理、选课、成绩录入/修改/查询、角色越权与参数校验。

运行（项目根目录）：
    python tests/smoke_test.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402
from app.utils.db import build_connection_string  # noqa: E402
import pyodbc  # noqa: E402

TEST_STUDENT_ID = "202301019999"
TEST_TEACHER_ID = "T9001"
TEST_COURSE_ID = "C900"
DEMO_PASSWORD = "123456"
TERM = Config.DEFAULT_TERM


def cleanup():
    """清理测试产生的数据，保证脚本可重复执行"""
    conn = pyodbc.connect(build_connection_string(), timeout=8, autocommit=False)
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM dbo.score WHERE student_id = ? OR (student_id = ? AND course_id = ?)",
        TEST_STUDENT_ID, "202301010002", "C003"
    )
    cur.execute("DELETE FROM dbo.score WHERE course_id = ?", TEST_COURSE_ID)
    cur.execute("DELETE FROM dbo.course WHERE course_id = ?", TEST_COURSE_ID)
    cur.execute("DELETE FROM dbo.student WHERE student_id = ?", TEST_STUDENT_ID)
    cur.execute("DELETE FROM dbo.teacher WHERE teacher_id = ?", TEST_TEACHER_ID)
    conn.commit()
    conn.close()


class ApiSmokeTest(unittest.TestCase):
    """按业务流程顺序执行的接口测试"""

    @classmethod
    def setUpClass(cls):
        cleanup()
        cls.app = create_app()
        cls.anon = cls.app.test_client()

        cls.student = cls.app.test_client()
        resp = cls.student.post("/api/auth/login",
                                json={"account": "202301010002", "password": DEMO_PASSWORD})
        assert resp.status_code == 200, resp.get_json()

        cls.teacher = cls.app.test_client()
        resp = cls.teacher.post("/api/auth/login",
                                json={"account": "T2001", "password": DEMO_PASSWORD})
        assert resp.status_code == 200, resp.get_json()

        cls.teacher2 = cls.app.test_client()
        resp = cls.teacher2.post("/api/auth/login",
                                 json={"account": "T2002", "password": DEMO_PASSWORD})
        assert resp.status_code == 200, resp.get_json()

    @classmethod
    def tearDownClass(cls):
        cleanup()

    def assert_status(self, response, expected):
        self.assertEqual(response.status_code, expected, response.get_json())
        return response.get_json()

    def test_01_health(self):
        """数据库连通性"""
        body = self.assert_status(self.anon.get("/api/health"), 200)
        self.assertEqual(body["data"]["database"], "connected")

    def test_02_student_register(self):
        """学生注册：成功、重复账号 409、弱密码 400"""
        payload = {
            "student_id": TEST_STUDENT_ID, "name": "测试学生", "gender": "男",
            "password": "test1234", "enroll_year": 2024,
            "email": "test_student@wit.edu.cn", "major": "软件工程", "class_name": "软工2401"
        }
        body = self.assert_status(
            self.anon.post("/api/auth/student/register", json=payload), 201
        )
        self.assertEqual(body["data"]["student_id"], TEST_STUDENT_ID)
        self.assertNotIn("password_hash", str(body))

        self.assert_status(
            self.anon.post("/api/auth/student/register", json=payload), 409
        )

        weak = dict(payload, student_id="202301019998", password="123456")
        self.assert_status(
            self.anon.post("/api/auth/student/register", json=weak), 400
        )

    def test_03_teacher_register(self):
        """教师注册成功"""
        payload = {
            "teacher_id": TEST_TEACHER_ID, "name": "测试教师", "gender": "女",
            "password": "test1234", "title": "讲师", "department": "计算机学院",
            "email": "test_teacher@wit.edu.cn"
        }
        body = self.assert_status(
            self.anon.post("/api/auth/teacher/register", json=payload), 201
        )
        self.assertEqual(body["data"]["teacher_id"], TEST_TEACHER_ID)
        self.assertNotIn("password_hash", str(body))

    def test_04_login_and_profile(self):
        """登录角色识别、错误密码 401、未登录 401"""
        body = self.assert_status(
            self.student.post("/api/auth/login",
                              json={"account": "202301010002", "password": DEMO_PASSWORD}),
            200
        )
        self.assertEqual(body["data"]["role"], "student")

        self.assert_status(
            self.anon.post("/api/auth/login",
                           json={"account": "202301010002", "password": "wrong123"}), 401
        )
        me = self.assert_status(self.student.get("/api/auth/me"), 200)
        self.assertEqual(me["data"]["user"]["name"], "赵敏")
        self.assert_status(self.anon.get("/api/auth/me"), 401)

    def test_05_role_guard(self):
        """角色权限：学生不能走教师接口，教师不能走学生接口"""
        self.assert_status(self.student.get("/api/courses/mine"), 403)
        self.assert_status(self.teacher.get("/api/enrollments/mine"), 403)
        self.assert_status(
            self.student.post("/api/courses", json={"course_id": "C901"}), 403
        )

    def test_06_course_crud(self):
        """课程新增、重复 409、非法学分 400、越权修改 403、删除成功"""
        payload = {
            "course_id": TEST_COURSE_ID, "course_name": "测试课程", "credit": 2.5,
            "hours": 32, "course_type": "选修", "dept": "计算机学院"
        }
        body = self.assert_status(
            self.teacher.post("/api/courses", json=payload), 201
        )
        self.assertEqual(body["data"]["teacher_id"], "T2001")

        self.assert_status(self.teacher.post("/api/courses", json=payload), 409)
        self.assert_status(
            self.teacher.post("/api/courses", json=dict(payload, course_id="C902", credit=99)), 400
        )
        self.assert_status(
            self.teacher2.put(f"/api/courses/{TEST_COURSE_ID}", json={"credit": 3}), 403
        )
        updated = self.assert_status(
            self.teacher.put(f"/api/courses/{TEST_COURSE_ID}", json={"credit": 3}),
            200
        )
        self.assertEqual(updated["data"]["credit"], 3.0)
        self.assert_status(self.anon.get("/api/courses/C404"), 404)
        self.assert_status(self.teacher.delete(f"/api/courses/{TEST_COURSE_ID}"), 200)

    def test_07_enrollment(self):
        """学生选课成功、重复选课 409、查询本人已选课程"""
        body = self.assert_status(
            self.student.post("/api/enrollments",
                              json={"course_id": "C003", "term": TERM}), 201
        )
        self.assertIsNone(body["data"]["score"])
        self.assert_status(
            self.student.post("/api/enrollments",
                              json={"course_id": "C003", "term": TERM}), 409
        )
        mine = self.assert_status(self.student.get("/api/enrollments/mine"), 200)
        self.assertIn("C003", [row["course_id"] for row in mine["data"]])

    def test_08_score_permission(self):
        """成绩权限与前置校验：非本人课程 403、未选课 400、分数越界 400"""
        payload = {
            "student_id": "202301010002", "course_id": "C003",
            "term": TERM, "exam_type": "期末", "score": 90
        }
        self.assert_status(self.teacher2.post("/api/scores", json=payload), 403)

        unselected = dict(payload, student_id="202301010001")
        self.assert_status(self.teacher.post("/api/scores", json=unselected), 400)

        invalid_score = dict(payload, score=101)
        self.assert_status(self.teacher.post("/api/scores", json=invalid_score), 400)

        self.assert_status(
            self.student.post("/api/scores", json=payload), 403
        )

    def test_09_score_flow(self):
        """成绩录入 201、重复录入 409、修改 200、教师统计与学生成绩单"""
        payload = {
            "student_id": "202301010002", "course_id": "C003",
            "term": TERM, "exam_type": "期末", "score": 90, "comment": "第一次录入"
        }
        self.assert_status(self.teacher.post("/api/scores", json=payload), 201)
        self.assert_status(self.teacher.post("/api/scores", json=payload), 409)

        changed = dict(payload, score=95, comment="复核后修改")
        body = self.assert_status(self.teacher.put("/api/scores", json=changed), 200)
        self.assertEqual(body["data"]["score"], 95.0)

        course_scores = self.assert_status(
            self.teacher.get(f"/api/scores/course/C003?term={TERM}"), 200
        )
        self.assertGreaterEqual(course_scores["data"]["stats"]["total"], 2)
        self.assertIsNotNone(course_scores["data"]["stats"]["avg_score"])

        mine = self.assert_status(self.student.get("/api/scores/mine"), 200)
        c003 = [row for row in mine["data"] if row["course_id"] == "C003"]
        self.assertEqual(c003[0]["score"], 95.0)

    def test_10_delete_course_with_records(self):
        """已有成绩的课程禁止删除（409），保证外键数据完整"""
        self.assert_status(self.teacher.delete("/api/courses/C001"), 409)

    def test_11_injection_and_secret(self):
        """SQL 注入账号无法登录，响应中不出现密码哈希"""
        body = self.assert_status(
            self.anon.post("/api/auth/login",
                           json={"account": "' OR 1=1--", "password": "x"}), 401
        )
        self.assertNotIn("password_hash", str(body))
        self.assertNotIn("$2b$", str(body))


if __name__ == "__main__":
    unittest.main(verbosity=2)
