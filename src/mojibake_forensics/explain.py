# -*- coding: utf-8 -*-
"""M3 · explain — replayable byte-level proof for each candidate path.

The command is read-only. It asks :func:`attr.search` for the *already ranked*
candidate chains (no second enumeration), replays each selected chain from its
input text, and compares every recomputed step with the step record built by
``paths.enumerate_chains``. A mismatch is reported at the exact step; it is
never smoothed over.

``--vs`` adds a divergence report against another candidate. The report states
the first differing step/byte/character only; it never ranks the candidates or
claims that one is "better".
"""

from __future__ import absolute_import

from . import attr
from . import paths
from . import report

MILESTONE = "M3"

STATUS_OK = "ok"
STATUS_VERIFY_FAILED = "verify_failed"

NOTE_NO_SECOND = "no_second_candidate"


def _bytes_from_hex(text):
    """Parse the report's ``"E9 9B 85"`` form back to bytes (``None`` if unset)."""
    if text is None:
        return None
    return bytes(bytearray(int(token, 16) for token in text.split()))


def _first_byte_diff(left, right):
    for index in range(min(len(left), len(right))):
        if left[index] != right[index]:
            return index
    return min(len(left), len(right))


def _first_char_diff(left, right):
    for index in range(min(len(left), len(right))):
        if left[index] != right[index]:
            return index
    return min(len(left), len(right))


def _codepoint(char):
    if char is None:
        return None
    return "U+%04X" % ord(char)


def replay_chain(chain):
    """Replay ``chain`` and verify every step against its recorded state.

    The chain's :class:`paths.Step` records were produced during enumeration.
    This function recomputes each step from the *computed* state, then checks:

    * the recorded step input equals the computed input (chain consistency);
    * ``state.encode(codec)`` / ``state.decode(codec)`` equals the recorded
      output (the independent recomputation requirement of M3).

    The first failure stops the replay; ``failed_step`` is that step's 1-based
    index. Returns a dict with ``steps`` / ``verify`` / ``failed_step`` /
    ``output``.
    """
    steps = []
    failed_step = None
    state = None

    if chain.steps:
        state = chain.steps[0].input_text

    for step in chain.steps:
        entry = {
            "index": step.index,
            "op": step.op,
            "codec": step.codec,
        }

        if step.op == "encode":
            if not isinstance(state, str):
                entry["verify"] = False
                entry["failure"] = {
                    "reason": "state_type",
                    "expected": "str",
                    "observed": type(state).__name__,
                }
                failed_step = step.index
                steps.append(entry)
                break
            entry["input"] = state
            if step.input_text is None:
                entry["verify"] = False
                entry["failure"] = {"reason": "missing_record"}
                failed_step = step.index
                steps.append(entry)
                break
            if state != step.input_text:
                entry["verify"] = False
                entry["failure"] = {
                    "reason": "input_mismatch",
                    "expected": step.input_text,
                    "observed": state,
                    "char_offset": _first_char_diff(step.input_text, state),
                }
                failed_step = step.index
                steps.append(entry)
                break
            try:
                raw = state.encode(step.codec)
            except UnicodeEncodeError as exc:
                entry["verify"] = False
                entry["failure"] = {
                    "reason": "encode_error",
                    "char_offset": exc.start,
                }
                failed_step = step.index
                steps.append(entry)
                break
            entry["output_hex"] = paths.hexdump(raw)
            expected = _bytes_from_hex(step.output_hex)
            if expected is None:
                entry["verify"] = False
                entry["failure"] = {"reason": "missing_record"}
                failed_step = step.index
                steps.append(entry)
                break
            if raw != expected:
                entry["verify"] = False
                entry["failure"] = {
                    "reason": "mismatch",
                    "expected_hex": paths.hexdump(expected),
                    "observed_hex": paths.hexdump(raw),
                    "byte_offset": _first_byte_diff(expected, raw),
                }
                failed_step = step.index
                steps.append(entry)
                break
            entry["verify"] = True
            state = raw

        else:
            if not isinstance(state, (bytes, bytearray)):
                entry["verify"] = False
                entry["failure"] = {
                    "reason": "state_type",
                    "expected": "bytes",
                    "observed": type(state).__name__,
                }
                failed_step = step.index
                steps.append(entry)
                break
            state = bytes(state)
            entry["input_hex"] = paths.hexdump(state)
            recorded_input = _bytes_from_hex(step.input_hex)
            if recorded_input is None:
                entry["verify"] = False
                entry["failure"] = {"reason": "missing_record"}
                failed_step = step.index
                steps.append(entry)
                break
            if state != recorded_input:
                entry["verify"] = False
                entry["failure"] = {
                    "reason": "input_mismatch",
                    "expected_hex": paths.hexdump(recorded_input),
                    "observed_hex": paths.hexdump(state),
                    "byte_offset": _first_byte_diff(recorded_input, state),
                }
                failed_step = step.index
                steps.append(entry)
                break
            try:
                text = state.decode(step.codec)
            except UnicodeDecodeError as exc:
                entry["verify"] = False
                entry["failure"] = {
                    "reason": "decode_error",
                    "byte_offset": exc.start,
                }
                failed_step = step.index
                steps.append(entry)
                break
            entry["output"] = text
            if step.output_text is None:
                entry["verify"] = False
                entry["failure"] = {"reason": "missing_record"}
                failed_step = step.index
                steps.append(entry)
                break
            if text != step.output_text:
                entry["verify"] = False
                entry["failure"] = {
                    "reason": "mismatch",
                    "expected": step.output_text,
                    "observed": text,
                    "char_offset": _first_char_diff(step.output_text, text),
                }
                failed_step = step.index
                steps.append(entry)
                break
            entry["verify"] = True
            state = text

        steps.append(entry)

    output = state if isinstance(state, str) else None
    return {
        "steps": steps,
        "verify": failed_step is None,
        "failed_step": failed_step,
        "output": output,
    }


