"""Reading the API key from a .env file (no extra dependency needed)."""

from __future__ import annotations

import os
from pathlib import Path

ENV_FILE = Path(".env")
API_KEY_NAME = "ANTHROPIC_API_KEY"


def parse_env_line(line: str) -> tuple[str, str] | None:
    """Parse 'KEY=value'; return None for blank lines, comments and junk."""
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        return None
    key, value = stripped.split("=", 1)
    return key.strip(), value.strip().strip('"').strip("'")


def load_env_file(path: Path) -> dict[str, str]:
    """Read a .env file into a dict; a missing file gives an empty dict."""
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_env_line(line)
        if parsed:
            values[parsed[0]] = parsed[1]
    return values


def get_api_key(env_path: Path = ENV_FILE) -> str | None:
    """Return the API key from .env, falling back to the environment."""
    key = load_env_file(env_path).get(API_KEY_NAME) or os.environ.get(API_KEY_NAME)
    return key or None
