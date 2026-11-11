"""Saving and loading students as JSON."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from school.errors import StorageError
from school.models import Student

logger = logging.getLogger(__name__)


def save_students(students: list[Student], path: Path) -> None:
    """Write all students to a JSON file."""
    payload = {"students": [student.to_dict() for student in students]}
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError as error:
        raise StorageError(f"Could not save to {path}: {error}") from error
    logger.info("Saved %d student(s) to %s", len(students), path)


def load_students(path: Path) -> list[Student]:
    """Read students from a JSON file; a missing file means an empty school."""
    if not path.exists():
        logger.info("%s not found, starting empty", path)
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        students = [Student.from_dict(item) for item in payload["students"]]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise StorageError(f"Could not read {path}: {error}") from error
    logger.info("Loaded %d student(s) from %s", len(students), path)
    return students


def backup_corrupt_file(path: Path) -> Path:
    """Move an unreadable data file aside so it is not overwritten."""
    backup = path.with_suffix(path.suffix + ".bak")
    try:
        path.replace(backup)
    except OSError as error:
        raise StorageError(f"Could not back up {path}: {error}") from error
    logger.warning("Moved unreadable data file to %s", backup)
    return backup
