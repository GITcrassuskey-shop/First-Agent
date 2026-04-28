from __future__ import annotations

import argparse

from fa import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fa",
        description="First-Agent command-line entrypoint.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main() -> None:
    build_parser().parse_args()
