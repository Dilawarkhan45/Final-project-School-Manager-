"""Teacher comments: simple rules first, optional AI streaming on top."""

from __future__ import annotations

import logging
from typing import Iterator

from school import grading
from school.ai import ModelClient, build_prompt, start_stream
from school.models import Student

logger = logging.getLogger(__name__)

NO_MARKS_COMMENT = "No marks recorded yet, so there is nothing to comment on."
UNEVEN_GAP = 30.0  # highest minus lowest mark that counts as "uneven"


def comment_for_average(avg: float) -> str:
    """Pick the main sentence from the average."""
    if avg >= 90:
        return "Excellent in all subjects, keep it up."
    if avg >= 80:
        return "Very good results, keep working steadily."
    if avg >= 70:
        return "Good effort; a little more practice will lift your grades."
    if avg >= 60:
        return "Satisfactory, but more effort is needed."
    return "Needs urgent improvement; please ask your teachers for extra help."


def uneven_note(marks: list[float]) -> str:
    """Return an extra sentence when the marks vary a lot, else ''."""
    if max(marks) - min(marks) >= UNEVEN_GAP:
        return " Results are uneven, so revise the weaker subjects."
    return ""


def make_comment(student: Student) -> str:
    """Rule-based teacher comment from the student's marks."""
    if not student.marks:
        return NO_MARKS_COMMENT
    return comment_for_average(grading.average(student.marks)) + uneven_note(student.marks)


def comment_chunks(student: Student, client: ModelClient | None) -> Iterator[str]:
    """Generator: stream an AI comment piece by piece, else fall back to the rules."""
    if client is None or not student.marks:
        yield make_comment(student)
        return
    try:
        stream = start_stream(client, build_prompt(student))
    except Exception:  # any model failure -> fall back, the office must keep working
        logger.exception("AI comment failed, using rule-based comment")
        yield make_comment(student)
        return
    yield from stream
