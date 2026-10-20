# -*- coding: utf-8 -*-
"""M2 · attr — bounded candidate attribution.

Pipeline (``data/README.md`` §4.2–§4.5):

    enumerate_chains(max_depth=MAX_DEPTH)  ->  lossless chains
    collapse_by_result                     ->  one chain per distinct result
    score.rank                             ->  frozen sort key
    truncate to --top for display only     ->  total_candidates stays complete

The command never claims a single truth: ``candidates`` is always a list, and
every candidate carries its own score, confidence interval and note.
"""

from __future__ import absolute_import

import io

from . import codecs_table
from . import paths
from . import report
from . import score

DEFAULT_TOP = 5

NOTE_SINGLE = "single_candidate_in_bounded_search"
NOTE_NO_POSITIVE = "no_positive_score"
NOTE_TRUNCATED = "truncated_to_top_n"
NOTE_DEPTH_LIMIT = "depth_limit_reached"


class UsageError(ValueError):
    """Input/usage error: rendered as ``status="error"`` with exit code 2."""

    def __init__(self, code, message):
        super(UsageError, self).__init__(message)
        self.code = code
        self.message = message


def _codec_subset(raw, allowed, option):
    """Parse one comma-separated subset; only shrinks the frozen set (§4.1)."""
    if raw is None:
        return tuple(allowed)
    names = []
    for token in raw.split(","):
        name = token.strip().lower()
        if not name:
            raise UsageError(
                "invalid_codec_subset",
                "%s contains an empty codec name; expected a comma-separated "
                "subset of the frozen set (%s)" % (option, ", ".join(allowed)),
            )
        if name not in allowed:
            raise UsageError(
                "invalid_codec_subset",
                "%s=%r is not in the frozen set (%s); subsets may only shrink "
                "it, never add codecs" % (option, name, ", ".join(allowed)),
            )
        if name not in names:
            names.append(name)
    return tuple(names)


def _confidence(entries):
    """§4.5 relative confidence over the *full* candidate set.

    Returns ``(intervals, note)`` where ``intervals`` is aligned with
    ``entries`` and each item is ``{"lower", "upper"}`` or ``None``.
    """
    count = len(entries)
    if count == 0:
        return [], None
    if count == 1:
        return [{"lower": 1.0, "upper": 1.0}], NOTE_SINGLE

    total = 0.0
    for entry in entries:
        total += entry["score_total"]
    if total <= 0.0:
        # Includes the documented "all scores <= 0" case; a non-positive sum
        # makes the normalization undefined, so no distribution is invented.
        return [None] * count, NOTE_NO_POSITIVE

    spread = 0.05 * (count - 1)
    intervals = []
    for entry in entries:
        value = entry["score_total"] / total
        intervals.append(
            {
                "lower": value / (1.0 + spread),
                "upper": min(1.0, value * (1.0 + spread)),
            }
        )
    return intervals, None


def _validate_text(text):
    if not isinstance(text, str):
        raise UsageError(
            "invalid_input",
            "input must be an already-decoded str; raw bytes belong to the "
            "`file` subcommand",
        )
    if text == "":
        raise UsageError("empty_input", "input is empty; nothing to attribute")


def search(text, encoders=None, decoders=None):
    """Run the bounded, lossless search once (shared by ``attr`` / ``explain``).

    Returns ``(ranked, total_chains)``. Every ranked entry is the dict produced
    by :func:`score.rank` plus a ``chain`` key holding the original
    :class:`paths.Chain`. That keeps ``plan/02``'s rule intact: the Chain is the
    only intermediate representation, and ``explain`` replays exactly the chain
    that was ranked instead of enumerating a second time.
    """
    codecs_table.ensure_codecs()
    _validate_text(text)
    encoders = tuple(encoders) if encoders is not None else codecs_table.ENCODERS
    decoders = tuple(decoders) if decoders is not None else codecs_table.DECODERS

    chains = paths.enumerate_chains(
        text,
        encoders=encoders,
        decoders=decoders,
        max_depth=codecs_table.MAX_DEPTH,
    )
    collapsed = paths.collapse_by_result(chains)
    ranked = score.rank(collapsed)
    by_path = dict((chain.path_string, chain) for chain in collapsed)
    for entry in ranked:
        entry["chain"] = by_path[entry["path_string"]]
    return ranked, len(chains)


