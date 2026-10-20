#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""file fixture: UTF-16LE text shifted by one byte (odd byte count)."""

from __future__ import print_function

import os
import sys

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.dirname(FIXTURE_DIR)
if FILE_DIR not in sys.path:
    sys.path.insert(0, FILE_DIR)

import common  # noqa: E402


def build():
    text = "中文测试"
    body = text.encode("utf-16-le")
    data = b"\x00" + body  # one extra leading byte -> odd length

    if len(data) % 2 != 1:
        raise RuntimeError("fixture is not odd-length")

    try:
        data.decode("utf-16-le")
        unshifted = {"decodable": True}
    except UnicodeDecodeError as exc:
        unshifted = {"decodable": False, "byte_offset": exc.start}

    shifted_text = data[1:].decode("utf-16-le")
    if shifted_text != text:
        raise RuntimeError("shift-by-one does not recover the text")

    input_block = {
        "path": "utf16-misalignment.bin",
        "sha256": common.genlib.sha256_hex(data),
        "bytes_hex": common.genlib.hexdump(data),
    }
    expected = {
        "status": "ok",
        "utf16_misalignment": {
            "byte_length": len(data),
            "odd_length": True,
            "unshifted": unshifted,
            "shift_offset": 1,
            "shifted_text": shifted_text,
            "reason": "odd_byte_count",
        },
        "mutates_input": False,
    }
    return common.payload(input_block, expected, "M5 consumes this fixture; evidence only, no auto-fix"), {
        "utf16-misalignment.bin": data,
    }


if __name__ == "__main__":
    sys.exit(
        common.run(
            build,
            FIXTURE_DIR,
            "file/utf16-misalignment fixture generator (M1)",
        )
    )
