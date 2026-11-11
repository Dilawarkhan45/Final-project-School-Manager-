"""Optional AI teacher comments: a model client, retries and streaming."""

from __future__ import annotations

import logging
from importlib.util import find_spec
from itertools import chain
from pathlib import Path
from typing import Iterator, Protocol

from school import grading
from school.config import ENV_FILE, get_api_key
from school.errors import AIError
from school.models import Student
from school.retry import retry

logger = logging.getLogger(__name__)

MODEL_NAME = "claude-sonnet-5-5"
MAX_TOKENS = 120
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1.0


class ModelClient(Protocol):
    """Anything that can stream a reply, in pieces, for a prompt (real or fake)."""

    def stream(self, prompt: str) -> Iterator[str]: ...


class AnthropicClient:
    """Real client; needs `pip install anthropic` and an API key."""

    def __init__(self, api_key: str, model: str = MODEL_NAME) -> None:
        self._api_key = api_key
        self._model = model

    def stream(self, prompt: str) -> Iterator[str]:
        import anthropic

        client = anthropic.Anthropic(api_key=self._api_key)
        with client.messages.stream(
            model=self._model,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": prompt}],
        ) as response:
            yield from response.text_stream


def build_prompt(student: Student) -> str:
    """Describe the student's results and ask for a short teacher comment."""
    avg = grading.average(student.marks)
    marks_text = ", ".join(f"{mark:g}" for mark in student.marks)
    return (
        "Write a short teacher comment (at most two sentences) for a school "
        f"report card. Student: {student.name}. Marks out of 100: {marks_text}. "
        f"Average: {avg:.1f}, grade {grading.letter_grade(avg)}. "
        "Be kind and honest. Reply with the comment only."
    )


@retry(attempts=RETRY_ATTEMPTS, delay=RETRY_DELAY)
def start_stream(client: ModelClient, prompt: str) -> Iterator[str]:
    """Open the stream and read its first piece, so connection errors are retried."""
    stream = iter(client.stream(prompt))
    first = next(stream, None)
    if first is None:
        raise AIError("The model returned an empty reply.")
    return chain([first], stream)


def create_client(env_path: Path = ENV_FILE) -> ModelClient | None:
    """Return a real client, or None when no key / library is available."""
    api_key = get_api_key(env_path)
    if not api_key:
        logger.info("No API key found; using rule-based comments")
        return None
    if find_spec("anthropic") is None:
        logger.warning("The 'anthropic' package is not installed; using rule-based comments")
        return None
    return AnthropicClient(api_key)
