#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""explain fixture generator (M1).

One positive chain (every step replays) and one negative chain (a codec name is
deliberately changed, so the mutated step fails). The negative must point at the
exact failed step, not at "something went wrong".
"""

from __future__ import print_function

import os
import sys

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.dirname(FIXTURE_DIR)
if FIXTURES_DIR not in sys.path:
    sys.path.insert(0, FIXTURES_DIR)

import genlib  # noqa: E402


def build():
    truth = "雅"
    corruption_encoder = "utf-8"
    corruption_decoder = "cp1252"
    positive_encoder = corruption_decoder
    positive_decoder = corruption_encoder

    raw, corrupted = genlib.transform(truth, corruption_encoder, corruption_decoder)
    positive_steps, positive_result = genlib.chain_steps(
        corrupted, positive_encoder, positive_decoder
    )
    if positive_result != truth:
        raise RuntimeError("positive chain does not recover the truth")
    if not genlib.verify_steps(positive_steps):
        raise RuntimeError("positive chain does not verify")

    # Negative: keep step 1, change step 2's codec from utf-8 to gb18030.
    negative_encoder = positive_encoder
    negative_decoder = "gb18030"
    negative_raw = corrupted.encode(negative_encoder)
    failed_step = None
    byte_offset = None
    try:
        negative_raw.decode(negative_decoder)
    except UnicodeDecodeError as exc:
        failed_step = 2
        byte_offset = exc.start

    if failed_step is None:
        raise RuntimeError("negative chain unexpectedly decoded; pick another mutation")

    payload = {
        "input": {
            "text": corrupted,
            "positive_chain": "encode:%s>decode:%s"
            % (positive_encoder, positive_decoder),
            "negative_chain": "encode:%s>decode:%s"
            % (negative_encoder, negative_decoder),
            "corrupted_bytes_hex": genlib.hexdump(raw),
        },
        "expected": {
            "positive": {
                "verify": True,
                "result": truth,
                "steps": positive_steps,
                "failed_step": None,
            },
            "negative": {
                "verify": False,
                "failed_step": failed_step,
                "byte_offset": byte_offset,
                "reason": "decode_error",
                "input_hex": genlib.hexdump(negative_raw),
            },
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
        "note": "M3 consumes this fixture; replay must not import tool internals",
    }
    return payload, {}


if __name__ == "__main__":
    sys.exit(
        genlib.run(
            build,
            FIXTURE_DIR,
            description="explain fixture generator (M1)",
        )
    )
