"""Tests for the School Manager. Everything runs offline (the AI model is faked)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

import pytest

from school import ai, cli, comments, config, grading, reports, service, storage
from school.errors import (
    AIError,
    DuplicateStudentError,
    InvalidMarkError,
    StorageError,
    StudentNotFoundError,
    ValidationError,
)
from school.models import Student
from school.retry import retry


class FakeClient:
    """Stands in for the AI model: no network, no API key."""

    def __init__(self, chunks: list[str], fail_times: int = 0) -> None:
        self.chunks = chunks
        self.fail_times = fail_times
        self.calls = 0

    def stream(self, prompt: str) -> Iterator[str]:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ConnectionError("fake network failure")
        yield from self.chunks


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make retries instant."""
    monkeypatch.setattr("school.retry.time.sleep", lambda seconds: None)


@pytest.fixture
def students() -> list[Student]:
    return [
        Student("Ali", 1, [70, 80]),
        Student("Sara", 2, [95, 90, 100]),
        Student("Omar", 3, [50, 40]),
    ]


# ---------- grading ----------


def test_average_and_grade() -> None:
    assert grading.average([80, 90, 100]) == 90
    assert grading.average([]) == 0.0
    assert grading.letter_grade(95) == "A"
    assert grading.letter_grade(80) == "B"
    assert grading.letter_grade(59.9) == "F"


# ---------- service ----------


def test_add_student_rejects_bad_input() -> None:
    school: list[Student] = []
    service.add_student(school, "  Ayesha ", 1)
    assert school[0].name == "Ayesha"
    with pytest.raises(DuplicateStudentError):
        service.add_student(school, "Another", 1)
    with pytest.raises(ValidationError):
        service.add_student(school, "   ", 2)
    with pytest.raises(ValidationError):
        service.add_student(school, "Bilal", -5)


def test_marks_are_validated(students: list[Student]) -> None:
    assert service.parse_marks("85, 90 78.5") == [85.0, 90.0, 78.5]
    for bad in ("", "abc", "101", "-1", "nan"):
        with pytest.raises(InvalidMarkError):
            service.parse_marks(bad)
    with pytest.raises(StudentNotFoundError):
        service.add_marks(students, 99, [50])
    service.add_marks(students, 1, [100])
    assert students[0].marks == [70, 80, 100]


def test_ranking_highest_average_first(students: list[Student]) -> None:
    ranked = service.rank_students(students)
    assert [student.name for student in ranked] == ["Sara", "Ali", "Omar"]


# ---------- reports ----------


def test_report_card_and_empty_ranking(students: list[Student]) -> None:
    card = reports.format_report_card(students[1])
    assert "Sara" in card and "95" in card and "Average: 95.00" in card and "Grade  : A" in card
    assert "none yet" in reports.format_report_card(Student("New", 9))
    assert reports.format_ranking([]) == "No students yet."


# ---------- storage ----------


def test_save_and_load_round_trip(tmp_path: Path, students: list[Student]) -> None:
    path = tmp_path / "school.json"
    storage.save_students(students, path)
    assert storage.load_students(path) == students


def test_load_missing_and_corrupt_files(tmp_path: Path) -> None:
    assert storage.load_students(tmp_path / "missing.json") == []
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(StorageError):
        storage.load_students(broken)
    wrong_shape = tmp_path / "wrong.json"
    wrong_shape.write_text(json.dumps({"students": [{"name": "X"}]}), encoding="utf-8")
    with pytest.raises(StorageError):
        storage.load_students(wrong_shape)


# ---------- comments (rules) ----------


def test_rule_based_comments() -> None:
    assert comments.make_comment(Student("A", 1, [95, 92])) == "Excellent in all subjects, keep it up."
    assert "urgent" in comments.make_comment(Student("B", 2, [30, 40]))
    assert "uneven" in comments.make_comment(Student("C", 3, [100, 60]))
    assert comments.make_comment(Student("D", 4)) == comments.NO_MARKS_COMMENT


# ---------- comments (AI, mocked) ----------


def test_ai_comment_streams_chunks(students: list[Student]) -> None:
    client = FakeClient(["Great ", "work, ", "Sara!"])
    chunks = list(comments.comment_chunks(students[1], client))
    assert chunks == ["Great ", "work, ", "Sara!"]


def test_retry_recovers_after_failures(students: list[Student]) -> None:
    client = FakeClient(["Fine."], fail_times=2)
    assert "".join(comments.comment_chunks(students[0], client)) == "Fine."
    assert client.calls == 3


def test_ai_failure_falls_back_to_rules(students: list[Student]) -> None:
    client = FakeClient(["never used"], fail_times=99)
    result = "".join(comments.comment_chunks(students[1], client))
    assert result == comments.make_comment(students[1])
    assert client.calls == ai.RETRY_ATTEMPTS


def test_empty_ai_reply_is_an_error(students: list[Student]) -> None:
    with pytest.raises(AIError):
        ai.start_stream(FakeClient([]), "prompt")


def test_retry_decorator_gives_up_and_raises() -> None:
    calls: list[int] = []

    @retry(attempts=3, delay=0)
    def always_fails() -> None:
        calls.append(1)
        raise ValueError("nope")

    with pytest.raises(ValueError):
        always_fails()
    assert len(calls) == 3


def test_api_key_comes_from_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(config.API_KEY_NAME, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text('# comment\nANTHROPIC_API_KEY="secret-123"\n', encoding="utf-8")
    assert config.get_api_key(env_file) == "secret-123"
    assert config.get_api_key(tmp_path / "missing.env") is None


# ---------- the menu ----------


def run_with_inputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, answers: list[str]
) -> Path:
    """Run the menu with scripted keyboard input (no AI client)."""
    replies = iter(answers)

    def fake_input(prompt: str = "") -> str:
        try:
            return next(replies)
        except StopIteration:
            raise EOFError from None  # what input() does when stdin is closed

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(ai, "create_client", lambda *args, **kwargs: None)
    data_file = tmp_path / "school.json"
    cli.run(data_file)
    return data_file


def test_menu_survives_wrong_input_and_saves(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    data_file = run_with_inputs(
        monkeypatch,
        tmp_path,
        [
            "1", "Ayesha", "1",       # add student
            "1", "   ", "2",          # empty name -> error message
            "9",                      # invalid menu choice
            "banana",                 # not a number at all
            "2", "abc", "1", "90 80 x",   # roll typed badly, then bad marks
            "2", "1", "90 80 100",    # good marks
            "3", "1",                 # report card
            "4",                      # ranking
            "6", "1",                 # comment (rules only)
            "3", "42",                # unknown roll
            "5",                      # save and exit
        ],
    )
    output = capsys.readouterr().out
    assert "Invalid choice" in output
    assert "Please enter a whole number." in output
    assert "REPORT CARD" in output
    assert "Excellent in all subjects" in output
    assert "No student with roll number 42." in output
    saved = json.loads(data_file.read_text(encoding="utf-8"))
    assert saved["students"] == [{"name": "Ayesha", "roll_number": 1, "marks": [90.0, 80.0, 100.0]}]


def test_menu_saves_when_input_closes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Input runs out (EOF) right after adding a student: no crash, data still saved.
    data_file = run_with_inputs(monkeypatch, tmp_path, ["1", "Bilal", "7"])
    assert json.loads(data_file.read_text(encoding="utf-8"))["students"][0]["name"] == "Bilal"