def _step_divergence(left, right, at_step):
    return {
        "at_step": at_step,
        "kind": "step",
        "byte_offset": None,
        "char_offset": None,
        "left": {"op": left["op"], "codec": left["codec"]},
        "right": {"op": right["op"], "codec": right["codec"]},
        "statement": "step %d: op/codec differs: %s:%s vs %s:%s"
        % (at_step, left["op"], left["codec"], right["op"], right["codec"]),
    }


def compare_proofs(left_proof, right_proof, vs_rank, vs_entry):
    """First divergence between two replay proofs.

    Only differences are stated. The comparison order is fixed: op/codec, then
    bytes (encode steps), then text (decode steps), then chain length.
    """
    left_steps = left_proof["steps"]
    right_steps = right_proof["steps"]
    common = min(len(left_steps), len(right_steps))

    result = {
        "vs_rank": vs_rank,
        "vs_result": vs_entry["result"],
        "vs_path_string": vs_entry["path_string"],
        "at_step": None,
        "kind": "none",
        "byte_offset": None,
        "char_offset": None,
        "left": None,
        "right": None,
    }

    for index in range(common):
        left = left_steps[index]
        right = right_steps[index]
        at_step = index + 1

        if left["op"] != right["op"] or left["codec"] != right["codec"]:
            result.update(_step_divergence(left, right, at_step))
            return result

        if not left.get("verify") or not right.get("verify"):
            result.update(
                {
                    "at_step": at_step,
                    "kind": "failed_step",
                    "left": {
                        "verify": bool(left.get("verify")),
                        "failure": left.get("failure"),
                    },
                    "right": {
                        "verify": bool(right.get("verify")),
                        "failure": right.get("failure"),
                    },
                    "statement": "step %d: at least one proof fails verification there"
                    % at_step,
                }
            )
            return result

        if left["op"] == "encode":
            left_bytes = _bytes_from_hex(left.get("output_hex"))
            right_bytes = _bytes_from_hex(right.get("output_hex"))
            if left_bytes != right_bytes:
                offset = _first_byte_diff(left_bytes or b"", right_bytes or b"")
                left_byte = (
                    "%02X" % left_bytes[offset]
                    if left_bytes is not None and offset < len(left_bytes)
                    else None
                )
                right_byte = (
                    "%02X" % right_bytes[offset]
                    if right_bytes is not None and offset < len(right_bytes)
                    else None
                )
                result.update(
                    {
                        "at_step": at_step,
                        "kind": "bytes",
                        "byte_offset": offset,
                        "left": {
                            "hex": left.get("output_hex"),
                            "byte": left_byte,
                        },
                        "right": {
                            "hex": right.get("output_hex"),
                            "byte": right_byte,
                        },
                        "statement": "step %d: byte offset %d (0-based) differs: %s vs %s"
                        % (at_step, offset, left_byte, right_byte),
                    }
                )
                return result
        else:
            left_text = left.get("output")
            right_text = right.get("output")
            if left_text != right_text:
                offset = _first_char_diff(left_text or "", right_text or "")
                left_char = (
                    left_text[offset]
                    if left_text is not None and offset < len(left_text)
                    else None
                )
                right_char = (
                    right_text[offset]
                    if right_text is not None and offset < len(right_text)
                    else None
                )
                result.update(
                    {
                        "at_step": at_step,
                        "kind": "text",
                        "char_offset": offset,
                        "left": {
                            "char": left_char,
                            "codepoint": _codepoint(left_char),
                        },
                        "right": {
                            "char": right_char,
                            "codepoint": _codepoint(right_char),
                        },
                        "statement": "step %d: character offset %d (0-based) differs: %s vs %s"
                        % (
                            at_step,
                            offset,
                            _codepoint(left_char),
                            _codepoint(right_char),
                        ),
                    }
                )
                return result

    if len(left_steps) != len(right_steps):
        result.update(
            {
                "at_step": common + 1,
                "kind": "depth",
                "left": {"steps": len(left_steps)},
                "right": {"steps": len(right_steps)},
                "statement": "chain lengths differ after step %d: %d vs %d steps"
                % (common, len(left_steps), len(right_steps)),
            }
        )
        return result

    result["statement"] = "no divergence: same path and same outputs"
    return result


