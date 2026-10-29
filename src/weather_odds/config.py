"""Configuration: one YAML file with the defaults the dashboard starts from (requirements F18, F19, N9).

Every setting stands alone: no value is derived from another, so changing one never
changes another (N9, D41). The shipped defaults are those of the specification
(docs/spec/methodology.md); config.example.yaml lists them all. API keys never go
in this file; v1 needs none (F21).
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

CONFIG_FILE = "config.yaml"
Band = Literal["night", "morning", "afternoon", "evening"]
BAND_HOURS: dict[str, tuple[int, int]] = {
    "night": (0, 6),
    "morning": (6, 12),
    "afternoon": (12, 18),
    "evening": (18, 24),
}


class ConfigError(ValueError):
    """The config file is missing, unreadable or has invalid values."""


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Location(_Model):
    name: str = "Plovdiv"
    latitude: float = Field(42.1333, ge=-90, le=90)
    longitude: float = Field(24.75, ge=-180, le=180)
    timezone: str = "Europe/Sofia"
    station: str = "15625"  # WMO id of the station whose measurements are used

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as e:
            raise ValueError(f"unknown time zone {v!r}") from e
        return v


class Statistics(_Model):
    """How past years become odds (methodology sections 2 and 3)."""

    years: int = Field(30, ge=1, le=100)  # the last N complete years
    last_year: int | None = Field(None, ge=1940)  # None: the last complete year
    trend_adjustment: bool = True
    pooling_days: int = Field(0, ge=0, le=15)  # +- days pooled around each date

    def span(self, today: date | None = None) -> tuple[int, int]:
        """First and last year of the reference period."""
        last = self.last_year if self.last_year is not None else (today or date.today()).year - 1
        return last - self.years + 1, last


class Rain(_Model):
    """Hourly rain factor: 1 below light_mm, light_factor up to heavy_mm, heavy_factor from heavy_mm."""

    light_mm: float = Field(0.2, gt=0)
    heavy_mm: float = Field(1.0, gt=0)
    light_factor: float = Field(0.5, ge=0, le=1)
    heavy_factor: float = Field(0.2, ge=0, le=1)

    @model_validator(mode="after")
    def _ordered(self) -> Rain:
        if self.light_mm >= self.heavy_mm:
            raise ValueError("light_mm must be below heavy_mm")
        if self.heavy_factor > self.light_factor:
            raise ValueError("heavy_factor must not exceed light_factor")
        return self


class RainCap(_Model):
    """A period with at least from_mm of rain in the chosen hours scores at most max_score."""

    from_mm: float = Field(gt=0)
    max_score: float = Field(ge=0, le=100)


class Thresholds(_Model):
    """The outdoor-weather scale's thresholds for one time band (methodology section 4)."""

    comfort: tuple[float, float] = (18.0, 26.0)  # deg C: no penalty inside this range
    cold_zero: float = 0.0  # deg C: the temperature factor reaches 0
    hot_zero: float = 38.0
    rain: Rain = Rain()
    rain_caps: tuple[RainCap, ...] = (RainCap(from_mm=1.0, max_score=59), RainCap(from_mm=5.0, max_score=39))
    gust_ok: float = Field(30.0, ge=0)  # km/h
    gust_zero: float = 75.0
    thunder_factor: float = Field(0.2, ge=0, le=1)

    @model_validator(mode="after")
    def _ordered(self) -> Thresholds:
        low, high = self.comfort
        if not self.cold_zero < low < high < self.hot_zero:
            raise ValueError("need cold_zero < comfort low < comfort high < hot_zero")
        if self.gust_ok >= self.gust_zero:
            raise ValueError("gust_ok must be below gust_zero")
        return self


class Classes(_Model):
    """Lowest score of each class; below poor is Bad."""

    great: float = 80
    good: float = 60
    fair: float = 40
    poor: float = 20

    @model_validator(mode="after")
    def _ordered(self) -> Classes:
        if not 0 < self.poor < self.fair < self.good < self.great <= 100:
            raise ValueError("need 0 < poor < fair < good < great <= 100")
        return self


class Scale(_Model):
    thresholds: Thresholds = Thresholds()
    # Per-band changes, e.g. {"evening": {"comfort": [15, 26]}}; anything unset comes from thresholds.
    bands: dict[Band, dict[str, Any]] = {}
    classes: Classes = Classes()

    @model_validator(mode="after")
    def _bands_valid(self) -> Scale:
        for band in self.bands:
            self.for_band(band)
        return self

    def for_band(self, band: Band) -> Thresholds:
        """The thresholds that score the hours of one time band."""
        if band not in BAND_HOURS:
            raise ValueError(f"unknown time band {band!r}")
        merged = _deep_merge(self.thresholds.model_dump(), self.bands.get(band, {}))
        return Thresholds.model_validate(merged)


class View(_Model):
    """What the dashboard shows first."""

    time_of_day: str = "daylight"  # or local hours "HH-HH", e.g. "18-22"
    granularity: Literal["day", "week", "month"] = "week"
    measure: Literal["chance", "average"] = "chance"
    colours: Literal["absolute", "relative"] = "absolute"

    @field_validator("time_of_day")
    @classmethod
    def _hours(cls, v: str) -> str:
        if v != "daylight":
            m = re.fullmatch(r"(\d{1,2})-(\d{1,2})", v)
            if not m or not 0 <= int(m[1]) < int(m[2]) <= 24:
                raise ValueError('use "daylight" or local hours like "18-22"')
        return v

    def hours(self) -> tuple[int, int] | None:
        """Start and end hour, or None for the daylight window."""
        if self.time_of_day == "daylight":
            return None
        start, end = self.time_of_day.split("-")
        return int(start), int(end)


class Data(_Model):
    """Where each variable comes from, in order of priority (D34, D37), and the download cache."""

    cache_dir: Path = Path(".cache")
    temperature: list[Literal["station", "era5"]] = ["station", "era5"]
    precipitation: list[Literal["era5"]] = ["era5"]
    wind_gusts: list[Literal["era5"]] = ["era5"]
    thunder: list[Literal["airport", "gsod"]] = ["airport", "gsod"]

    @field_validator("temperature", "precipitation", "wind_gusts", "thunder")
    @classmethod
    def _priority(cls, v: list[str]) -> list[str]:
        if not v or len(set(v)) != len(v):
            raise ValueError("list each source once, at least one")
        return v


class Config(_Model):
    location: Location = Location()
    statistics: Statistics = Statistics()
    scale: Scale = Scale()
    view: View = View()
    data: Data = Data()


def load_config(path: Path | None = None) -> Config:
    """Read a config file; without a path, ./config.yaml if it exists, else the defaults."""
    if path is None:
        path = Path(CONFIG_FILE)
        if not path.exists():
            return Config()
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as e:
        raise ConfigError(f"cannot read {path}: {e}") from e
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise ConfigError(f"{path}: expected sections like 'location:' at the top level")
    try:
        return Config.model_validate(raw)
    except ValidationError as e:
        raise ConfigError(f"{path}: {e}") from e


def dump_config(config: Config) -> str:
    """The settings as YAML, in the layout of config.example.yaml."""
    return yaml.safe_dump(config.model_dump(mode="json"), sort_keys=False, allow_unicode=True)


def _deep_merge(base: dict[str, Any], changes: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in changes.items():
        out[key] = _deep_merge(out[key], value) if isinstance(value, dict) and isinstance(out.get(key), dict) else value
    return out
