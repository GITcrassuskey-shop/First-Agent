from __future__ import annotations

from fa.cli import build_parser


def test_cli_help_contains_project_name() -> None:
    help_text = build_parser().format_help()

    assert "First-Agent" in help_text