def attribute(text, source_enc=None, target_enc=None, top=DEFAULT_TOP, freq=None):
    """Return the bounded candidate envelope for ``text``.

    ``source_enc`` narrows ``ENCODERS`` and ``target_enc`` narrows ``DECODERS``;
    neither may add a codec. Raises :class:`UsageError` for bad input and
    :class:`codecs_table.CodecUnavailable` when a frozen codec is missing.
    """
    codecs_table.ensure_codecs()

    encoders = _codec_subset(source_enc, codecs_table.ENCODERS, "--source-enc")
    decoders = _codec_subset(target_enc, codecs_table.DECODERS, "--target-enc")

    if freq is not None:
        raise UsageError(
            "freq_not_implemented",
            "--freq (frequency prior) is a phase-2 optional feature and is not "
            "implemented in this build; no language prior is fabricated",
        )
    if isinstance(top, bool) or not isinstance(top, int) or top < 1:
        raise UsageError("invalid_top", "--top must be an integer >= 1")

    ranked, total_chains = search(text, encoders=encoders, decoders=decoders)
    intervals, shared_note = _confidence(ranked)

    total_candidates = len(ranked)
    truncated = total_candidates > top

    candidates = []
    for index, entry in enumerate(ranked[:top]):
        note = shared_note
        if note is None and truncated:
            note = NOTE_TRUNCATED
        candidates.append(
            {
                "rank": entry["rank"],
                "result": entry["result"],
                "path": entry["path"],
                "path_string": entry["path_string"],
                "depth": entry["depth"],
                "score": dict(entry["score"]),
                "confidence": intervals[index],
                "note": note,
            }
        )

    payload = report.base_envelope("candidates" if total_candidates else "no_candidate")
    payload["command"] = "attr"
    payload["total_candidates"] = total_candidates
    payload["total_chains"] = total_chains
    payload["candidates"] = candidates
    if not total_candidates:
        payload["notes"] = [NOTE_DEPTH_LIMIT]
    return payload


def _reason(exc):
    """Short, path-free reason for a read failure (K7: no absolute paths)."""
    if isinstance(exc, FileNotFoundError):
        return "file not found"
    if isinstance(exc, IsADirectoryError):
        return "path is a directory"
    if isinstance(exc, PermissionError):
        return "permission denied"
    return exc.__class__.__name__


def _read_text_file(path):
    """Read ``--file`` as UTF-8 only; raw bytes belong to the ``file`` command."""
    try:
        handle = io.open(path, "r", encoding="utf-8", newline="")
    except IOError as exc:
        raise UsageError(
            "file_unreadable",
            "cannot open --file for reading (%s); use the `file` subcommand "
            "for raw bytes" % _reason(exc),
        )
    try:
        with handle:
            return handle.read()
    except UnicodeDecodeError:
        raise UsageError(
            "file_unreadable",
            "--file is not valid UTF-8; use the `file` subcommand for raw bytes",
        )
    except IOError as exc:
        raise UsageError(
            "file_unreadable",
            "cannot read --file (%s); use the `file` subcommand for raw bytes"
            % _reason(exc),
        )


def text_from_args(args):
    """Resolve ``--text`` / ``--file`` for the commands that share that surface."""
    file_path = getattr(args, "file_path", None)
    text = getattr(args, "text", None)
    if file_path:
        return _read_text_file(file_path)
    if text is None:
        raise UsageError("missing_input", "one of --text or --file is required")
    return text


def run(args):
    try:
        text = text_from_args(args)
        return attribute(
            text,
            source_enc=getattr(args, "source_enc", None),
            target_enc=getattr(args, "target_enc", None),
            top=getattr(args, "top", DEFAULT_TOP),
            freq=getattr(args, "freq", None),
        )
    except UsageError as exc:
        return report.error(exc.code, exc.message, command="attr")


def render(payload):
    """Stable human-readable text (no color, no clock, no host paths)."""
    status = payload.get("status")
    if status == "no_candidate":
        return (
            "attr: no candidate within the frozen set and depth limit\n"
            "notes: %s\n" % ", ".join(payload.get("notes") or [NOTE_DEPTH_LIMIT])
        )
    if status != "candidates":
        return None

    criteria = payload.get("criteria", {})
    lines = [
        "attr: %d candidate(s) in bounded search (chains %d, depth <= %s)"
        % (
            payload["total_candidates"],
            payload["total_chains"],
            criteria.get("max_depth", codecs_table.MAX_DEPTH),
        )
    ]
    shown = len(payload["candidates"])
    if shown < payload["total_candidates"]:
        lines.append(
            "showing top %d of %d; the rest are beyond the display cut"
            % (shown, payload["total_candidates"])
        )
    for candidate in payload["candidates"]:
        confidence = candidate["confidence"]
        if confidence is None:
            confidence_text = "confidence=null"
        else:
            confidence_text = "confidence=[%.4f, %.4f]" % (
                confidence["lower"],
                confidence["upper"],
            )
        lines.append(
            "%2d. %r  score=%.4f  %s  %s"
            % (
                candidate["rank"],
                candidate["result"],
                candidate["score"]["total"],
                confidence_text,
                candidate["path_string"],
            )
        )
        if candidate["note"]:
            lines.append("    note: %s" % candidate["note"])
    lines.append(
        "criteria: %d encoders x %d decoders, max_depth %s"
        % (
            len(criteria.get("encoders", [])),
            len(criteria.get("decoders", [])),
            criteria.get("max_depth", codecs_table.MAX_DEPTH),
        )
    )
    return "\n".join(lines) + "\n"
