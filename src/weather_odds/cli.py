"""Command line: weather-odds [--config PATH] COMMAND.

Later milestones add export and validate (#19).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from weather_odds import __version__
from weather_odds.cache import Cache
from weather_odds.checks import check_fills, report
from weather_odds.config import Config, ConfigError, dump_config, load_config
from weather_odds.prefetch import prefetch
from weather_odds.sources import SOURCES
from weather_odds.table import MissingDataError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="weather-odds", description="Historical weather odds for planning time outdoors."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--config", type=Path, help="config file (default: ./config.yaml if it exists, else the built-in defaults)"
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    commands.add_parser("config", help="check the config and print the settings in effect")
    fetch = commands.add_parser("prefetch", help="download the data for the configured location into the cache")
    fetch.add_argument(
        "--sources", type=_source_list, default=None, help=f"comma-separated subset of: {', '.join(SOURCES)}"
    )
    fetch.add_argument("--refresh", action="store_true", help="download every file again")
    commands.add_parser("build", help="combine the downloaded sources into the hourly and daily tables")
    check = commands.add_parser(
        "check", help="test the gap fills, build the tables and compare them with the station's measurements"
    )
    check.add_argument("--output", type=Path, help="also write the report to this Markdown file")
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if args.command == "config":
        print(dump_config(config), end="")
    elif args.command == "prefetch":
        failed = prefetch(config, args.sources, refresh=args.refresh)
        if failed:
            print(f"error: {', '.join(failed)} could not be downloaded; run prefetch again later", file=sys.stderr)
            return 1
    elif args.command in ("build", "check"):
        try:
            return _build(config) if args.command == "build" else _check(config, args.output)
        except MissingDataError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
    return 0


def _build(config: Config) -> int:
    from weather_odds.table import build

    build(config)
    return 0


def _check(config: Config, output: Path | None) -> int:
    from weather_odds.station_checks import compare_with_station, to_markdown

    cache = Cache(config.data.cache_dir, config.location.slug)
    station, era5 = cache.load_table("meteostat"), cache.load_table("era5")
    if station is None or era5 is None:
        raise MissingDataError("no cached data; run `weather-odds prefetch` first")
    fills = check_fills(station["temperature"], era5["temperature"])
    comparisons = compare_with_station(config)
    text = "\n\n".join(
        ["### Gap fills (hidden hours)", report(fills), "### Against the station", to_markdown(comparisons)]
    )
    print(text)
    if output is not None:
        output.write_text(text + "\n", encoding="utf-8")
    failed = not all(c.passed for c in fills) or any(c.passed is False for c in comparisons)
    return 1 if failed else 0


def _source_list(text: str) -> list[str]:
    names = [n.strip() for n in text.split(",") if n.strip()]
    unknown = [n for n in names if n not in SOURCES]
    if unknown or not names:
        raise argparse.ArgumentTypeError(
            f"unknown source {', '.join(unknown) or text!r}; choose from {', '.join(SOURCES)}"
        )
    return names
