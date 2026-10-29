"""The local cache: raw downloads per source, and the tidy tables parsed from them (Parquet).

Layout under the configured cache folder, per location:

    <cache_dir>/<location>/raw/<source>/...       files as downloaded
    <cache_dir>/<location>/tables/<source>.parquet

Nothing here is committed (N4); the folder is git-ignored.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


class Cache:
    def __init__(self, cache_dir: Path, location_slug: str):
        self.root = Path(cache_dir) / location_slug

    def raw(self, source: str) -> Path:
        return self.root / "raw" / source

    def table_path(self, source: str) -> Path:
        return self.root / "tables" / f"{source}.parquet"

    def save_table(self, source: str, table: pd.DataFrame) -> Path:
        path = self.table_path(source)
        path.parent.mkdir(parents=True, exist_ok=True)
        table.to_parquet(path)
        return path

    def load_table(self, source: str) -> pd.DataFrame | None:
        """The parsed table, or None before the first prefetch."""
        path = self.table_path(source)
        return pd.read_parquet(path) if path.exists() else None
