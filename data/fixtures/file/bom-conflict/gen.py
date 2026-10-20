#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""file fixture: a UTF-8 BOM followed by non-UTF-8 (GBK) bytes."""

from __future__ import print_function

import os
import sys

FIXTURE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_DIR = os.path.dirname(FIXTURE_DIR)
if FILE_DIR not in sys.path:
    sys.path.insert(0, FILE_DIR)

import common  # noqa: E402


def build():
    bom = b"\xef\xbb\xbf"
    body = "中文".encode("gbk")
    data = bom + body

    try:
        body.decode("utf-8")
        as_utf8 = {"decodable": True, "text": body.decode("utf-8")}
    except UnicodeDecodeError as exc:
        as_utf8 = {"decodable": False, "byte_offset": exc.start}

    try:
        as_gb18030 = {"decodable": True, "text": body.decode("gb18030")}
    except UnicodeDecodeError:
        as_gb18030 = {"decodable": False, "text": None}

    if as_utf8["decodable"] or not as_gb18030["decodable"]:
        raise RuntimeError("BOM conflict fixture is not actually conflicting")

    input_block = {
        "path": "bom-conflict.bin",
        "sha256": common.genlib.sha256_hex(data),
        "bytes_hex": common.genlib.hexdump(data),
    }
    expected = {
        "status": "ok",
        "bom": {"present": True, "kind": "utf-8", "bytes_hex": "EF BB BF", "offset": 0},
        "bom_conflict": True,
        "content": {"body_hex": common.genlib.hexdump(body), "as_utf8": as_utf8, "as_gb18030": as_gb18030},
        "mutates_input": False,
    }
    return common.payload(input_block, expected, "M5 consumes this fixture; report the conflict, never rewrite"), {
        "bom-conflict.bin": data,
    }


if __name__ == "__main__":
    sys.exit(
        common.run(
            build,
            FIXTURE_DIR,
            "file/bom-conflict fixture generator (M1)",
        )
    )
