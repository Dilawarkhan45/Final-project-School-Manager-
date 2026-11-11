"""Business rules: adding students, adding marks, ranking."""

from __future__ import annotations

import logging

from school import grading
from school.errors import (
    DuplicateStudentError,
    InvalidMarkError,
    StudentNotFoundError,
    ValidationError,
)
from school.models import Student

logger = logging.getLogger(__name__)

MIN_MARK = 0.0
MAX_MARK = 100.0


def clean_name(name: str) -> str:
    """Strip the name and make sure it is not empty."""
    cleaned = name.strip()
    if not cleaned:
        raise ValidationError("Name cannot be empty.")
    return cleaned


def check_roll_number(students: list[Student], roll_number: int) -> None:
    """Raise if the roll number is not positive or is already taken."""
    if roll_number <= 0:
        raise ValidationError("Roll number must be a positive number.")
    if any(student.roll_number == roll_number for student in students):
        raise DuplicateStudentError(f"Roll number {roll_number} already exists.")


def get_student(students: list[Student], roll_number: int) -> Student:
    """Find a student by roll number."""
    for student in students:
        if student.roll_number == roll_number:
            return student
    raise StudentNotFoundError(f"No student with roll number {roll_number}.")


def add_student(students: list[Student], name: str, roll_number: int) -> Student:
    """Create a student and add them to the list."""
    cleaned = clean_name(name)
    check_roll_number(students, roll_number)
    student = Student(name=cleaned, roll_number=roll_number)
    students.append(student)
    logger.info("Added student %s (roll %d)", cleaned, roll_number)
    return student


def validate_mark(mark: float) -> float:
    """Return the mark if it is between 0 and 100, otherwise raise."""
    if not MIN_MARK <= mark <= MAX_MARK:  # also rejects NaN
        raise InvalidMarkError(f"Mark {mark} must be between 0 and 100.")
    return mark


def parse_marks(text: str) -> list[float]:
    """Turn text like '85 90, 78' into a list of validated marks."""
    tokens = text.replace(",", " ").split()
    if not tokens:
        raise InvalidMarkError("Enter at least one mark.")
    marks: list[float] = []
    for token in tokens:
        try:
            value = float(token)
        except ValueError:
            raise InvalidMarkError(f"'{token}' is not a number.") from None
        marks.append(validate_mark(value))
    return marks


def add_marks(students: list[Student], roll_number: int, marks: list[float]) -> Student:
    """Append marks to an existing student."""
    student = get_student(students, roll_number)
    student.marks.extend(validate_mark(mark) for mark in marks)
    logger.info("Added %d mark(s) to roll %d", len(marks), roll_number)
    return student


def rank_students(students: list[Student]) -> list[Student]:
    """Return students sorted by average, highest first (ties by name)."""
    return sorted(
        students,
        key=lambda student: (-grading.average(student.marks), student.name.lower()),
    )
