# -*- coding: utf-8 -*-
"""M5 · scan — read-only CI gate with baseline accounting.

Detection unit = one file, one non-empty line (K9, ``data/README.md`` §4.8).
A line is a hit iff:

    readability(line) < 0.5
    and a lossless candidate (depth <= MAX_DEPTH) has readability >= 0.8
    and readability(result) - readability(line) >= 0.3

The directory walk, the baseline buckets (new / baselined / stale) and the
report are all read-only: no file is ever modified. JSON is emitted before the
exit code is chosen (CI needs the report), but exit-code-2 paths produce no
output file (bad input leaves no trace).
"""

from __future__ import absolute_import

import io
import os

from . import attr
from . import codecs_table
from . import report
from . import score

MILESTONE = "M5"

BASELINE_SCHEMA = "mojibake-forensics/clean-corpus/1"

# K9 thresholds — single source: data/README.md §4.8.
INPUT_READABILITY_BELOW = 0.5
CANDIDATE_READABILITY_AT_LEAST = 0.8
READABILITY_GAIN_AT_LEAST = 0.3


class UsageError(ValueError):
    """Input/usage error: rendered as ``status="error"`` with exit code 2."""

    def __init__(self, code, message):
        super(UsageError, self).__init__(message)
        self.code = code
        self.message = message


def _read_baseline(path):
    """Load and validate the baseline JSON; syntax/schema errors → UsageError."""
    try:
        handle = io.open(path, "r", encoding="utf-8")
    except IOError as exc:
        reason = {
            FileNotFoundError: "file not found",
            IsADirectoryError: "path is a directory",
            PermissionError: "permission denied",
        }.get(exc.__class__, exc.__class__.__name__)
        raise UsageError("baseline_unreadable", "cannot read --baseline (%s)" % reason)
    try:
        with handle:
            import json

            baseline = json.load(handle)
    except UnicodeDecodeError:
        raise UsageError("baseline_invalid", "--baseline is not valid UTF-8")
    except ValueError as exc:
        raise UsageError(
            "baseline_invalid", "--baseline is not valid JSON (%s)" % exc.__class__.__name__
        )
    if not isinstance(baseline, dict) or not isinstance(baseline.get("files"), list):
        raise UsageError(
            "baseline_invalid", '--baseline must be an object with a "files" list'
        )
    return baseline


def line_hit(line):
    """K9 verdict for one line: hit evidence dict, or ``None``.

    Evidence carries the readability figures and the qualifying candidate set
    (bounded search via :func:`attr.search`; no second enumeration anywhere).
    """
    if not line.strip():
        return None
    line_read = score.readability(line)
    if line_read >= INPUT_READABILITY_BELOW:
        return None

    ranked, total_chains = attr.search(line)
    qualifying = []
    for entry in ranked:
        result_read = entry["score"]["readability"]
        if result_read >= CANDIDATE_READABILITY_AT_LEAST and (
            result_read - line_read >= READABILITY_GAIN_AT_LEAST
        ):
            qualifying.append(
                {
                    "result": entry["result"],
                    "path_string": entry["path_string"],
                    "depth": entry["depth"],
                    "readability": result_read,
                }
            )
    if not qualifying:
        return None
    return {
        "input_readability": line_read,
        "candidates": qualifying,
        "total_chains": total_chains,
    }


def _iter_lines(data):
    """Yield ``(line_number, text)`` for non-empty lines of a UTF-8 file."""
    text = data.decode("utf-8")
    for number, line in enumerate(text.splitlines(), 1):
        if line.strip():
            yield number, line


