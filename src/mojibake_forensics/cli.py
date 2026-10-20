# -*- coding: utf-8 -*-
"""Command-line entry point for Mojibake Forensics.

Skeleton behaviour: every implemented-in-a-later-milestone subcommand returns
``status="not_ready"`` and exit code 4. No empty result is fabricated.
"""

from __future__ import absolute_import

import argparse
import sys

from . import __version__
from . import attr as attr_cmd
from . import codecs_table
from . import explain as explain_cmd
from . import file as file_cmd
from . import recover as recover_cmd
from . import report
from . import scan as scan_cmd

COMMANDS = {
    "attr": attr_cmd,
    "explain": explain_cmd,
    "recover": recover_cmd,
    "file": file_cmd,
    "scan": scan_cmd,
}

PRESETS = ("csv-excel-win", "zip-names", "utf16")


def _configure_stdio():
    """Disable platform newline translation so canonical JSON keeps LF bytes."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(newline="\n")
        except (ValueError, OSError):
            pass


def build_parser():
    parser = argparse.ArgumentParser(
        prog="forensics",
        description="Mojibake forensics: bounded candidates + byte-level proofs (local-only).",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + __version__
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    attr = subparsers.add_parser(
        "attr", help="attribute an already-decoded string to bounded candidate chains"
    )
    _add_text_input(attr)
    attr.add_argument("--source-enc", default=None, help="comma-separated encoder subset")
    attr.add_argument("--target-enc", default=None, help="comma-separated decoder subset")
    attr.add_argument("--top", type=int, default=5, help="number of candidates to show (default 5)")
    attr.add_argument("--freq", default=None, help="optional frequency table (phase 2)")
    attr.add_argument("--json", action="store_true", help="machine-readable JSON")

    explain = subparsers.add_parser(
        "explain", help="replay a candidate path step by step with byte proofs"
    )
    _add_text_input(explain)
    explain.add_argument("--pick", type=int, default=None, help="candidate rank to explain")
    explain.add_argument("--all", dest="all_candidates", action="store_true", help="explain all candidates")
    explain.add_argument("--vs", type=int, default=None, help="compare with candidate rank N")
    explain.add_argument("--json", action="store_true", help="machine-readable JSON")

    recover = subparsers.add_parser(
        "recover", help="recover via an explicit candidate, or declare LOST / NOT_MOJIBAKE"
    )
    recover.add_argument("--text", required=True, help="already-decoded string")
    recover.add_argument("--pick", type=int, required=True, help="candidate rank from attr")
    recover.add_argument("--out", default=None, help="write recovered text here (never overwrite input)")
    recover.add_argument("--json", action="store_true", help="machine-readable JSON")

    file_cmd_parser = subparsers.add_parser(
        "file", help="diagnose raw bytes: BOM, UTF-16 misalignment, zip names, CSV presets"
    )
    file_cmd_parser.add_argument("--path", required=True, help="file to inspect (read-only)")
    file_cmd_parser.add_argument("--preset", choices=PRESETS, default=None, help="named candidate set")
    file_cmd_parser.add_argument("--json", action="store_true", help="machine-readable JSON")

    scan = subparsers.add_parser(
        "scan", help="read-only directory gate with a clean-corpus baseline"
    )
    scan.add_argument("--dir", dest="directory", required=True, help="directory to scan")
    scan.add_argument("--baseline", required=True, help="clean-corpus baseline JSON")
    scan.add_argument("--format", choices=("json", "human"), default="json")
    scan.add_argument("--json", action="store_true", help="alias for --format json")

    return parser


def _add_text_input(parser):
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="already-decoded string")
    group.add_argument("--file", dest="file_path", help="UTF-8 text file")


def _wants_json(args):
    if getattr(args, "json", False):
        return True
    return getattr(args, "format", None) == "json"


def _exit_code_for(payload):
    status = payload.get("status")
    if status == "not_ready":
        return report.EXIT_NOT_READY
    if status in ("candidates", "recovered", "ok", "explain"):
        return report.EXIT_OK
    if status == "error":
        return report.EXIT_USAGE
    return report.EXIT_ATTENTION


def main(argv=None):
    _configure_stdio()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "explain" and args.pick is None and not args.all_candidates:
        parser.error("explain requires --pick N or --all")
    if args.command == "attr" and args.top < 1:
        parser.error("--top must be >= 1")
    if args.command == "explain" and args.pick is not None and args.pick < 1:
        parser.error("--pick must be >= 1")
    if args.command == "recover" and args.pick < 1:
        parser.error("--pick must be >= 1")

    try:
        codecs_table.ensure_codecs()
    except codecs_table.CodecUnavailable as exc:
        report.write_json(report.error("codec_unavailable", str(exc), command=args.command))
        return report.EXIT_ENV

    module = COMMANDS[args.command]
    payload = module.run(args)
    report.emit(
        payload,
        as_json=_wants_json(args),
        command=args.command,
        milestone=payload.get("milestone"),
    )
    return _exit_code_for(payload)


if __name__ == "__main__":
    sys.exit(main())
