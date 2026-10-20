#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Irreversible fixture: an unencodable character became '?'.

The fixture deliberately uses ``errors='replace'`` in the *generator* to model
a third-party bug. The tool itself never uses a lossy handler on its decision
path; the fixture exists so the tool can decline to guess what the '?' was.
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
    raw = original.encode(codec, "replace")
    text = raw.decode(codec)
    if text != "a?b":
        raise RuntimeError("unexpected question-mark construction: %r" % text)
    offset = text.index("?")
    if offset != 1:
        raise RuntimeError("unexpected question-mark offset: %r" % offset)

    input_block = {
        "text": text,
        "construction": {
            "kind": "encode_errors_replace",
            "original": original,
            "encode": codec,
            "decode": codec,
            "errors": "replace",
            "bytes_hex": common.genlib.hexdump(raw),
        },
    }
    expected = {
        "status": "LOST",
        "reason": "encode_truncated",
        "recovered": None,
        "loss": {
            "step": "encode",
            "codec": codec,
            "offset": offset,
            "replaced_with": "?",
            "original_char": "雅",
            "cause": "errors=replace",
        },
        "contains_tool_invented_chars": False,
        "requires_provenance": True,
        "note": "'a?b' alone cannot reveal the lost character; do not invent it",
    }
    return common.payload(input_block, expected, "M4 consumes this fixture; LOST must locate the '?'"), {}


if __name__ == "__main__":
    sys.exit(
        common.run(
            build,
            FIXTURE_DIR,
            "recover/question-mark fixture generator (M1)",
        )
    )
