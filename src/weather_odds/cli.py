"""Command line: weather-odds [--config PATH] COMMAND.

Later milestones add prefetch (#16), export and validate (#19).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from weather_odds import __version__
from weather_odds.config import ConfigError, dump_config, load_config


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
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
    except ConfigError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if args.command == "config":
        print(dump_config(config), end="")
    return 0
