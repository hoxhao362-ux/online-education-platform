"""实体类包：Student / Teacher / Course / Score"""
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.course import Course
from app.models.score import Score

__all__ = ["Student", "Teacher", "Course", "Score"]
