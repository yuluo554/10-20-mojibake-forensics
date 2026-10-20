#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Irreversible fixture: MSVC 0xCC / 0xCD stack fill read as text.

This is not an encoding accident at all; it must be classified NOT_MOJIBAKE.
"""

from __future__ import print_function

import os
import sys

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
RECOVER_DIR = os.path.dirname(FIXTURE_DIR)
if RECOVER_DIR not in sys.path:
    sys.path.insert(0, RECOVER_DIR)

import common  # noqa: E402


def build():
    raw_cc = b"\xcc" * 6
    raw_cd = b"\xcd" * 6
    text_cc = raw_cc.decode("gbk")
    text_cd = raw_cd.decode("gbk")
    if text_cc != "烫烫烫" or text_cd != "屯屯屯":
        raise RuntimeError("unexpected fill-byte construction: %r / %r" % (text_cc, text_cd))

    input_block = {
        "text": text_cc,
        "alternative_text": text_cd,
        "construction": {
            "kind": "fill_byte_decode",
            "fill_bytes": ["CC", "CD"],
            "repeat": 6,
            "codec": "gbk",
            "bytes_hex": {
                "CC": common.genlib.hexdump(raw_cc),
                "CD": common.genlib.hexdump(raw_cd),
            },
        },
    }
    expected = {
        "status": "NOT_MOJIBAKE",
        "reason": "msvc_fill",
        "recovered": None,
        "loss": None,
        "not_mojibake": True,
        "contains_tool_invented_chars": False,
        "note": "MSVC Debug stack fill (0xCC/0xCD); do not try to repair it",
    }
    return common.payload(input_block, expected, "M4 consumes this fixture; classify, do not repair"), {}


if __name__ == "__main__":
    sys.exit(
        common.run(
            build,
            FIXTURE_DIR,
            "recover/tang-tang fixture generator (M1)",
        )
    )
