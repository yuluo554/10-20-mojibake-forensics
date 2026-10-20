# -*- coding: utf-8 -*-
"""M4 · recover — deterministic recovery or an explicit LOST verdict.

Decision order is fixed (``plan/03`` §5.2): the five irreversible classes are
judged **first** — a verdict is never softened by a plausible chain — and only
a text that survives that triage is replayed through the ``--pick`` candidate.
The replay reuses :func:`explain.replay_chain` on the already-ranked candidate
from :func:`attr.search` (no second enumeration, ``plan/02`` intact).

A verified replay yields ``RECOVERED``. Any replay failure degrades to
``LOST(reason="verify_failed")``: an unverified repair is never emitted.
"""

from __future__ import absolute_import

from . import attr
from . import explain
from . import report

MILESTONE = "M4"

STATUS_RECOVERED = "recovered"
STATUS_LOST = "lost"
STATUS_NOT_MOJIBAKE = "not_mojibake"

REASON_REPLACEMENT_CHAR = "replacement_char"
REASON_KUN_JIN_KAO = "kun_jin_kao"
REASON_MSVC_FILL = "msvc_fill"
REASON_ENCODE_TRUNCATED = "encode_truncated"
REASON_SILENT_DROP = "silent_drop"
REASON_VERIFY_FAILED = "verify_failed"

REPLACEMENT_CHAR = u"\ufffd"  # U+FFFD
KUN_JIN_KAO = u"\u951f\u65a4\u62f7"  # 锟斤拷
TANG_TANG = u"\u70eb\u70eb\u70eb"  # 烫烫烫
TUN_TUN = u"\u5c6f\u5c6f\u5c6f"  # 屯屯屯
KUN_JIN_KAO_BYTES_HEX = "EF BF BD"

NOTE_NOT_MOJIBAKE = "classified_not_mojibake_no_repair_attempted"


class _Irreversible(Exception):
    """Internal triage signal carrying the LOST / NOT_MOJIBAKE payload."""

    def __init__(self, status, reason, loss=None, notes=None):
        super(_Irreversible, self).__init__(reason)
        self.status = status
        self.reason = reason
        self.loss = loss
        self.notes = notes or []


def _codepoint(char):
    return "U+%04X" % ord(char)


def _check_replacement_char(text):
    """U+FFFD marks bytes that no longer exist; locate every occurrence."""
    offsets = [index for index, char in enumerate(text) if char == REPLACEMENT_CHAR]
    if not offsets:
        return
    loss = {
        "step": "decode",
        "offset": offsets[0],
        "replaced_with": _codepoint(REPLACEMENT_CHAR),
        "cause": "errors=replace",
    }
    raise _Irreversible(
        STATUS_LOST, REASON_REPLACEMENT_CHAR, loss=loss, notes=["no_invented_characters"]
    )


def _check_kun_jin_kao(text):
    """锟斤拷 = the GBK misread of repeated EF BF BD replacement bytes."""
    if KUN_JIN_KAO not in text:
        return
    offset = text.index(KUN_JIN_KAO)
    repeat = 1
    unit_len = len(KUN_JIN_KAO)
    cursor = offset + unit_len
    while text[cursor:cursor + unit_len] == KUN_JIN_KAO:
        repeat += 1
        cursor += unit_len
    loss = {
        "step": "decode",
        "codec": "gbk",
        "offset": offset,
        "repeat": repeat,
        "bytes_hex": KUN_JIN_KAO_BYTES_HEX,
        "replaced_with": _codepoint(REPLACEMENT_CHAR),
        "cause": "errors=replace bytes misread as gbk",
    }
    raise _Irreversible(
        STATUS_LOST, REASON_KUN_JIN_KAO, loss=loss, notes=["no_invented_characters"]
    )


def _check_msvc_fill(text):
    """烫烫烫 (0xCC) / 屯屯屯 (0xCD) are MSVC debug stack fill, not mojibake."""
    if TANG_TANG in text or TUN_TUN in text:
        raise _Irreversible(
            STATUS_NOT_MOJIBAKE,
            REASON_MSVC_FILL,
            loss=None,
            notes=[NOTE_NOT_MOJIBAKE, "no_invented_characters"],
        )


def _check_question_mark(text):
    """A lone ``?`` is judged as an encode-time replacement (``errors=replace``).

    The fixture contract (``question-mark``) makes ``?`` in the text the
    evidence: the original character cannot be reconstructed from ``?``, so the
    verdict is LOST with the exact offset, never an invented character. (A
    ``?`` that genuinely belongs to clean ASCII prose is also reported as a
    candidate loss location — the human reader decides; the tool never claims
    the text is intact.)
    """
    if "?" not in text:
        return
    offset = text.index("?")
    loss = {
        "step": "encode",
        "offset": offset,
        "replaced_with": "?",
        "cause": "errors=replace",
    }
    raise _Irreversible(
        STATUS_LOST,
        REASON_ENCODE_TRUNCATED,
        loss=loss,
        notes=["original_character_unrecoverable", "no_invented_characters"],
    )


def _triage(text):
    """Fixed irreversible-class order (plan/03 §5.2). Raises ``_Irreversible``."""
    _check_replacement_char(text)
    _check_kun_jin_kao(text)
    _check_msvc_fill(text)
    _check_question_mark(text)
    # ``silent_drop`` cannot be proven from the visible text alone (the
    # fixture is explicit: "do not infer a drop from 'ab' alone"). It is
    # decided only through provenance, which the CLI surface does not carry;
    # see plan/06 已知边界.


