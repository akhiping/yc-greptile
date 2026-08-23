"""Command-line entry point for Pinocchio's report interfaces."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .ui import load_report, render_terminal
from .verify import create_report
from .web import serve_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pinocchio",
        description="Inspect a Pinocchio trust report in the terminal or browser.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    show = commands.add_parser("show", help="Render a report in the terminal")
    show.add_argument("report", type=Path, help="Path to a contract-compatible report JSON")
    show.add_argument("--no-color", action="store_true", help="Disable ANSI colors")

    verify = commands.add_parser("verify", help="Capture a repository and create a trust report")
    verify.add_argument("target_repo", type=Path, help="Git repository to inspect")
    verify.add_argument("--message", required=True, help="Agent's final message to verify")
    verify.add_argument("--evidence", type=Path, help="JSON file containing independent evidence")
    verify.add_argument("--output", type=Path, required=True, help="Report JSON destination")
    verify.add_argument("--greptile", action="store_true", help="Enable the optional Greptile witness")

    serve = commands.add_parser("serve", help="Open a local browser dashboard for a report")
    serve.add_argument("report", type=Path, help="Path to a contract-compatible report JSON")
    serve.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    serve.add_argument("--port", type=int, default=8765, help="Port (default: 8765)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "show":
            render_terminal(load_report(args.report), color=not args.no_color and sys.stdout.isatty())
        elif args.command == "verify":
            result = create_report(
                args.target_repo,
                message=args.message,
                evidence_path=args.evidence,
                output=args.output,
                greptile_enabled=True if args.greptile else None,
            )
            print(result)
        else:
            if not 0 < args.port < 65536:
                raise ValueError("--port must be between 1 and 65535")
            serve_report(args.report, host=args.host, port=args.port)
    except (OSError, ValueError) as exc:
        print(f"Pinocchio: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
