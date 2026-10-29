"""Stand-ins for a requests.Session and for the ERA5 bucket, so tests run without network."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pandas as pd
import requests

from weather_odds.sources import era5

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


FILLED_UNTIL = pd.Timestamp("2026-10-24", tz="UTC")  # ERA5 runs a few days behind


class FakeReader:
    def __init__(self, shape, values):
        self.shape = shape
        self.values = np.asarray(values, dtype=float)

    def __getitem__(self, key):
        return self.values.reshape(1, 1, -1) if self.values.ndim else np.array([[self.values]])


class FakeBucket:
    """2020 as a whole-year file; 2026 as chunks, filled until FILLED_UNTIL."""

    def __init__(self):
        self.read = []

    def years(self, variable):
        return {2020}

    def exists(self, path):
        chunk = int(path.rsplit("_", 1)[1].removesuffix(".om"))
        return pd.Timestamp(chunk * era5.CHUNK_HOURS * 3600, unit="s", tz="UTC").year == 2026

    def reader(self, path):
        self.read.append(path)
        if path.endswith("HSURF.om"):
            return FakeReader((721, 1440), 300.0)
        variable = path.split("/")[1]
        if "year_2020" in path:
            hours = 366 * 24
            if variable == "precipitation":
                return FakeReader(None, np.where(np.arange(hours) == 5, 1.0, 0.0))
            return FakeReader(None, np.full(hours, 10.0))
        chunk = int(path.rsplit("_", 1)[1].removesuffix(".om"))
        times = pd.date_range(pd.Timestamp(chunk * era5.CHUNK_HOURS * 3600, unit="s", tz="UTC"), periods=504, freq="h")
        return FakeReader(None, np.where(times < FILLED_UNTIL, 20.0, np.nan))
