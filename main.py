"""Entry point: python main.py"""

from __future__ import annotations

import logging

from school.cli import run

LOG_FILE = "school.log"


def configure_logging() -> None:
    """Send log messages to a file so they do not clutter the menu."""
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    configure_logging()
    run()


if __name__ == "__main__":
    main()