def _proof(entry):
    replayed = replay_chain(entry["chain"])
    return {
        "rank": entry["rank"],
        "result": entry["result"],
        "path": entry["path"],
        "path_string": entry["path_string"],
        "depth": entry["depth"],
        "steps": replayed["steps"],
        "verify": replayed["verify"],
        "failed_step": replayed["failed_step"],
        "output": replayed["output"],
        "divergence": None,
    }


def _default_vs(pick, total):
    """Compare with the other top candidate: pick 1 -> 2, pick 2 -> 1."""
    if total < 2:
        return None
    return 1 if pick == 2 else 2


def explain(text, pick=None, versus=None, all_candidates=False):
    """Build the byte-level proof payload for one or all candidates.

    ``versus`` is a 1-based candidate rank. When omitted, the comparison uses
    the other top-2 candidate (see :func:`_default_vs`); with fewer than two
    candidates the note ``no_second_candidate`` is emitted instead of failing.
    An explicit out-of-range ``versus`` is a usage error.
    """
    ranked, total_chains = attr.search(text)
    total_candidates = len(ranked)

    if total_candidates == 0:
        payload = report.base_envelope("no_candidate")
        payload["command"] = "explain"
        payload["mode"] = "all" if all_candidates else "pick"
        payload["total_candidates"] = 0
        payload["total_chains"] = total_chains
        payload["proofs"] = []
        if pick is not None:
            payload["pick"] = pick
        payload["notes"] = [attr.NOTE_DEPTH_LIMIT]
        return payload

    if all_candidates:
        mode = "all"
        selected = ranked
    else:
        mode = "pick"
        if pick is None:
            raise attr.UsageError(
                "missing_pick", "explain requires --pick N or --all"
            )
        if pick < 1 or pick > total_candidates:
            raise attr.UsageError(
                "pick_out_of_range",
                "--pick %d is outside 1..%d (candidate count from attr)"
                % (pick, total_candidates),
            )
        selected = [ranked[pick - 1]]

    proofs = [_proof(entry) for entry in selected]
    notes = []

    if mode == "pick":
        vs_rank = versus if versus is not None else _default_vs(pick, total_candidates)
        if versus is not None and (versus < 1 or versus > total_candidates):
            raise attr.UsageError(
                "vs_out_of_range",
                "--vs %d is outside 1..%d (candidate count from attr)"
                % (versus, total_candidates),
            )
        if vs_rank is None:
            notes.append(NOTE_NO_SECOND)
        else:
            other = ranked[vs_rank - 1]
            other_proof = _proof(other)
            proofs[0]["divergence"] = compare_proofs(
                proofs[0], other_proof, vs_rank, other
            )

    failed = any(proof["verify"] is False for proof in proofs)
    payload = report.base_envelope(STATUS_VERIFY_FAILED if failed else STATUS_OK)
    payload["command"] = "explain"
    payload["mode"] = mode
    payload["total_candidates"] = total_candidates
    payload["total_chains"] = total_chains
    payload["proofs"] = proofs
    if mode == "pick":
        payload["pick"] = pick
    if notes:
        payload["notes"] = notes
    return payload


