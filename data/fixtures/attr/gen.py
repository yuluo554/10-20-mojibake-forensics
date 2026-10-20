#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""attr fixture generator (M1).

Fixed synthetic strings, fixed corruption chains, fixed expectations. The M2
``attr`` command must return a candidate *list*; even a single candidate stays in
the list and is never labelled "determined".
"""

from __future__ import print_function

import os
import sys

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.dirname(FIXTURE_DIR)
if FIXTURES_DIR not in sys.path:
    sys.path.insert(0, FIXTURES_DIR)

import genlib  # noqa: E402


CASES = (
    # id, truth, corruption encoder, corruption decoder, note
    ("classic-cp1252", "雅", "utf-8", "cp1252", "ftfy issue #166 shape"),
    ("utf8-as-latin1", "中文測試", "utf-8", "latin-1", "classic UTF-8 read as Latin-1"),
    ("utf8-as-cp437", "日本語", "utf-8", "cp437", "UTF-8 read as CP437 channel"),
)


def build():
    inputs = []
    expected_cases = []
    for case_id, truth, encoder, decoder in ((c[0], c[1], c[2], c[3]) for c in CASES):
        raw, corrupted = genlib.transform(truth, encoder, decoder)
        chain = "encode:%s>decode:%s" % (decoder, encoder)
        steps, result = genlib.chain_steps(corrupted, decoder, encoder)
        if result != truth:
            raise RuntimeError("%s: truth chain does not replay" % case_id)
        if not genlib.verify_steps(steps):
            raise RuntimeError("%s: steps do not verify" % case_id)
        inputs.append(
            {
                "id": case_id,
                "text": corrupted,
                "corrupted_bytes_hex": genlib.hexdump(raw),
            }
        )
        expected_cases.append(
            {
                "id": case_id,
                "status": "candidates",
                "chain": chain,
                "steps": steps,
                "truth": truth,
                "truth_in_candidates": True,
                "candidate_count_min": 1,
                "note": None,
            }
        )

    payload = {
        "input": {"cases": inputs},
        "expected": {
            "status": "candidates",
            "candidates_are_always_a_list": True,
            "top_1_note": "single_candidate_in_bounded_search",
            "cases": expected_cases,
        },
        "criteria": {
            "encoders": [
                "utf-8",
                "gb18030",
                "gbk",
                "big5",
                "shift_jis",
                "euc-jp",
                "euc-kr",
                "cp1252",
                "latin-1",
                "cp437",
            ],
            "decoders": [
                "utf-8",
                "gb18030",
                "big5",
                "shift_jis",
                "euc-kr",
                "cp1252",
                "latin-1",
            ],
            "max_depth": 3,
        },
        "note": "M2 consumes this fixture; expected values are recomputable with stdlib codecs",
    }
    return payload, {}


if __name__ == "__main__":
    sys.exit(
        genlib.run(
            build,
            FIXTURE_DIR,
            description="attr fixture generator (M1)",
        )
    )