def scan_directory(directory, baseline, output_format="json"):
    """Return new / baselined / stale buckets and the exit code (M5).

    ``baseline`` is the parsed baseline dict. Walking order is the fixed byte
    order of the relative paths; every scan is read-only.
    """
    entries = baseline.get("files", [])
    baselined_paths = set()
    allowed = {}
    for entry in entries:
        rel = entry.get("path")
        if not rel:
            continue
        allowed[rel] = entry.get("allowed_hits") or []
        baselined_paths.add(rel)

    hits = []
    files_scanned = 0
    if os.path.isdir(directory):
        for root, dirs, files in os.walk(directory):
            dirs.sort()
            for name in sorted(files):
                absolute = os.path.join(root, name)
                rel = os.path.relpath(absolute, directory).replace(os.sep, "/")
                files_scanned += 1
                try:
                    handle = io.open(absolute, "rb")
                except IOError:
                    continue  # unreadable files are skipped silently (read-only gate)
                with handle:
                    data = handle.read()
                try:
                    lines = list(_iter_lines(data))
                except UnicodeDecodeError:
                    continue  # non-UTF-8 files are not the gate's input here
                for number, line in lines:
                    evidence = line_hit(line)
                    if evidence is None:
                        continue
                    hits.append(
                        {
                            "path": rel,
                            "line": number,
                            "input_readability": evidence["input_readability"],
                            "candidates": evidence["candidates"],
                        }
                    )

    hit_paths = set(hit["path"] for hit in hits)
    known = set(allowed)
    new = [hit for hit in hits if hit["path"] not in known]
    baselined = [hit for hit in hits if hit["path"] in known]
    # stale = baseline entries whose file no longer exists on disk
    stale = sorted(
        path
        for path in baselined_paths
        if not os.path.exists(os.path.join(directory, path.replace("/", os.sep)))
    )

    exit_code = report.EXIT_ATTENTION if new else report.EXIT_OK
    return {
        "new": new,
        "baselined": baselined,
        "stale": stale,
        "exit_code": exit_code,
        "files_scanned": files_scanned,
    }


def scan(directory, baseline_path):
    """Full envelope for the ``scan`` subcommand (read-only, K9 thresholds)."""
    baseline = _read_baseline(baseline_path)
    if baseline.get("schema") not in (None, BASELINE_SCHEMA):
        raise UsageError(
            "baseline_invalid",
            "--baseline schema %r is not %r" % (baseline.get("schema"), BASELINE_SCHEMA),
        )

    buckets = scan_directory(directory, baseline)
    expected_new = baseline.get("expected_new", [])
    payload = report.base_envelope(
        "ok" if not buckets["new"] else "attention"
    )
    payload["command"] = "scan"
    payload["directory"] = "."
    payload["files_scanned"] = buckets["files_scanned"]
    payload["new"] = buckets["new"]
    payload["baselined"] = buckets["baselined"]
    payload["stale"] = buckets["stale"]
    payload["expected_new"] = expected_new
    if buckets["new"]:
        payload["notes"] = ["new_hits_require_attention"]
    else:
        payload["notes"] = []
    return payload


def run(args):
    try:
        payload = scan(args.directory, args.baseline)
    except UsageError as exc:
        return report.error(exc.code, exc.message, command="scan")
    payload["directory"] = "."
    return payload


def _render_hit(hit):
    lines = ["  %s:%d" % (hit["path"], hit["line"])]
    lines.append(
        "    input readability: %.3f (below %.1f)"
        % (hit["input_readability"], INPUT_READABILITY_BELOW)
    )
    for candidate in hit["candidates"]:
        lines.append(
            "    candidate %r via %s (readability %.3f)"
            % (candidate["result"], candidate["path_string"], candidate["readability"])
        )
    return lines


def render(payload):
    """Stable human-readable text (no color, no clock, no host paths)."""
    if payload.get("status") not in ("ok", "attention"):
        return None
    lines = [
        "scan: %d file(s) scanned, %d new hit(s)"
        % (payload["files_scanned"], len(payload["new"]))
    ]
    for hit in payload["new"]:
        lines.extend(_render_hit(hit))
    if payload["baselined"]:
        lines.append("baselined hits: %d (already registered, see JSON)" % len(payload["baselined"]))
    if payload["stale"]:
        lines.append("stale baseline entries: %d" % len(payload["stale"]))
        for path in payload["stale"]:
            lines.append("  %s (no longer on disk)" % path)
    return "\n".join(lines) + "\n"