def run(args):
    try:
        text = attr.text_from_args(args)
        return explain(
            text,
            pick=getattr(args, "pick", None),
            versus=getattr(args, "vs", None),
            all_candidates=getattr(args, "all_candidates", False),
        )
    except attr.UsageError as exc:
        return report.error(exc.code, exc.message, command="explain")


def _format_failure(failure):
    if not failure:
        return "unspecified"
    reason = failure.get("reason")
    if reason == "encode_error":
        return "encode_error at character %d (0-based)" % failure["char_offset"]
    if reason == "decode_error":
        return "decode_error at byte %d (0-based)" % failure["byte_offset"]
    if reason == "input_mismatch":
        if "char_offset" in failure:
            return "input_mismatch at character %d (0-based)" % failure["char_offset"]
        return "input_mismatch at byte %d (0-based)" % failure["byte_offset"]
    if reason == "mismatch":
        if "char_offset" in failure:
            return "recorded text and recomputed text differ at character %d (0-based)" % failure[
                "char_offset"
            ]
        return "recorded bytes and recomputed bytes differ at byte %d (0-based)" % failure[
            "byte_offset"
        ]
    if reason == "state_type":
        return "state_type: expected %s, observed %s" % (
            failure["expected"],
            failure["observed"],
        )
    if reason == "missing_record":
        return "missing_record: the chain step has no recorded value"
    return str(reason)


def render(payload):
    """Stable human-readable proof text (no color, no clock, no host paths)."""
    status = payload.get("status")
    if status == "no_candidate":
        return (
            "explain: no candidate within the frozen set and depth limit\n"
            "notes: %s\n" % ", ".join(payload.get("notes") or [attr.NOTE_DEPTH_LIMIT])
        )
    if status not in (STATUS_OK, STATUS_VERIFY_FAILED):
        return None

    total = payload.get("total_candidates")
    lines = []
    for proof in payload.get("proofs", []):
        lines.append(
            "candidate %d/%d  result=%r  depth=%d  path=%s"
            % (proof["rank"], total, proof["result"], proof["depth"], proof["path_string"])
        )
        for step in proof["steps"]:
            flag = "OK" if step.get("verify") else "FAIL"
            if step["op"] == "encode":
                lines.append(
                    "step %d  encode  %s  %r  ->  %s  %s"
                    % (
                        step["index"],
                        step["codec"],
                        step.get("input"),
                        step.get("output_hex"),
                        flag,
                    )
                )
            else:
                lines.append(
                    "step %d  decode  %s  %s  ->  %r  %s"
                    % (
                        step["index"],
                        step["codec"],
                        step.get("input_hex"),
                        step.get("output"),
                        flag,
                    )
                )
            if not step.get("verify"):
                lines.append("    failure: %s" % _format_failure(step.get("failure")))
        if proof["verify"]:
            lines.append(
                "recompute: PASS (%d step(s), every recorded value recomputed)"
                % len(proof["steps"])
            )
        else:
            lines.append(
                "recompute: FAIL at step %s" % proof["failed_step"]
            )
        divergence = proof.get("divergence")
        if divergence is not None:
            lines.append(
                "vs %d  result=%r  path=%s"
                % (
                    divergence["vs_rank"],
                    divergence["vs_result"],
                    divergence["vs_path_string"],
                )
            )
            lines.append("  divergence: %s" % divergence["statement"])
        lines.append("")

    if not lines:
        return "explain: no proof produced\n"
    return "\n".join(lines).rstrip("\n") + "\n"
