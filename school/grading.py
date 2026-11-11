"""Average and letter-grade calculations."""

from __future__ import annotations

# (minimum average, letter), checked from the top down.
GRADE_BOUNDARIES: tuple[tuple[float, str], ...] = (
    (90.0, "A"),
    (80.0, "B"),
    (70.0, "C"),
    (60.0, "D"),
)
FAILING_GRADE = "F"


def average(marks: list[float]) -> float:
    """Return the mean of the marks, or 0.0 when there are none."""
    if not marks:
        return 0.0
    return sum(marks) / len(marks)


def letter_grade(avg: float) -> str:
    """Turn an average into a letter grade."""
    for minimum, letter in GRADE_BOUNDARIES:
        if avg >= minimum:
            return letter
    return FAILING_GRADE
