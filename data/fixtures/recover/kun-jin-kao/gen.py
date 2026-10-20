#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Irreversible fixture: 锟斤拷 from repeated U+FFFD bytes read as GBK."""

from __future__ import print_function

import os
import sys

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
RECOVER_DIR = os.path.dirname(FIXTURE_DIR)
if RECOVER_DIR not in sys.path:
    sys.path.insert(0, RECOVER_DIR)

import common  # noqa: E402


def build():
    replacement = "\ufffd"
    raw = (replacement * 2).encode("utf-8")
    text = raw.decode("gbk")
    if text != "锟斤拷":
        raise RuntimeError("unexpected kun-jin-kao construction: %r" % text)
    if text.encode("gbk") != raw:
        raise RuntimeError("kun-jin-kao bytes are not round-trip stable")

    input_block = {
        "text": text,
        "construction": {
            "kind": "bytes_decode",
            "bytes_hex": common.genlib.hexdump(raw),
            "codec": "gbk",
            "replacement_char": "U+FFFD",
            "repeat": 2,
        },
    }
    expected = {
        "status": "LOST",
        "reason": "kun_jin_kao",
        "recovered": None,
        "loss": {
            "step": "decode",
            "codec": "gbk",
            "offset": 0,
            "replaced_with": "U+FFFD",
            "bytes_hex": "EF BF BD",
            "repeat": 2,
        },
        "contains_tool_invented_chars": False,
        "note": "bytes were already destroyed; any 'repair' would invent characters",
    }
    return common.payload(input_block, expected, "M4 consumes this fixture; LOST must not guess"), {}


if __name__ == "__main__":
    sys.exit(
        common.run(
            build,
            FIXTURE_DIR,
            "recover/kun-jin-kao fixture generator (M1)",
        )
    )
