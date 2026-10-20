#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Independent replay checker for ``forensics explain --json`` (M3).

Reads one JSON object from stdin::

    {"text": "<input string>", "payload": <explain payload>}

It replays each reported proof using only the standard library and the values
that the report itself published (``path`` / ``steps``). It imports nothing from
``mojibake_forensics`` and keeps no tool state, so a green run is independent
evidence that the proof is reproducible outside the tool.

Exit code: 0 when every proof replays and every reported step matches, 1
otherwise. Prints one PASS/FAIL line per proof plus a final summary.
"""

from __future__ import print_function

import json
import sys


def hexdump(data):
    return " ".join("%02X" % byte for byte in data)


def replay_proof(text, proof):
    """Return a list of problems; an empty list means the proof reproduced."""
    problems = []
    state = text
    failure_step = None

    for step in proof.get("steps", []):
        index = step.get("index")
        op = step.get("op")
        codec = step.get("codec")

        if op == "encode":
            if not isinstance(state, str):
                problems.append("step %s: state is not text before encode" % index)
                failure_step = index
                break
            if "input" in step and step["input"] != state:
                problems.append("step %s: reported input text differs from replay" % index)
                failure_step = index
                break
            try:
                raw = state.encode(codec)
            except UnicodeEncodeError:
                failure_step = index
                break
            if step.get("output_hex") != hexdump(raw):
                problems.append(
                    "step %s: reported output_hex %r != replayed %r"
                    % (index, step.get("output_hex"), hexdump(raw))
                )
                failure_step = index
                break
            state = raw
        elif op == "decode":
            if not isinstance(state, (bytes, bytearray)):
                problems.append("step %s: state is not bytes before decode" % index)
                failure_step = index
                break
            state = bytes(state)
            if step.get("input_hex") != hexdump(state):
                problems.append(
                    "step %s: reported input_hex %r != replayed %r"
                    % (index, step.get("input_hex"), hexdump(state))
                )
                failure_step = index
                break
            try:
                decoded = state.decode(codec)
            except UnicodeDecodeError:
                failure_step = index
                break
            if step.get("output") != decoded:
                problems.append(
                    "step %s: reported output %r != replayed %r"
                    % (index, step.get("output"), decoded)
                )
                failure_step = index
                break
            state = decoded
        else:
            problems.append("step %s: unknown op %r" % (index, op))
            failure_step = index
            break

        if step.get("verify") is not True:
            problems.append("step %s: report marks verify=%r on a passing step"
                            % (index, step.get("verify")))

    if proof.get("verify") is True:
        if failure_step is not None:
            problems.append("report says verify=true but replay failed at step %s"
                            % failure_step)
        if proof.get("failed_step") is not None:
            problems.append("report says verify=true but failed_step is not null")
        if state != proof.get("result"):
            problems.append(
                "final text %r != reported result %r"
                % (state, proof.get("result"))
            )
    else:
        if failure_step != proof.get("failed_step"):
            problems.append(
                "replay failed at step %r, report says %r"
                % (failure_step, proof.get("failed_step"))
            )

    return problems


def main():
    data = json.load(sys.stdin)
    text = data["text"]
    payload = data["payload"]
    proofs = payload.get("proofs") or []

    if payload.get("status") == "no_candidate":
        if proofs:
            print("FAIL: no_candidate payload carries proofs")
            return 1
        print("PASS: no_candidate payload has no proofs")
        return 0

    if not proofs:
        print("FAIL: payload has no proofs")
        return 1

    failed = 0
    for proof in proofs:
        problems = replay_proof(text, proof)
        if problems:
            failed += 1
            print(
                "FAIL candidate %s (%s): %s"
                % (proof.get("rank"), proof.get("path_string"), "; ".join(problems))
            )
        else:
            print(
                "PASS candidate %s (%s)"
                % (proof.get("rank"), proof.get("path_string"))
            )

    print("summary: %d proof(s), %d failure(s)" % (len(proofs), failed))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
