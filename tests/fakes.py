"""A stand-in for requests.Session that serves canned answers and records what was asked."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import requests

Answer = bytes | int | Exception | Callable[[dict[str, Any] | None], bytes]


def response(status: int, content: bytes = b"") -> requests.Response:
    r = requests.Response()
    r.status_code = status
    r._content = content
    r.encoding = "utf-8"
    return r


class FakeSession:
    """Answers each URL from `routes`: bytes (HTTP 200), a status code, an exception, a list of
    those (used in turn), or a function of the query parameters. Unknown URLs get 404."""

    def __init__(self, routes: dict[str, Answer | list[Answer]]):
        self.routes = {url: list(a) if isinstance(a, list) else a for url, a in routes.items()}
        self.calls: list[tuple[str, dict[str, Any] | None]] = []

    def get(self, url: str, params: dict[str, Any] | None = None, timeout: float = 0) -> requests.Response:
        self.calls.append((url, params))
        answer = self.routes.get(url, 404)
        if isinstance(answer, list):
            answer = answer.pop(0) if len(answer) > 1 else answer[0]
        if isinstance(answer, Exception):
            raise answer
        if callable(answer):
            answer = answer(params)
        if isinstance(answer, int):
            return response(answer)
        return response(200, answer)
