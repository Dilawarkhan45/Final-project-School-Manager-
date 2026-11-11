"""Text output: report cards and the class ranking."""

from __future__ import annotations

from school import grading
from school.models import Student

NO_MARKS_TEXT = "none yet"


def format_mark(mark: float) -> str:
    """Show 85.0 as '85' and 72.5 as '72.5'."""
    return f"{mark:g}"


def result_fields(student: Student) -> tuple[str, str, str]:
    """Return (marks, average, grade) as display text."""
    if not student.marks:
        return NO_MARKS_TEXT, "-", "N/A"
    avg = grading.average(student.marks)
    marks_text = ", ".join(format_mark(mark) for mark in student.marks)
    return marks_text, f"{avg:.2f}", grading.letter_grade(avg)


def format_report_card(student: Student) -> str:
    """Build the report card for one student."""
    marks_text, average_text, grade_text = result_fields(student)
    lines = [
        "-" * 30,
        "REPORT CARD",
        f"Name   : {student.name}",
        f"Roll   : {student.roll_number}",
        f"Marks  : {marks_text}",
        f"Average: {average_text}",
        f"Grade  : {grade_text}",
        "-" * 30,
    ]
    return "\n".join(lines)


def ranking_row(position: int, student: Student) -> str:
    """One line of the ranking table."""
    _, average_text, grade_text = result_fields(student)
    return (
        f"{position}. {student.name} (roll {student.roll_number}) "
        f"- average {average_text}, grade {grade_text}"
    )


def format_ranking(ranked: list[Student]) -> str:
    """Build the class ranking from an already-sorted list."""
    if not ranked:
        return "No students yet."
    rows = [ranking_row(position, student) for position, student in enumerate(ranked, start=1)]
    return "\n".join(["CLASS RANKING", *rows])