def _recovered_payload(text, pick, ranked, total_chains):
    entry = ranked[pick - 1]
    chain = entry["chain"]
    replayed = explain.replay_chain(chain)

    if not replayed["verify"] or replayed["output"] != entry["result"]:
        loss = {
            "step": "replay",
            "offset": None,
            "cause": "verify_failed",
            "failed_step": replayed["failed_step"],
        }
        payload = report.base_envelope(STATUS_LOST)
        payload["command"] = "recover"
        payload["mode"] = "pick"
        payload["pick"] = pick
        payload["total_candidates"] = len(ranked)
        payload["total_chains"] = total_chains
        payload["candidate"] = {
            "rank": entry["rank"],
            "result": entry["result"],
            "path_string": entry["path_string"],
            "depth": entry["depth"],
        }
        payload["reason"] = REASON_VERIFY_FAILED
        payload["recovered"] = None
        payload["verify"] = False
        payload["loss"] = loss
        payload["steps"] = replayed["steps"]
        payload["notes"] = ["unverified_repair_suppressed", "no_invented_characters"]
        return payload

    payload = report.base_envelope(STATUS_RECOVERED)
    payload["command"] = "recover"
    payload["mode"] = "pick"
    payload["pick"] = pick
    payload["total_candidates"] = len(ranked)
    payload["total_chains"] = total_chains
    payload["candidate"] = {
        "rank": entry["rank"],
        "result": entry["result"],
        "path_string": entry["path_string"],
        "depth": entry["depth"],
    }
    payload["path_string"] = entry["path_string"]
    payload["recovered"] = replayed["output"]
    payload["verify"] = True
    payload["loss"] = None
    payload["steps"] = replayed["steps"]
    return payload


def _lost_payload(text, pick, triage, total_chains=None):
    payload = report.base_envelope(STATUS_LOST if triage.status == STATUS_LOST
                                   else STATUS_NOT_MOJIBAKE)
    payload["command"] = "recover"
    payload["mode"] = "pick"
    if pick is not None:
        payload["pick"] = pick
    payload["reason"] = triage.reason
    payload["recovered"] = None
    payload["verify"] = False
    payload["loss"] = triage.loss
    payload["notes"] = triage.notes
    return payload


def recover(text, pick, out=None):
    """RECOVERED / LOST / NOT_MOJIBAKE with loss-point evidence (M4)."""
    triage = None
    try:
        _triage(text)
    except _Irreversible as verdict:
        triage = verdict

    if triage is not None:
        return _lost_payload(text, pick, triage)

    ranked, total_chains = attr.search(text)
    if not ranked:
        payload = report.base_envelope(STATUS_LOST)
        payload["command"] = "recover"
        payload["mode"] = "pick"
        payload["pick"] = pick
        payload["total_candidates"] = 0
        payload["total_chains"] = total_chains
        payload["reason"] = "no_candidate"
        payload["recovered"] = None
        payload["verify"] = False
        payload["loss"] = None
        payload["notes"] = [attr.NOTE_DEPTH_LIMIT]
        return payload
    if pick < 1 or pick > len(ranked):
        raise attr.UsageError(
            "pick_out_of_range",
            "--pick %d is outside 1..%d (candidate count from attr)"
            % (pick, len(ranked)),
        )
    return _recovered_payload(text, pick, ranked, total_chains)


def _write_out(path, text):
    import io

    with io.open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def run(args):
    try:
        text = attr.text_from_args(args)
    except attr.UsageError as exc:
        return report.error(exc.code, exc.message, command="recover")

    # No implicit best guess: --pick is required (plan/03 §5.1).
    if args.pick is None:
        return report.error(
            "missing_pick",
            "recover requires --pick N; run `attr` first and pick a candidate",
            command="recover",
        )

    out_path = getattr(args, "out", None)
    if out_path is not None:
        # Never overwrite the input (plan/03 §5.1).
        import os

        in_path = getattr(args, "file_path", None)
        if in_path is not None and os.path.abspath(out_path) == os.path.abspath(in_path):
            return report.error(
                "out_overwrites_input",
                "--out must never overwrite the input file",
                command="recover",
            )

    try:
        payload = recover(text, pick=args.pick, out=out_path)
    except attr.UsageError as exc:
        return report.error(exc.code, exc.message, command="recover")

    if (
        payload.get("status") == STATUS_RECOVERED
        and out_path is not None
    ):
        _write_out(out_path, payload["recovered"])
        payload["written_to"] = "<out>"
    return payload


def _render_verdict(payload):
    status = payload["status"]
    lines = ["recover: %s" % status.upper()]
    if payload.get("reason"):
        lines.append("reason: %s" % payload["reason"])
    if payload.get("path_string"):
        lines.append("path: %s" % payload["path_string"])
    if payload.get("verify") is not None:
        lines.append("verify: %s" % ("true" if payload["verify"] else "false"))
    if payload.get("recovered") is not None:
        lines.append("recovered: %r" % payload["recovered"])
    loss = payload.get("loss")
    if loss:
        parts = ["step=%s" % loss.get("step")]
        if loss.get("offset") is not None:
            parts.append("offset=%d (0-based)" % loss["offset"])
        if loss.get("replaced_with"):
            parts.append("replaced_with=%s" % loss["replaced_with"])
        if loss.get("cause"):
            parts.append("cause=%s" % loss["cause"])
        lines.append("loss: %s" % ", ".join(parts))
    for note in payload.get("notes") or []:
        lines.append("note: %s" % note)
    return "\n".join(lines) + "\n"


def render(payload):
    """Stable human-readable verdict (no color, no clock, no host paths)."""
    status = payload.get("status")
    if status in (STATUS_RECOVERED, STATUS_LOST, STATUS_NOT_MOJIBAKE):
        return _render_verdict(payload)
    return None
