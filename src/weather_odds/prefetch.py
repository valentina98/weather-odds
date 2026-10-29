"""Download every source for the configured location and store the tidy tables (requirements F20, N2).

The sources live on different servers, so they are fetched at the same time,
each with its own connection.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

import requests

from weather_odds.cache import Cache
from weather_odds.config import Config
from weather_odds.download import Downloader, DownloadError
from weather_odds.sources import SOURCES


def prefetch(
    config: Config,
    names: Iterable[str] | None = None,
    refresh: bool = False,
    downloader: Callable[[], Downloader] = Downloader,
    today: date | None = None,
    log: Callable[[str], None] = print,
) -> list[str]:
    """Fetch what is missing and rebuild each source's table. Returns the sources that failed."""
    today = today or date.today()
    cache = Cache(config.data.cache_dir, config.location.slug)
    years = range(config.data.first_year, today.year + 1)
    names = list(names or SOURCES)

    def run(name: str) -> tuple[str, bool, str]:
        source, dl, start = SOURCES[name], downloader(), time.monotonic()
        note, ok = "", True
        try:
            written = source.fetch(dl, cache.raw(name), config.location, years, today, refresh)
        except (DownloadError, requests.RequestException) as e:
            note, ok, written = f" (download failed: {e}; keeping what is cached)", False, 0
        try:
            table = source.parse(cache.raw(name), config.location, today)
        except (ValueError, KeyError, OSError) as e:
            return name, False, f"{name}: cached files could not be read ({e}); run prefetch with --refresh"
        cache.save_table(name, table)
        span = f"{table.index.min():%d.%m.%Y}-{table.index.max():%d.%m.%Y}" if len(table) else "no data"
        busy = f", {dl.retried} retries" if dl.retried else ""
        files = f"{written} file{'' if written == 1 else 's'} in {time.monotonic() - start:.0f} s{busy}{note}"
        return name, ok, f"{name}: {files}; {len(table)} {source.kind} rows, {span}"

    failed = []
    with ThreadPoolExecutor(max_workers=len(names)) as pool:
        for future in as_completed([pool.submit(run, name) for name in names]):
            name, ok, message = future.result()
            log(message)
            if not ok:
                failed.append(name)
    return sorted(failed, key=names.index)
