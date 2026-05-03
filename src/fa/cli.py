from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from fa import __version__
from fa.chunker import CHUNKER_VERSION, Chunk, default_chunker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fa",
        description="First-Agent command-line entrypoint.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command")

    chunk_parser = subparsers.add_parser(
        "chunk",
        help="Run the deterministic chunker on a single file (smoke / inspection).",
        description=(
            "Run the deterministic chunker on PATH and emit the produced "
            "chunks. Intended for manual inspection of the chunker output; "
            "the real indexing command (`fa reindex`) lands once storage is "
            "wired."
        ),
    )
    chunk_parser.add_argument("path", type=Path, help="Path to the file to chunk.")
    chunk_parser.add_argument(
        "--output",
        choices=("text", "json"),
        default="text",
        help=(
            "Output format. 'text' prints a one-line-per-chunk summary; "
            "'json' emits the full Chunk records on stdout."
        ),
    )
    chunk_parser.set_defaults(func=_cmd_chunk)

    return parser


def _cmd_chunk(args: argparse.Namespace) -> int:
    path: Path = args.path
    if not path.exists():
        print(f"fa chunk: path not found: {path}", file=sys.stderr)
        return 2
    if not path.is_file():
        print(f"fa chunk: not a file: {path}", file=sys.stderr)
        return 2

    chunks = default_chunker().chunk_file(path)

    if args.output == "json":
        payload = {
            "chunker_version": CHUNKER_VERSION,
            "path": str(path),
            "chunks": [_chunk_to_dict(c) for c in chunks],
        }
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    print(f"# {path}  ({len(chunks)} chunk(s); chunker {CHUNKER_VERSION})")
    for chunk in chunks:
        breadcrumb = " > ".join(chunk.breadcrumb) if chunk.breadcrumb else "<root>"
        print(
            f"- {chunk.anchor}  L{chunk.line_start}-{chunk.line_end} "
            f"B{chunk.byte_start}-{chunk.byte_end}  [{chunk.lang}]  ({breadcrumb})"
        )
    return 0


def _chunk_to_dict(chunk: Chunk) -> dict[str, object]:
    data = asdict(chunk)
    # ``asdict`` converts the breadcrumb tuple to a list, which is the
    # right shape for JSON output.
    return data


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    func = getattr(args, "func", None)
    if func is None:
        parser.print_help()
        return
    raise SystemExit(func(args))
