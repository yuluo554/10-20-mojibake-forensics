#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Irreversible fixture: invalid bytes decoded with errors='replace'."""

from __future__ import print_function

import os
import sys

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
RECOVER_DIR = os.path.dirname(FIXTURE_DIR)
if RECOVER_DIR not in sys.path:
    sys.path.insert(0, RECOVER_DIR)

import common  # noqa: E402


def build():
    raw = b"abc\xffdef"
    codec = "utf-8"
    text = raw.decode(codec, "replace")
    if text != "abc\ufffddef":
        raise RuntimeError("unexpected replacement-char construction: %r" % text)
    offset = text.index("\ufffd")
    if offset != 3:
        raise RuntimeError("unexpected replacement-char offset: %r" % offset)

    input_block = {
        "text": text,
        "construction": {
            "kind": "decode_errors_replace",
            "bytes_hex": common.genlib.hexdump(raw),
            "decode": codec,
            "errors": "replace",
        },
    }
    expected = {
        "status": "LOST",
        "reason": "replacement_char",
        "recovered": None,
        "loss": {
            "step": "decode",
            "codec": codec,
            "offset": offset,
            "replaced_with": "U+FFFD",
            "bytes_hex": "FF",
        },
        "contains_tool_invented_chars": False,
        "note": "U+FFFD marks bytes that no longer exist; the original cannot be recovered",
    }
    return common.payload(input_block, expected, "M4 consumes this fixture; LOST must locate U+FFFD"), {}


if __name__ == "__main__":
    sys.exit(
        common.run(
            build,
            FIXTURE_DIR,
            "recover/replacement-char fixture generator (M1)",
        )
    )
