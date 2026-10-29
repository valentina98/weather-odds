"""Downloads into the raw cache: only what is missing, retried when a server is busy."""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

import requests

from weather_odds import __version__

USER_AGENT = f"weather-odds/{__version__} (github.com/valentina98/weather-odds)"
RETRY_STATUS = {429, 500, 502, 503, 504}


class DownloadError(RuntimeError):
    """A source answered, but not with the data asked for."""


class Session(Protocol):
    def get(self, url: str, params: dict[str, Any] | None = None, timeout: float = ...) -> requests.Response: ...


class Downloader:
    def __init__(self, session: Session | None = None, retries: int = 4, pause: float = 5.0):
        if session is None:
            session = requests.Session()
            session.headers["User-Agent"] = USER_AGENT
        self.session = session
        self.retries = retries
        self.pause = pause
        self.retried = 0  # requests repeated because a server was busy or unreachable

    def get(self, url: str, params: dict[str, Any] | None = None, timeout: float = 120) -> requests.Response:
        """GET with retries on connection errors and busy servers, waiting longer each time."""
        for attempt in range(self.retries + 1):
            last = attempt == self.retries
            try:
                response = self.session.get(url, params=params, timeout=timeout)
            except requests.ConnectionError:
                if last:
                    raise
            else:
                if response.status_code not in RETRY_STATUS or last:
                    return response
            self.retried += 1
            time.sleep(self.pause * 2**attempt)
        raise AssertionError("unreachable")

    def wait(self, seconds: float) -> None:
        """Pause between requests to a host that asks for gentle use (skipped when pause is 0, as in tests)."""
        if self.pause:
            time.sleep(seconds)

    def fetch(
        self,
        url: str,
        path: Path,
        params: dict[str, Any] | None = None,
        refresh: bool = False,
        timeout: float = 120,
        check: Callable[[bytes], bool] | None = None,
    ) -> bool:
        """Save url to path unless it is already there. Returns whether a file was written.

        A 404 means the source has no file (e.g. no data that year): nothing is written, and the
        file is not asked for again unless refresh is set (which callers do for the current year).
        check() can reject a response that is not the data, such as an error page sent with HTTP 200.
        """
        none = path.with_name(path.name + ".none")  # remembers a 404 so it is not asked again
        if not refresh and (path.exists() or none.exists()):
            return False
        response = self.get(url, params, timeout)
        if response.status_code == 404:
            if not refresh:
                none.parent.mkdir(parents=True, exist_ok=True)
                none.touch()
            return False
        if response.status_code != 200:
            raise DownloadError(f"{url}: HTTP {response.status_code}")
        if check is not None and not check(response.content):
            raise DownloadError(f"{url}: unexpected content {response.content[:80]!r}")
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(path.name + ".part")
        partial.write_bytes(response.content)
        os.replace(partial, path)
        return True
