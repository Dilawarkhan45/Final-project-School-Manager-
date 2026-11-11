"""Custom exceptions, so the menu can show a friendly message instead of crashing."""

from __future__ import annotations


class SchoolError(Exception):
    """Base class for every error the School Manager raises on purpose."""


class ValidationError(SchoolError):
    """The user typed something that is not acceptable (empty name, bad roll...)."""


class DuplicateStudentError(SchoolError):
    """A student with this roll number already exists."""


class StudentNotFoundError(SchoolError):
    """No student has this roll number."""


class InvalidMarkError(SchoolError):
    """A mark is not a number between 0 and 100."""


class StorageError(SchoolError):
    """The data file could not be read or written."""


class AIError(SchoolError):
    """The AI model failed or returned nothing."""
