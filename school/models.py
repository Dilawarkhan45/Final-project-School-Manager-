"""The Student dataclass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Student:
    name: str
    roll_number: int
    marks: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a plain dict that can be written as JSON."""
        return {
            "name": self.name,
            "roll_number": self.roll_number,
            "marks": list(self.marks),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Student:
        """Build a Student from a dict made by to_dict (raises on bad data)."""
        return cls(
            name=str(data["name"]),
            roll_number=int(data["roll_number"]),
            marks=[float(mark) for mark in data["marks"]],
        )
