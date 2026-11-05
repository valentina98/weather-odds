"""Command line: weather-odds [--config PATH] COMMAND.

Later milestones add export and validate (#19).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from weather_odds import __version__
from weather_odds.config import ConfigError, dump_config, load_config
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
    check = commands.add_parser("check", help="build the tables and check them against the station's measurements")
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


def _build(config) -> int:
    from weather_odds.table import build

    build(config)
    return 0


def _check(config, output: Path | None) -> int:
    from weather_odds.checks import run_checks, to_markdown

    checks = run_checks(config)
    report = to_markdown(checks)
    print(report)
    if output is not None:
        output.write_text(report, encoding="utf-8")
    failed = [c for c in checks if c.passed is False and c.section == "station"]
    return 1 if failed else 0


def _source_list(text: str) -> list[str]:
    names = [n.strip() for n in text.split(",") if n.strip()]
    unknown = [n for n in names if n not in SOURCES]
    if unknown or not names:
        raise argparse.ArgumentTypeError(
            f"unknown source {', '.join(unknown) or text!r}; choose from {', '.join(SOURCES)}"
        )
    return names
