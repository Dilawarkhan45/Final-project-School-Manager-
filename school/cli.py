"""The menu: reads input, calls the service functions, prints results."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Iterator

from school import ai, comments, reports, service, storage
from school.errors import SchoolError, StorageError
from school.models import Student

logger = logging.getLogger(__name__)

DATA_FILE = Path("school.json")
EXIT_CHOICE = "5"
MENU_TEXT = """
===== SCHOOL MANAGER =====
1. Add student
2. Add marks
3. Show report card
4. Class ranking
5. Save and exit
6. Write comment (bonus)"""


def read_int(message: str) -> int:
    """Keep asking until the user types a whole number."""
    while True:
        text = input(message).strip()
        try:
            return int(text)
        except ValueError:
            print("Please enter a whole number.")


def handle_add_student(students: list[Student]) -> None:
    name = input("Student name: ")
    roll_number = read_int("Roll number: ")
    student = service.add_student(students, name, roll_number)
    print(f"Added {student.name} (roll {student.roll_number}).")


def handle_add_marks(students: list[Student]) -> None:
    roll_number = read_int("Roll number: ")
    service.get_student(students, roll_number)  # fail early if the roll is unknown
    marks = service.parse_marks(input("Marks out of 100 (e.g. 85 90 78): "))
    student = service.add_marks(students, roll_number, marks)
    print(f"{student.name} now has {len(student.marks)} mark(s).")


def handle_report_card(students: list[Student]) -> None:
    student = service.get_student(students, read_int("Roll number: "))
    print(reports.format_report_card(student))


def handle_ranking(students: list[Student]) -> None:
    print(reports.format_ranking(service.rank_students(students)))


def print_stream(chunks: Iterator[str]) -> None:
    """Print text pieces as they arrive, then end the line."""
    for chunk in chunks:
        print(chunk, end="", flush=True)
    print()


def handle_write_comment(students: list[Student]) -> None:
    student = service.get_student(students, read_int("Roll number: "))
    print_stream(comments.comment_chunks(student, ai.create_client()))


HANDLERS: dict[str, Callable[[list[Student]], None]] = {
    "1": handle_add_student,
    "2": handle_add_marks,
    "3": handle_report_card,
    "4": handle_ranking,
    "6": handle_write_comment,
}


def run_handler(handler: Callable[[list[Student]], None], students: list[Student]) -> None:
    """Run one menu action; show a message instead of crashing on any error."""
    try:
        handler(students)
    except SchoolError as error:
        print(f"Error: {error}")
    except (EOFError, KeyboardInterrupt):
        raise  # the user closed the input; run() handles it
    except Exception:
        logger.exception("Unexpected error in menu action")
        print("Something went wrong. Please try again.")


def menu_loop(students: list[Student]) -> None:
    """Show the menu until the user chooses to exit."""
    while True:
        print(MENU_TEXT)
        choice = input("Choose: ").strip()
        if choice == EXIT_CHOICE:
            return
        handler = HANDLERS.get(choice)
        if handler is None:
            print("Invalid choice. Please enter a number from 1 to 6.")
            continue
        run_handler(handler, students)


def load_students_safely(path: Path) -> list[Student]:
    """Load saved data; if the file is unreadable, keep a backup and start empty."""
    try:
        return storage.load_students(path)
    except StorageError as error:
        logger.error("%s", error)
        print(f"Warning: {error}")
        try:
            backup = storage.backup_corrupt_file(path)
            print(f"The old file was moved to {backup}. Starting with an empty school.")
        except StorageError as backup_error:
            print(f"Warning: {backup_error}")
        return []


def save_and_report(students: list[Student], path: Path) -> None:
    """Save everything and tell the user whether it worked."""
    try:
        storage.save_students(students, path)
    except StorageError as error:
        logger.error("%s", error)
        print(f"Error: {error}")
        return
    print(f"Saved {len(students)} student(s) to {path}. Goodbye!")


def run(data_file: Path = DATA_FILE) -> None:
    """Start the School Manager."""
    students = load_students_safely(data_file)
    try:
        menu_loop(students)
    except (EOFError, KeyboardInterrupt):
        print("\nInput closed, saving your work.")
    save_and_report(students, data_file)
