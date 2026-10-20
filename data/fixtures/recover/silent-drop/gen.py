#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Irreversible fixture: errors='ignore' silently dropped a character.

The observable result ("ab") is indistinguishable from clean text. The verdict
is therefore only assertable with provenance (or raw bytes); the string alone
carries no evidence. The tool must not claim otherwise.
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
    original = "a雅b"
    codec = "latin-1"
    raw = original.encode(codec, "ignore")
    text = raw.decode(codec)
    if text != "ab":
        raise RuntimeError("unexpected silent-drop construction: %r" % text)
    if "雅" in text:
        raise RuntimeError("silent drop did not remove the character")

    input_block = {
        "text": text,
        "construction": {
            "kind": "encode_errors_ignore",
            "original": original,
            "encode": codec,
            "decode": codec,
            "errors": "ignore",
            "bytes_hex": common.genlib.hexdump(raw),
        },
    }
    expected = {
        "status": "LOST",
        "reason": "silent_drop",
        "recovered": None,
        "loss": {
            "step": "encode",
            "codec": codec,
            "offset": 1,
            "dropped_char": "雅",
            "cause": "errors=ignore",
        },
        "contains_tool_invented_chars": False,
        "requires_provenance": True,
        "note": "the visible 'ab' is clean; only provenance or raw bytes reveal the drop",
    }
    return common.payload(input_block, expected, "M4 consumes this fixture; do not infer a drop from 'ab' alone"), {}


if __name__ == "__main__":
    sys.exit(
        common.run(
            build,
            FIXTURE_DIR,
            "recover/silent-drop fixture generator (M1)",
        )
    )
